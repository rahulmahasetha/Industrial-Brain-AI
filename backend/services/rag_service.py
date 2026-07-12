import json
import os
import re
from typing import List, Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from sqlalchemy.orm import Session
import concurrent.futures
from langchain_core.documents import Document
from services.cache_service import cache_service

from services.page_index_service import (
    detect_intent,
    extract_equipment_ids,
    page_index_service,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

def extract_enterprise_ids(text: str) -> List[str]:
    """Extract standard enterprise identifiers like INC-001, ML-123, SOP-456."""
    pattern = r"\b(INC|ML|SOP|RCA|QA|AUDIT)-?\s*(\d{3,5})\b"
    matches = re.findall(pattern, text.upper())
    return sorted({f"{prefix}-{digits}" for prefix, digits in matches})



class RAGEngine:
    def __init__(self):
        self.init_error = None
        self.has_api_key = bool(os.environ.get("GOOGLE_API_KEY"))
        self.has_groq_key = bool(os.environ.get("GROQ_API_KEY"))
        
        self.llm = None
        self.embeddings = None
        self.primary_llm = None
        self.fallback_llm = None

        if self.has_api_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
                model_name = os.environ.get("GOOGLE_MODEL", "gemini-2.5-flash")
                embedding_model = os.environ.get("GOOGLE_EMBEDDING_MODEL", "gemini-embedding-001")
                self.llm = ChatGoogleGenerativeAI(model=model_name)
                self.fallback_llm = self.llm
                self.embeddings = GoogleGenerativeAIEmbeddings(model=embedding_model)
                print(f"RAG Engine initialized with Gemini LLM={model_name} EMBED={embedding_model}")
            except Exception as e:
                self.init_error = str(e)
                print(f"RAG Engine failed to initialize Gemini LLM: {e}")
                
        if self.has_groq_key:
            try:
                from langchain_groq import ChatGroq
                self.primary_llm = ChatGroq(
                    api_key=os.environ.get("GROQ_API_KEY"),
                    model="llama-3.1-8b-instant"
                )
                print("Groq LLM initialized as primary.")
            except Exception as e:
                print(f"Failed to init Groq: {e}")
            
        if not self.primary_llm and self.fallback_llm:
            self.primary_llm = self.fallback_llm
            print("Using Gemini as primary LLM (Groq unavailable).")

        if not self.has_api_key and not self.has_groq_key:
            print("RAG Engine initialized in Mock mode (no GOOGLE_API_KEY or GROQ_API_KEY found)")

    def _matches_graph_context(self, doc: Any, asset_tag: str = None, graph_terms: List[str] = None) -> bool:
        if asset_tag:
            asset_norm = asset_tag.upper().replace("-", "")
            metadata_equipment = str(doc.metadata.get("equipment", "")).upper().replace("-", "")
            if asset_norm and asset_norm in metadata_equipment:
                return True

        if not graph_terms:
            return True

        searchable = " ".join([
            str(doc.metadata.get("title", "")),
            str(doc.metadata.get("section_name", "")),
            getattr(doc, "page_content", "")
        ]).lower()
        return any(term.lower() in searchable for term in graph_terms)

    def _build_memory_context(self, history: List[Dict[str, Any]] = None) -> str:
        if not history:
            return ""
        recent = [turn for turn in history[-6:] if turn.get("role") and turn.get("content")]
        return "\n\n".join([f"{turn['role'].capitalize()}: {turn['content']}" for turn in recent])


    def _build_prompt(self, retrieval_plan: Dict[str, Any] = None) -> PromptTemplate:
        template_fields = []
        intent = retrieval_plan.get("intent", "") if retrieval_plan else ""
        if retrieval_plan and "response_template" in retrieval_plan:
            template_fields = retrieval_plan["response_template"]
        
        json_fields = [
            '"answer": "Your detailed response here. Use a Markdown table with full details if listing multiple items, otherwise a 3-4 sentence explanation",',
            '"confidence": 95,',
            '"citations": [{{"document_name": "...", "page_number": 1, "section_title": "..."}}],',
            '"safety_flag": false,',
            '"follow_up_suggestions": ["...", "..."],',
            '"data": {{'
        ]
        
        if template_fields:
            for field in template_fields:
                key = field.lower().replace(" ", "_")
                json_fields.append(f'    "{key}": "...",')  
        else:
            json_fields.append('    "details": "..."')
            
        json_fields.append('  }}')
        json_schema = "\n".join(json_fields)
        
        intent_rules = ""
        if intent == "RCA":
            intent_rules = (
                "\nROOT CAUSE ANALYSIS RULES:\n"
                "- The root cause MUST be a physical or process failure mechanism.\n"
                "- Merge evidence chronologically based on document dates.\n"
                "- Prioritize evidence from: Incident Reports, RCA Reports, Failure Logs.\n"
            )
        elif intent in ["manual_lookup", "startup_procedure", "shutdown_procedure", "sop"]:
            intent_rules = (
                "\nMANUAL CONTENT FIDELITY RULES:\n"
                "- PRESERVE EXACTLY: Section numbers, Section titles, Numbered steps, Bullet points, Tables, OEM terminology, and WARNING / CAUTION / DANGER / NOTE blocks.\n"
                "- PRESERVE EXACTLY: All technical parameters, units, pressures, temperatures, and concentrations.\n"
                "- Do not rewrite, paraphrase, or summarize procedures unless explicitly requested by the user.\n"
                "- If multiple sections are requested, return them in the original manual order.\n"
                "- NEVER substitute information from Maintenance Logs, Incident Reports, Inspection Reports, QA Records, RCA Reports, Knowledge Graph, or LLM internal knowledge when answering from the manual.\n"
                "- If the context states that a section exists but pages are not indexed, explicitly state: 'The requested section exists in the manual, but its content pages are not indexed.'\n"
                "- Every answer MUST include the original section headings, lists/tables, source document name, and page number(s).\n"
                "- Before generating the response, validate that the retrieved context actually contains the requested section. If not, do not hallucinate; return only the indexed content or clearly state the content is unavailable.\n"
            )
        ambiguous_rules = (
            "\nAMBIGUOUS QUERY RULES:\n"
            "- Do not immediately ask the user for clarification if the query is a common industrial term such as 'procedure', 'manual', 'SOP', 'maintenance', 'inspection', 'startup', 'shutdown', 'troubleshooting', 'RCA', or 'incident'.\n"
            "- First search the indexed documents and infer the most likely intent using the provided context.\n"
            "- If multiple matching procedures/documents exist in the context, return a concise list (Document Name, Equipment ID, Procedure Type, Page/Section) and ask the user to choose one.\n"
            "- If exactly one relevant procedure is found, return it directly without asking for clarification.\n"
            "- Only ask a clarification question when NO relevant documents are found or multiple equally relevant results cannot be distinguished.\n"
        )
        
        list_rules = ""
        intent_lower = (retrieval_plan or {}).get("intent", "").lower()
        if any(w in intent_lower for w in ["incident", "maintenance", "inspection"]):
            list_rules = (
                "\nLIST QUERY RULES:\n"
                "- If the user asks to 'show', 'list', or 'find all' matching records, return ALL matching items.\n"
            )
            
        reasoning_rules = ""
        if intent_lower in ["reasoning_analysis", "root_cause_analysis", "compliance", "predictive_maintenance"]:
            reasoning_rules = (
                "\nREASONING & ANALYSIS RULES:\n"
                "- NEVER generate explanations from general knowledge; always explain answers with evidence from retrieved documents.\n"
                "- Correlate information across all retrieved document types (Manuals, SOPs, RCA, Incident Reports, etc.).\n"
                "- Explain root cause, impact, contributing factors, and corrective/preventive actions when available.\n"
                "- If evidence is insufficient, clearly state that the information is unavailable instead of guessing.\n"
                "- Preserve all technical values, tables, units, warnings, and specifications exactly as written in the source documents.\n"
                "- You MUST display an 'Evidence Summary' section at the end detailing Document ID, Page Number, Section, and confidence score for your claims.\n"
            )
        else:
            reasoning_rules = (
                "\nCITATION RULES:\n"
                "- For this retrieval request, display ONLY compact source citations inline (e.g., [Document ID, Page X, Section Y, Confidence Z]) instead of a full Evidence Summary.\n"
                "- Never hallucinate technical facts or operating limits.\n"
                "- If evidence is insufficient, clearly state that the information is unavailable instead of guessing.\n"
                "- Preserve all technical values, tables, units, warnings, and specifications exactly as written.\n"
            )
        
        prompt_text = (
            "You are Industrial Brain AI, an expert assistant for FreshFlow Beverages plant operations.\n\n"
            "Answer the operator's question using ONLY the context provided below. If one or more specific sections were requested, restrict your answer strictly to the information within those sections.\n"
            "ASSET CONTEXT: {asset_tag}\n"
            "OPERATOR ROLE: {user_role}\n\n"
            "RULES:\n"
            "1. Provide a highly detailed and comprehensive response by default. Extract and present as much useful information as possible from the context. Do not artificially limit your word count.\n"
            "2. NEVER expose raw JSON, internal schema, backend keys (answer, data, confidence, citations, follow_up_suggestions) to the user.\n"
            "3. Format your response dynamically to best answer the user's question.\n"
            "4. Include all relevant timelines, evidence, RCA, and context from the provided documents.\n"
            "5. Always cite your sources using [Document Name (Page X)] format.\n\n"
            "FORMAT GUIDELINES:\n"
            "- CRITICAL: If there are multiple incidents, details, items, or events, you MUST format the response as a standard Markdown table.\n"
            "- Do not use a rigid template otherwise. Adapt the structure to the specific question.\n"
            "- Only provide recommendations if action is necessary (e.g., for time-sensitive, critical, or specific case-sensitive issues).\n"
            "- If the query is just informational, do not force a recommendations section.\n\n"
            + intent_rules
            + list_rules
            + reasoning_rules
            + ambiguous_rules +
            "\nRespond in this exact JSON format. Put your formatted markdown inside the 'answer' field:\n"
            "{{\n"
            + json_schema +
            "\n}}\n"
            "\n\nSearch Log:\n{search_log}\n\n"
            "Context: {context_chunks}\n"
            "Question: {question}"
        )
        return PromptTemplate.from_template(prompt_text)

    def _build_direct_answer_prompt(self, retrieval_plan: Dict[str, Any] = None) -> PromptTemplate:
        """Lightweight prompt for concise/direct answers."""
        intent = retrieval_plan.get("intent", "") if retrieval_plan else ""
        intent_rules = ""
        if intent in ["manual_lookup", "startup_procedure", "shutdown_procedure", "sop"]:
            intent_rules = (
                "\nMANUAL CONTENT FIDELITY RULES:\n"
                "- PRESERVE EXACTLY: Section numbers, Section titles, Numbered steps, Bullet points, Tables, OEM terminology, and WARNING / CAUTION / DANGER / NOTE blocks.\n"
                "- PRESERVE EXACTLY: All technical parameters, units, pressures, temperatures, and concentrations.\n"
                "- Do not rewrite, paraphrase, or summarize procedures unless explicitly requested by the user.\n"
                "- If multiple sections are requested, return them in the original manual order.\n"
                "- NEVER substitute information from Maintenance Logs, Incident Reports, Inspection Reports, QA Records, RCA Reports, Knowledge Graph, or LLM internal knowledge when answering from the manual.\n"
                "- If the context states that a section exists but pages are not indexed, explicitly state: 'The requested section exists in the manual, but its content pages are not indexed.'\n"
                "- Every answer MUST include the original section headings, lists/tables, source document name, and page number(s).\n"
                "- Before generating the response, validate that the retrieved context actually contains the requested section. If not, do not hallucinate; return only the indexed content or clearly state the content is unavailable.\n"
            )
        ambiguous_rules = (
            "\nAMBIGUOUS QUERY RULES:\n"
            "- Do not immediately ask the user for clarification if the query is a common industrial term such as 'procedure', 'manual', 'SOP', 'maintenance', 'inspection', 'startup', 'shutdown', 'troubleshooting', 'RCA', or 'incident'.\n"
            "- First search the indexed documents and infer the most likely intent using the provided context.\n"
            "- If multiple matching procedures/documents exist in the context, return a concise list (Document Name, Equipment ID, Procedure Type, Page/Section) and ask the user to choose one.\n"
            "- If exactly one relevant procedure is found, return it directly without asking for clarification.\n"
            "- Only ask a clarification question when NO relevant documents are found or multiple equally relevant results cannot be distinguished.\n"
        )
            
        reasoning_rules = ""
        if intent in ["reasoning_analysis", "root_cause_analysis", "compliance", "predictive_maintenance"]:
            reasoning_rules = (
                "\nREASONING & ANALYSIS RULES:\n"
                "- NEVER generate explanations from general knowledge; always explain answers with evidence from retrieved documents.\n"
                "- Correlate information across all retrieved document types (Manuals, SOPs, RCA, Incident Reports, etc.).\n"
                "- Explain root cause, impact, contributing factors, and corrective/preventive actions when available.\n"
                "- If evidence is insufficient, clearly state that the information is unavailable instead of guessing.\n"
                "- Preserve all technical values, tables, units, warnings, and specifications exactly as written in the source documents.\n"
                "- You MUST display an 'Evidence Summary' section at the end detailing Document ID, Page Number, Section, and confidence score for your claims.\n"
            )
        else:
            reasoning_rules = (
                "\nCITATION RULES:\n"
                "- For this retrieval request, display ONLY compact source citations inline (e.g., [Document ID, Page X, Section Y, Confidence Z]) instead of a full Evidence Summary.\n"
                "- Never hallucinate technical facts or operating limits.\n"
                "- If evidence is insufficient, clearly state that the information is unavailable instead of guessing.\n"
                "- Preserve all technical values, tables, units, warnings, and specifications exactly as written.\n"
            )
            
        prompt_text = (
            "You are Industrial Brain AI, an expert assistant for FreshFlow Beverages plant operations.\n\n"
            "Answer the operator's question using ONLY the context provided below.\n"
            "RULES:\n"
            "1. Provide a highly detailed and comprehensive response by default. Extract and present as much useful information as possible from the context. Do not artificially limit your word count.\n"
            "2. NEVER expose raw JSON, internal schema, backend keys (answer, data, confidence, citations, follow_up_suggestions) to the user.\n"
            "3. Format your response dynamically to best answer the user's question.\n"
            "4. Include all relevant timelines, evidence, RCA, and context from the provided documents.\n"
            "5. Always cite your sources using [Document Name (Page X)] format.\n\n"
            "FORMAT GUIDELINES:\n"
            "- CRITICAL: If there are multiple incidents, details, items, or events, you MUST format the response as a standard Markdown table.\n"
            "- Do not use a rigid template otherwise. Adapt the structure to the specific question.\n"
            "- Only provide recommendations if action is necessary (e.g., for time-sensitive, critical, or specific case-sensitive issues).\n"
            "- If the query is just informational, do not force a recommendations section.\n\n"
            + intent_rules
            + reasoning_rules
            + ambiguous_rules +
            "\nSearch Log:\n{search_log}\n\n"
            "Context: {context_chunks}\n"
            "Question: {question}"
        )
        return PromptTemplate.from_template(prompt_text)
    def _rerank_pages(self, query_text: str, pages: List[Any], candidate_page_ids: List[int], retrieval_plan: Dict[str, Any] = None, db: Session = None) -> List[Any]:
        ranked = []
        query_terms = [term.lower() for term in re.findall(r"\b[A-Za-z0-9_-]{3,}\b", query_text)]
        
        # Cache document types to avoid N+1 queries if db is available
        doc_types = {}
        if db:
            from models.domain import Document
            doc_ids = list({p.document_id for p in pages})
            docs = db.query(Document).filter(Document.id.in_(doc_ids)).all()
            for d in docs:
                doc_types[d.id] = d.type
                
        weights = retrieval_plan.get("doc_priority_weights", {}) if retrieval_plan else {}
        
        for page in pages:
            score = 0
            if page.id in candidate_page_ids:
                score += 15
            
            # Apply document priority weight
            doc_type = doc_types.get(page.document_id)
            if doc_type and doc_type in weights:
                # Add a substantial boost based on weight (e.g. 1.0 -> 20, 0.6 -> 12)
                score += (weights[doc_type] * 20)
                
            haystack = " ".join([
                page.document_name or "",
                page.section_title or "",
                page.keywords or "",
                page.summary or "",
                page.extracted_text or "",
            ]).lower()
            score += sum(2 for term in query_terms if term in haystack)
            score += 5 if page.section_title and any(term in page.section_title.lower() for term in query_terms) else 0
            score += 3 if page.document_name and query_text.lower() in page.document_name.lower() else 0
            ranked.append((score, page))
        ranked.sort(key=lambda item: (-item[0], item[1].document_name or "", item[1].page_number))
        return [page for _, page in ranked]

    def route_query(self, query_text: str) -> Dict[str, str]:
        """Rule-based query router. No LLM call — saves API quota for answer generation."""
        lower = query_text.lower()
        
        # Full card triggers: diagnostic, RCA, incident reports, list/show queries, inspections
        full_card_words = [
            "why", "cause", "caused", "because", "root cause",
            "failure", "failed", "troubleshoot", "troubleshooting",
            "pattern", "should", "need", "recommend",
            "incident", "breakdown", "rca",
            "show", "list", "all", "find",
            "inspect", "audit", "compliance",
            "predict", "predictive", "health", "risk",
            "maintenance", "history", "service",
            "sop", "startup", "shutdown", "procedure",
            "manual", "guide",
        ]
        if any(word in lower for word in full_card_words):
            return {"mode": "full_card", "reasoning": "structured response required"}
        return {"mode": "concise", "reasoning": "simple factual or status inquiry"}

    def query(
        self,
        query_text: str,
        context_docs: List[str] = None,
        asset_tag: str = None,
        graph_context: str = None,
        db: Session = None,
        synthesize: bool = True,
        retrieval_plan: Dict[str, Any] = None,
        history: List[Dict[str, Any]] = None,
        direct_answer: bool = False,
    ) -> Dict[str, Any]:
        """Execute Page Index + GraphRAG retrieval.

        Flow: intent detection -> equipment extraction -> graph expansion ->
        page-index filter -> pooled hybrid ranking -> reranking -> Groq over exact pages.
        """
        print(f"RAG Engine processing query: {query_text} (Target Asset: {asset_tag})")

        import time
        t_start = time.time()

        t0 = time.time()
        intent = detect_intent(query_text)
        intent_time = time.time() - t0

        metrics = {
            "query": query_text,
            "intent": intent,
            "intent_time": intent_time,
            "kg_time": 0.0,
            "toc_time": 0.0,
            "sql_time": 0.0,
            "vector_time": 0.0,
            "rerank_time": 0.0,
            "metadata_time": 0.0,
            "llm_time": 0.0,
            "total_time": 0.0,
            "metadata_matches": 0,
            "sql_matches": 0,
            "vector_matches": 0,
            "toc_matches": 0,
            "kg_matches": 0,
            "final_docs": 0,
            "confidence_score": 0.0,
            "timestamp": time.time()
        }

        def record_metrics(res):
            metrics["total_time"] = time.time() - t_start
            metrics["final_docs"] = len(res.get("sources") or [])
            metrics["confidence_score"] = float(res.get("confidence") or 0.0)
            if "llm_start_time" in metrics:
                metrics["llm_time"] = time.time() - metrics["llm_start_time"]
            cache_service.record_query_metrics(metrics)
            return res

        asset_tag = asset_tag or (extract_equipment_ids(query_text)[0] if extract_equipment_ids(query_text) else None)
        graph_terms = [term.strip() for term in re.split(r"[,;|]+", graph_context or "")]
        def fetch_kg():
            from database import SessionLocal
            local_db = SessionLocal()
            t_kg_start = time.time()
            try:
                res = page_index_service.get_graph_connected_entities(local_db, asset_tag)
                metrics["kg_time"] = time.time() - t_kg_start
                metrics["kg_matches"] = len(res)
                return res
            finally:
                local_db.close()
        if db:
            graph_terms.extend(fetch_kg())

        pages = []
        semantic_docs = []
        context = ""
        sources = []
        citations = []
        supporting_evidence = []
        memory_context = self._build_memory_context(history)
        
        # Inject external db_context if provided
        if context_docs:
            for c_doc in context_docs:
                if c_doc:
                    context += f"{c_doc}\n\n"

        if self.has_api_key and self.init_error:
            raise RuntimeError(f"AI initialization error: {self.init_error}")

        search_log = []
        pages = []
        
        preferred_doc_types = retrieval_plan.get("allowed_doc_types") if retrieval_plan else None
        
        def fetch_toc():
            t_toc_start = time.time()
            from database import SessionLocal
            local_db = SessionLocal()
            try:
                from services.toc_service import detect_requested_sections, get_sections_pages
                requested_sections = detect_requested_sections(query_text)
                if requested_sections and asset_tag:
                    toc_pages = get_sections_pages(local_db, asset_tag, requested_sections)
                    if toc_pages:
                        local_db.expunge_all()
                        metrics["toc_time"] = time.time() - t_toc_start
                        metrics["toc_matches"] = len(toc_pages)
                        return toc_pages, requested_sections
                metrics["toc_time"] = time.time() - t_toc_start
                return [], []
            finally:
                local_db.close()

        def fetch_sql():
            t_sql_start = time.time()
            from database import SessionLocal
            local_db = SessionLocal()
            local_log = []
            local_debug = []
            local_pages = []
            try:
                page_index_service.sync_legacy_document_pages(local_db)
                page_index_service.sync_structured_record_pages(local_db)
                
                # EXACT METADATA BYPASS
                exact_ids = extract_enterprise_ids(query_text)
                if exact_ids:
                    from models.domain import PageIndex
                    for ex_id in exact_ids:
                        q = local_db.query(PageIndex).filter(
                            (PageIndex.log_id == ex_id) |
                            (PageIndex.incident_id == ex_id) |
                            (PageIndex.inspection_id == ex_id) |
                            (PageIndex.sop_id == ex_id) |
                            (PageIndex.document_name.ilike(f"%{ex_id}%")) |
                            (PageIndex.section_title.ilike(f"%{ex_id}%"))
                        )
                        local_pages.extend(q.all())
                    if local_pages:
                        local_log.append(f"- Tier 1 Exact Metadata Lookup: Retrieved {len(local_pages)} pages for IDs {exact_ids}")
                        local_debug.append({"step": "Tier 1 Exact Metadata Lookup", "found": len(local_pages)})
                        metrics["metadata_matches"] = len(local_pages)
                        metrics["sql_matches"] = len(local_pages)
                        metrics["metadata_time"] = time.time() - t_sql_start
                        metrics["sql_time"] = time.time() - t_sql_start
                        local_db.expunge_all()
                        return list({p.id: p for p in local_pages if p.id}.values()), local_log, local_debug
                
                if retrieval_plan and retrieval_plan.get("retrieval_strategy") == "STRUCTURED_SQL" and retrieval_plan.get("structured_filters"):
                    from models.domain import PageIndex
                    filters = retrieval_plan.get("structured_filters", {})
                    q = local_db.query(PageIndex)
                    for key, val in filters.items():
                        if val:
                            q = q.filter(PageIndex.extracted_text.ilike(f"%{val}%"))
                    if asset_tag:
                        q = q.filter(PageIndex.equipment_ids.ilike(f"%{asset_tag}%"))
                    local_pages = q.limit(20).all()
                    if local_pages:
                        local_log.append(f"- Tier 3 Structured SQL Lookup: Retrieved {len(local_pages)} pages")
                        local_debug.append({"step": "Tier 3 Structured SQL Lookup", "found": len(local_pages)})
                        metrics["sql_matches"] = len(local_pages)
                        metrics["sql_time"] = time.time() - t_sql_start
                        local_db.expunge_all()
                        return local_pages, local_log, local_debug

                local_pages, _ = page_index_service.search_pages(local_db, query=query_text, equipment=asset_tag, graph_terms=graph_terms, allowed_doc_types=preferred_doc_types, limit=20)
                if local_pages:
                    local_log.append(f"- Primary SQL Search ({preferred_doc_types or 'All'}): {len(local_pages)} exact pages found")
                    local_debug.append({"step": "Primary SQL Search", "types": preferred_doc_types, "found": len(local_pages)})
                else:
                    # Never fall back to unconstrained search if disallowed_doc_types exists
                    if retrieval_plan and retrieval_plan.get("disallowed_doc_types"):
                        allowed = retrieval_plan.get("allowed_doc_types", []) + retrieval_plan.get("fallback_doc_types", [])
                        local_pages, _ = page_index_service.search_pages(local_db, query=query_text, equipment=asset_tag, graph_terms=graph_terms, allowed_doc_types=allowed, limit=20)
                        local_log.append(f"- Fallback SQL Search (Strict Types): {len(local_pages)} pages found")
                        local_debug.append({"step": "Fallback SQL Search", "types": allowed, "found": len(local_pages)})
                    else:
                        local_pages, _ = page_index_service.search_pages(local_db, query=query_text, equipment=asset_tag, graph_terms=graph_terms, allowed_doc_types=None, limit=20)
                        local_log.append(f"- Unconstrained SQL Search (All Documents): {len(local_pages)} pages found")
                        local_debug.append({"step": "Unconstrained SQL Search", "types": "All", "found": len(local_pages)})
                
                metrics["sql_matches"] = len(local_pages)
                metrics["sql_time"] = time.time() - t_sql_start
                local_db.expunge_all()
                return local_pages, local_log, local_debug
            finally:
                local_db.close()

        def run_chroma_search(search_q, allowed_types):
            t_chroma_start = time.time()
            local_fb_docs = []
            local_log = []
            local_debug = []
            
            cache_key = f"chroma:{search_q}:{'-'.join(allowed_types or [])}"
            cached_res = cache_service.get(cache_key)
            if cached_res:
                local_log.append(f"- Chroma Cache Hit for: {search_q}")
                local_debug.append({"step": "Semantic Vector Search (Cached)", "types": allowed_types, "found": len(cached_res)})
                local_fb_docs = [Document(page_content=d["page_content"], metadata=d["metadata"]) for d in cached_res]
                metrics["vector_matches"] = len(local_fb_docs)
                metrics["vector_time"] = time.time() - t_chroma_start
                return local_fb_docs, local_log, local_debug
                
            if self.has_api_key:
                try:
                    from services.ingestion import get_chroma_vectorstore
                    vectorstore = get_chroma_vectorstore()
                    filter_dict = None
                    if allowed_types:
                        filter_dict = {"type": allowed_types[0]} if len(allowed_types) == 1 else {"type": {"$in": allowed_types}}
                    
                    retriever = vectorstore.as_retriever(search_kwargs={"k": 8, "filter": filter_dict})
                    local_fb_docs = retriever.invoke(search_q)
                    local_debug.append({"step": "Semantic Vector Search", "types": allowed_types, "found": len(local_fb_docs)})
                    
                    if not local_fb_docs:
                        retriever = vectorstore.as_retriever(search_kwargs={"k": 8})
                        local_fb_docs = retriever.invoke(search_q)
                        local_log.append(f"- Unconstrained Vector Fallback: {len(local_fb_docs)} semantic matches found.")
                        local_debug.append({"step": "Unconstrained Semantic Search", "types": "All", "found": len(local_fb_docs)})
                except Exception as e:
                    print(f"[RAG] ChromaDB retrieval error: {e}")
                    
            if local_fb_docs:
                serializable_docs = [{"page_content": d.page_content, "metadata": d.metadata} for d in local_fb_docs]
                cache_service.set(cache_key, serializable_docs, ttl=3600)
                
            metrics["vector_matches"] = len(local_fb_docs)
            metrics["vector_time"] = time.time() - t_chroma_start
            return local_fb_docs, local_log, local_debug

        search_query = " ".join([part for part in [asset_tag, query_text, " ".join(graph_terms)] if part])
        allowed_types_for_chroma = retrieval_plan.get("allowed_doc_types") if retrieval_plan else None
        
        debug_info = {
            "search_steps": [],
            "final_filters_applied": None,
            "retrieved_documents": [],
            "scores": {}
        }
        
        fallback_docs = []
        is_toc_retrieval = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            kg_future = executor.submit(fetch_kg)
            toc_future = executor.submit(fetch_toc)
            sql_future = executor.submit(fetch_sql)
            chroma_future = executor.submit(run_chroma_search, search_query, allowed_types_for_chroma)
            
            graph_terms_res = kg_future.result()
            if graph_terms_res:
                graph_terms.extend(graph_terms_res)

            toc_pages, requested_sections = toc_future.result()
            
            sql_pages, sql_logs, sql_debug = sql_future.result()
            fallback_docs, chroma_logs, chroma_debug = chroma_future.result()
            
            if toc_pages:
                pages = toc_pages
                is_toc_retrieval = True
                search_log.append(f"- TOC-Aware Search: Retrieved {len(toc_pages)} exact pages for sections '{', '.join(requested_sections)}'")
                debug_info["search_steps"].append({"step": "TOC Retrieval", "found": len(toc_pages)})
            else:
                pages = sql_pages
                search_log.extend(sql_logs)
                debug_info["search_steps"].extend(sql_debug)
            
        semantic_page_ids = []
        if self.has_api_key and fallback_docs and not is_toc_retrieval:
            if pages:
                # We have SQL pages, let's rerank based on Chroma overlap
                allowed_page_ids = {p.id for p in pages}
                semantic_docs = [
                    doc for doc in fallback_docs
                    if (doc.metadata or {}).get("page_index_id")
                    and int((doc.metadata or {}).get("page_index_id")) in allowed_page_ids
                ]
                semantic_page_ids = [int(doc.metadata.get("page_index_id")) for doc in semantic_docs if doc.metadata and doc.metadata.get("page_index_id")]
                if semantic_page_ids:
                    t_rerank_start = time.time()
                    pages = self._rerank_pages(query_text, pages, semantic_page_ids, retrieval_plan, db)
                    metrics["rerank_time"] = time.time() - t_rerank_start
            else:
                search_log.extend(chroma_logs)
                debug_info["search_steps"].extend(chroma_debug)
                search_log.append(f"- Pure Vector Fallback triggered because no exact keywords matched.")
                fb_page_ids = list(set([int(doc.metadata.get("page_index_id")) for doc in fallback_docs if doc.metadata and doc.metadata.get("page_index_id")]))
                if fb_page_ids and db:
                    pages = db.query(page_index_service.PageIndex).filter(page_index_service.PageIndex.id.in_(fb_page_ids)).all()
                    search_log.append(f"- Vector Fallback successfully retrieved {len(pages)} pages from SQL.")

        context_parts = []
        seen_chunks = set()
        
        # Limit chunks globally to 15 to retrieve multiple events and documents.
        intent_name = (retrieval_plan or {}).get("intent", intent)
        MAX_CHUNKS = 15
        added_count = 0
        
        # STRICT SOURCE VALIDATION
        disallowed = retrieval_plan.get("disallowed_doc_types", []) if retrieval_plan else []
        allowed_docs_only = []
        for page in pages:
            # Re-fetch doc type from DB to be completely safe, or use cache.
            # In memory we can loosely guess by document name or status if needed, 
            # but since we already queried via search_pages we trust it mostly.
            # We will just do a string check on document_name to be doubly sure for disallowed.
            doc_name_lower = (page.document_name or "").lower()
            if any(d_type.lower() in doc_name_lower for d_type in disallowed):
                search_log.append(f"- Strict Validation: Discarded {page.document_name} due to disallowed type.")
                continue
            allowed_docs_only.append(page)
        
        pages = allowed_docs_only
        
        for page in pages:
            if added_count >= MAX_CHUNKS:
                break
                
            chunk_hash = hash(page.extracted_text or page.summary or "")
            if chunk_hash in seen_chunks:
                continue
            seen_chunks.add(chunk_hash)
            added_count += 1
            
            context_parts.append(
                f"Document Name: {page.document_name}\n"
                f"Page Number: {page.page_number}\n"
                f"Section Title: {page.section_title or 'N/A'}\n"
                f"Page Summary: {page.summary}\n"
                f"Extracted Text:\n{(page.extracted_text or '')[:1800]}"
            )
            source = f"{page.document_name} p.{page.page_number} - {page.section_title or 'N/A'}"
            sources.append(source)
            citations.append({
                "document_name": page.document_name,
                "page_number": page.page_number,
                "section_title": page.section_title or "N/A",
                "page_index_id": page.id,
            })
            supporting_evidence.append({
                "document_name": page.document_name,
                "page_number": page.page_number,
                "section_title": page.section_title or "N/A",
                "evidence": page.summary or (page.extracted_text or "")[:260],
            })
            debug_info["retrieved_documents"].append(page.document_name)
        
        context_str = "\n\n---\n\n".join(context_parts)
        if context:
            context_str = context + "\n\n---\n\n" + context_str
        sources = list(dict.fromkeys(sources))
        debug_info["retrieved_documents"] = list(dict.fromkeys(debug_info["retrieved_documents"]))

        if synthesize and self.primary_llm:
            metrics["llm_start_time"] = time.time()
            search_log_str = "\n".join(search_log)
            primary_llm = self.primary_llm
            fallback_llm = self.fallback_llm
            
            if direct_answer:
                prompt = self._build_direct_answer_prompt(retrieval_plan=retrieval_plan)
                try:
                    chain = prompt | primary_llm | StrOutputParser()
                    answer = chain.invoke({
                        "context_chunks": context_str[:7000],
                        "question": query_text,
                        "search_log": search_log_str,
                    })
                except Exception as e:
                    print(f"[RAG] Primary LLM error (concise): {e}")
                    if fallback_llm:
                        print("[RAG] Falling back to secondary LLM (Gemini)...")
                        try:
                            chain = prompt | fallback_llm | StrOutputParser()
                            answer = chain.invoke({
                                "context_chunks": context_str[:7000],
                                "question": query_text,
                                "search_log": search_log_str,
                            })
                        except Exception as e_inner:
                            print(f"[RAG] LLM error (concise fallback): {e_inner}")
                            answer = "I am experiencing high traffic right now and couldn't generate a response. Please try again in a moment."
                    else:
                        print(f"[RAG] LLM error (concise): {e}")
                        answer = "I am experiencing high traffic right now and couldn't generate a response. Please try again in a moment."
                        
                return record_metrics({
                    "answer": answer,
                    "sources": sources,
                    "confidence": 92 if semantic_docs else 84,
                    "intent": intent,
                    "equipment": asset_tag,
                    "citations": citations,
                    "supporting_evidence": supporting_evidence,
                    "mode": "concise",
                    "debug_info": debug_info,
                })
            else:
                prompt = self._build_prompt(retrieval_plan)
                try:
                    chain = prompt | primary_llm.bind(response_format={"type": "json_object"}) | StrOutputParser()
                    raw_answer = chain.invoke({
                        "context_chunks": context_str[:7000] if context_str else "No documents matched your query.",
                        "question": query_text,
                        "search_log": search_log_str,
                        "asset_tag": asset_tag or "Unknown",
                        "user_role": "Operator"
                    })
                except Exception as e:
                    print(f"[RAG] Primary LLM error (full_card): {e}")
                    if fallback_llm:
                        print("[RAG] Falling back to secondary LLM (Gemini)...")
                        chain = prompt | fallback_llm.bind(response_format={"type": "json_object"}) | StrOutputParser()
                        raw_answer = chain.invoke({
                            "context_chunks": context_str[:7000] if context_str else "No documents matched your query.",
                            "question": query_text,
                            "search_log": search_log_str,
                            "asset_tag": asset_tag or "Unknown",
                            "user_role": "Operator"
                        })
                    else:
                        raise e
                        
                try:
                    match = re.search(r'\{.*\}', raw_answer, re.DOTALL)
                    json_str = match.group() if match else raw_answer
                    
                    # Fix common unescaped newlines in JSON strings by replacing literal newlines with \n
                    # Only do this if standard parsing fails
                    try:
                        parsed_json = json.loads(json_str)
                    except json.JSONDecodeError:
                        # naive attempt to escape newlines inside the JSON string
                        # just escape all newlines since the JSON schema doesn't strictly need them
                        json_str_fixed = json_str.replace('\n', '\\n')
                        parsed_json = json.loads(json_str_fixed)
                        
                    return record_metrics({
                        "mode": "full_card",
                        "intent": intent,
                        "equipment": asset_tag,
                        "parsed_json": parsed_json,
                        "answer": parsed_json.get("answer", ""),
                        "confidence": parsed_json.get("confidence", 92 if semantic_docs else 84),
                        "citations": parsed_json.get("citations", citations),
                        "sources": sources,
                        "safety_flag": parsed_json.get("safety_flag", False),
                        "follow_up_suggestions": parsed_json.get("follow_up_suggestions", []),
                        "debug_info": debug_info,
                    })
                except json.JSONDecodeError:
                    print(f"[RAG] Failed to parse JSON from LLM: {raw_answer}")
                    cleaned = raw_answer
                    # Remove markdown JSON wrappers if any
                    cleaned = re.sub(r'^```json\s*', '', cleaned, flags=re.IGNORECASE)
                    cleaned = re.sub(r'```\s*$', '', cleaned)
                    # Clean up by stripping the { "answer": prefix, including optional YAML pipes
                    cleaned = re.sub(r'^\s*\{\s*"answer"\s*:\s*[|"]?\s*', '', cleaned)
                    # Strip trailing metadata
                    cleaned = re.sub(r'"?\s*,?\s*"confidence".*$', '', cleaned, flags=re.DOTALL)
                    cleaned = re.sub(r'"?\s*\}\s*$', '', cleaned)
                    return record_metrics({
                        "mode": "concise",
                        "answer": cleaned,
                        "intent": intent,
                        "sources": sources,
                        "confidence": 50,
                        "debug_info": debug_info,
                    })
                except Exception as e:
                    print(f"[RAG] LLM error (full_card): {e}")
                    return record_metrics({
                        "mode": "concise",
                        "intent": intent,
                        "answer": "I am experiencing high traffic right now and couldn't process your request. Please try again in a moment.",
                        "confidence": 0,
                        "debug_info": debug_info,
                    })

        if pages:
            top_evidence = supporting_evidence[0]["evidence"]
            if direct_answer:
                answer = top_evidence
            else:
                answer = (
                    f"Answer: {top_evidence}\n"
                    f"Confidence Score: {82 if asset_tag else 72}%\n"
                    f"Source Document: {citations[0]['document_name']}\n"
                    f"Page Number: {citations[0]['page_number']}\n"
                    f"Section Title: {citations[0]['section_title']}\n"
                    f"Supporting Evidence: {supporting_evidence[0]['evidence']}"
                )
            return record_metrics({
                "answer": answer,
                "sources": sources,
                "confidence": 82 if asset_tag else 72,
                "intent": intent,
                "equipment": asset_tag,
                "citations": citations,
                "supporting_evidence": supporting_evidence,
                "mode": "concise" if direct_answer else "full_card",
                "debug_info": debug_info,
            })

        if not pages:
            # Fallback when LLM synthesis is disabled or unavailable
            return record_metrics({
                "answer": "No information found.",
                "sources": [],
                "confidence": 0,
                "intent": intent,
                "equipment": asset_tag,
                "citations": [],
                "supporting_evidence": [],
                "mode": "concise" if direct_answer else "full_card",
                "debug_info": debug_info,
            })

rag_engine = RAGEngine()
