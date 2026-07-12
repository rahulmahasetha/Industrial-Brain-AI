import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.domain import Document, DocumentPage, Incident, KnowledgeEdge, KnowledgeNode, PageIndex
from services.cache_service import cache_service

try:
    from llama_parse import LlamaParse
except ImportError:
    LlamaParse = None


# Matches patterns like P101, CV101, HX-301, P-101A, V-2001, PMP-101
EQUIPMENT_PATTERN = r"(?<![A-Z0-9])([A-Z]{1,4})-?(\d{3,4}[A-Z]?)(?![A-Z0-9])"


def normalize_equipment_id(value: str) -> str:
    return value.upper().replace("-", "").strip()


def extract_equipment_ids(text: str) -> List[str]:
    matches = re.findall(EQUIPMENT_PATTERN, text.upper())
    return sorted({f"{prefix}{digits}" for prefix, digits in matches})


def detect_intent(query: str) -> str:
    lowered = query.lower()
    if any(word in lowered for word in ["why", "root cause", "failure", "failed", "trip", "alarm"]):
        return "root_cause"
    if any(word in lowered for word in ["procedure", "startup", "shutdown", "step", "sop"]):
        return "procedure"
    if any(word in lowered for word in ["maintenance", "inspection", "pm", "service"]):
        return "maintenance"
    if any(word in lowered for word in ["compliance", "audit", "standard", "permit"]):
        return "compliance"
    return "general"


def extract_keywords(text: str, limit: int = 10) -> List[str]:
    stop_words = {
        "about", "after", "again", "against", "between", "document", "equipment",
        "from", "have", "into", "manual", "page", "section", "should", "system",
        "that", "their", "there", "these", "this", "with", "where", "which",
    }
    words = re.findall(r"\b[A-Za-z][A-Za-z0-9_-]{4,}\b", text)
    ranked: Dict[str, int] = {}
    for word in words:
        key = word.lower()
        if key in stop_words:
            continue
        ranked[key] = ranked.get(key, 0) + 1
    return [word for word, _ in sorted(ranked.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def infer_procedure_type(text: str = "", document_name: str = "", section_title: str = "") -> str:
    haystack = f"{document_name} {section_title} {text}".upper().replace("-", " ")
    if any(term in haystack for term in ["STARTUP", "START UP", "PRE START", "COMMISSIONING"]):
        return "STARTUP"
    if any(term in haystack for term in ["SHUTDOWN", "SHUT DOWN", "STOP PROCEDURE", "SAFE STOP"]):
        return "SHUTDOWN"
    if any(term in haystack for term in ["EMERGENCY", "EVACUATION", "GAS LEAK", "FIRE SAFETY", "FIRST AID"]):
        return "EMERGENCY"
    if any(term in haystack for term in ["MAINTENANCE", "INSPECTION", "REPAIR", "OVERHAUL", "LOTO", "ISOLATION"]):
        return "MAINTENANCE"
    return "GENERAL"


def summarize_page(text: str, limit: int = 280) -> str:
    compact = re.sub(r"\s+", " ", text or "").strip()
    if len(compact) <= limit:
        return compact
    sentence_match = re.match(r"^(.{80,}?[.!?])\s", compact)
    if sentence_match and len(sentence_match.group(1)) <= limit:
        return sentence_match.group(1)
    return compact[: limit - 3].rstrip() + "..."


def extract_headings(text: str) -> List[str]:
    markdown = re.findall(r"^#{1,6}\s+(.+)$", text or "", re.MULTILINE)
    numbered = re.findall(r"^(?:\d+(?:\.\d+)*\.?\s+)([A-Z][^\n]{4,80})$", text or "", re.MULTILINE)
    return list(dict.fromkeys([h.strip() for h in markdown + numbered if h.strip()]))[:8]


def extract_tables(text: str) -> str:
    lines = [line for line in (text or "").splitlines() if "|" in line]
    return "\n".join(lines[:12])


def extract_images(text: str) -> str:
    images = re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", text or "")
    return ", ".join([alt or src for alt, src in images[:8]])


def split_page_into_smart_chunks(text: str, page_index_id: int, max_size: int = 1200) -> List[Dict[str, str]]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text or "") if block.strip()]
    chunks: List[Dict[str, str]] = []
    current = ""
    for block in blocks or [text or ""]:
        if len(current) + len(block) + 2 <= max_size:
            current = f"{current}\n\n{block}".strip()
            continue
        if current:
            chunk_id = f"page_{page_index_id}_chunk_{len(chunks) + 1}"
            chunks.append({"id": chunk_id, "text": current})
        current = block
    if current:
        chunk_id = f"page_{page_index_id}_chunk_{len(chunks) + 1}"
        chunks.append({"id": chunk_id, "text": current})
    return chunks


class PageIndexService:
    def build_page_record(
        self,
        db: Session,
        doc: Document,
        page_number: int,
        text: str,
        log_id: str = "",
        incident_id: str = "",
        inspection_id: str = "",
        sop_id: str = "",
        source_type: str = ""
    ) -> PageIndex:
        headings = extract_headings(text)
        equipment_ids = extract_equipment_ids(text)
        keywords = extract_keywords(text)
        page = PageIndex(
            document_id=doc.id,
            document_name=doc.title,
            page_number=page_number,
            section_title=headings[0] if headings else infer_section_title(doc.title, page_number),
            headings=",".join(headings),
            equipment_ids=",".join(equipment_ids),
            keywords=",".join(keywords),
            summary=summarize_page(text),
            extracted_text=text,
            tables=extract_tables(text),
            images=extract_images(text),
            procedure_type=infer_procedure_type(text=text, document_name=doc.title, section_title=headings[0] if headings else ""),
            indexing_status="metadata_extracted",
            log_id=log_id,
            incident_id=incident_id,
            inspection_id=inspection_id,
            sop_id=sop_id,
            source_type=source_type,
        )
        db.add(page)
        db.flush()
        page.embedding_id = f"page_{page.id}"
        
        chunks = split_page_into_smart_chunks(text, page.id)
        page.chunk_ids = ",".join([chunk["id"] for chunk in chunks])
        
        # Save chunks dynamically to PostgreSQL
        from models.domain import DocumentChunk
        for chunk in chunks:
            db_chunk = DocumentChunk(
                chunk_id=chunk["id"],
                page_index_id=page.id,
                document_id=doc.id,
                text=chunk["text"]
            )
            db.add(db_chunk)
            
        page.indexing_status = "indexed"
        return page

    def list_pages(
        self,
        db: Session,
        query: Optional[str] = None,
        document_id: Optional[int] = None,
        equipment: Optional[str] = None,
        status: Optional[str] = None,
        allowed_doc_types: Optional[List[str]] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> tuple[List[PageIndex], int]:
        q = db.query(PageIndex)
        if allowed_doc_types:
            q = q.join(Document, PageIndex.document_id == Document.id).filter(Document.type.in_(allowed_doc_types))
        if document_id:
            q = q.filter(PageIndex.document_id == document_id)
        if equipment:
            q = q.filter(PageIndex.equipment_ids.ilike(f"%{normalize_equipment_id(equipment)}%"))
        if status:
            q = q.filter(PageIndex.indexing_status == status)
        if query:
            like = f"%{query}%"
            q = q.filter(
                or_(
                    PageIndex.document_name.ilike(like),
                    PageIndex.section_title.ilike(like),
                    PageIndex.equipment_ids.ilike(like),
                    PageIndex.keywords.ilike(like),
                    PageIndex.summary.ilike(like),
                    PageIndex.extracted_text.ilike(like),
                )
            )
        total = q.count()
        pages = q.order_by(PageIndex.document_name, PageIndex.page_number).offset(skip).limit(limit).all()
        return pages, total

    def get_page(self, db: Session, page_id: int) -> Optional[PageIndex]:
        return db.query(PageIndex).filter(PageIndex.id == page_id).first()

    def search_pages(
        self,
        db: Session,
        query: str,
        equipment: Optional[str] = None,
        document_id: Optional[int] = None,
        graph_terms: Optional[List[str]] = None,
        allowed_doc_types: Optional[List[str]] = None,
        limit: int = 25,
        skip: int = 0,
        loose_match: bool = False,
    ) -> tuple[List[PageIndex], int]:
        pages, _ = self.list_pages(db, query=None, document_id=document_id, equipment=equipment, allowed_doc_types=allowed_doc_types, limit=100000, skip=0)
        
        # Pre-fetch document types for these pages
        doc_ids = list({p.document_id for p in pages if p.document_id})
        doc_types = {}
        if doc_ids:
            docs = db.query(Document).filter(Document.id.in_(doc_ids)).all()
            doc_types = {d.id: (d.type or "") for d in docs}
            
        query_terms = [term.lower() for term in re.findall(r"\b[A-Za-z0-9_-]{3,}\b", query)]
        graph_terms = [term.lower() for term in graph_terms or [] if term]
        date_window = infer_date_window(query)

        scored: List[tuple[int, PageIndex]] = []
        for page in pages:
            haystack = " ".join([
                page.document_name or "",
                page.section_title or "",
                page.equipment_ids or "",
                page.keywords or "",
                page.summary or "",
                page.extracted_text or "",
                doc_types.get(page.document_id, "")
            ]).lower()
            score = 0
            if equipment and normalize_equipment_id(equipment) in normalize_equipment_id(page.equipment_ids or ""):
                score += 8
            score += sum(2 for term in query_terms if term in haystack)
            score += sum(3 for term in graph_terms if term and term in haystack)
            if date_window and page_matches_date_window(page, date_window):
                score += 12
            if score > 0 or loose_match:
                scored.append((score, page))

        scored.sort(key=lambda item: (-item[0], item[1].document_name, item[1].page_number))
        total = len(scored)
        paginated_pages = [page for _, page in scored[skip : skip + limit]]
        return paginated_pages, total

    def page_matches_procedure_type(self, page: PageIndex, procedure_type: str) -> bool:
        if not procedure_type:
            return True
        expected = procedure_type.upper()
        actual = (getattr(page, "procedure_type", None) or "").upper()
        if not actual or actual == "GENERAL":
            actual = infer_procedure_type(
                text=page.extracted_text or page.summary or "",
                document_name=page.document_name or "",
                section_title=page.section_title or "",
            )
        return actual == expected

    def sync_procedure_metadata(self, db: Session) -> int:
        updated = 0
        for page in db.query(PageIndex).all():
            inferred = infer_procedure_type(
                text=page.extracted_text or page.summary or "",
                document_name=page.document_name or "",
                section_title=page.section_title or "",
            )
            current = (getattr(page, "procedure_type", None) or "GENERAL").upper()
            if current != inferred:
                page.procedure_type = inferred
                updated += 1
        if updated:
            db.commit()
        return updated

    def get_graph_connected_entities(self, db: Session, equipment: Optional[str]) -> List[str]:
        if not equipment:
            return []
            
        cache_key = f"kg:connected_entities:{equipment.lower()}"
        cached = cache_service.get(cache_key)
        if cached is not None:
            return cached
            
        try:
            asset_id = normalize_equipment_id(equipment)
            graph_ids = [f"eq_{asset_id}", asset_id]
            edges = db.query(KnowledgeEdge).filter(
                or_(KnowledgeEdge.source_id.in_(graph_ids), KnowledgeEdge.target_id.in_(graph_ids))
            ).all()
            node_ids = set()
            for edge in edges:
                if edge.source_id in graph_ids:
                    node_ids.add(edge.target_id)
                if edge.target_id in graph_ids:
                    node_ids.add(edge.source_id)
            nodes = db.query(KnowledgeNode).filter(KnowledgeNode.node_id.in_(node_ids)).all() if node_ids else []
            labels = [node.label for node in nodes if node.label]
            labels.extend([node_id for node_id in node_ids if not any(node.label == node_id for node in nodes)])
            
            terms = list(dict.fromkeys(labels))
            cache_service.set(cache_key, terms, ttl=3600)  # 1 hour cache
            return terms
            
        except Exception:
            return []

    def sync_legacy_document_pages(self, db: Session, document_id: Optional[int] = None) -> int:
        q = db.query(DocumentPage)
        if document_id:
            q = q.filter(DocumentPage.document_id == document_id)

        created = 0
        for legacy_page in q.all():
            exists = db.query(PageIndex).filter(
                PageIndex.document_id == legacy_page.document_id,
                PageIndex.page_number == legacy_page.page_number,
            ).first()
            if exists:
                continue
            doc = db.query(Document).filter(Document.id == legacy_page.document_id).first()
            if not doc:
                continue
            page = self.build_page_record(db, doc, legacy_page.page_number, legacy_page.content or "")
            if legacy_page.section_name and not page.section_title:
                page.section_title = legacy_page.section_name
            created += 1
        db.commit()
        return created

    def sync_structured_record_pages(self, db: Session) -> int:
        """Expose structured maintenance/incident rows as page-index records.

        The demo dataset loads maintenance CSV rows into the Incident table but
        does not parse the CSV into DocumentPage rows. Page-first RAG still needs
        a citable retrieval unit, so each operational record becomes a page in a
        synthetic maintenance document.
        """
        doc = db.query(Document).filter(Document.title == "maintenance_logs.csv").first()
        if not doc:
            doc = Document(
                title="maintenance_logs.csv",
                type="Maintenance",
                size="Structured records",
                status="processed",
            )
            db.add(doc)
            db.flush()

        created = 0
        incidents = db.query(Incident).order_by(Incident.created_at.desc()).all()
        for incident in incidents:
            exists = db.query(PageIndex).filter(
                PageIndex.document_id == doc.id,
                PageIndex.section_title == incident.title,
                PageIndex.page_number == incident.id,
            ).first()
            if exists:
                continue

            text = (
                f"# {incident.title}\n\n"
                f"Asset: {incident.asset_tag}\n"
                f"Date: {incident.created_at.date() if incident.created_at else 'Unknown'}\n"
                f"Severity: {incident.severity}\n"
                f"Status: {incident.status}\n"
                f"Symptoms: {incident.description}\n"
                f"Root Cause: {incident.root_cause}\n"
                f"Corrective Action: {incident.corrective_action}\n"
                f"Engineer: {incident.reported_by or incident.assigned_to}"
            )
            page = self.build_page_record(db, doc, incident.id, text)
            page.section_title = incident.title
            page.equipment_ids = incident.asset_tag
            page.keywords = ",".join(extract_keywords(text + " maintenance failure corrective root cause", limit=12))
            page.summary = (
                f"{incident.asset_tag} had {incident.title} on "
                f"{incident.created_at.date() if incident.created_at else 'an unknown date'}; "
                f"root cause: {incident.root_cause}."
            )
            created += 1

            incident_node_id = f"incident_{incident.id}"
            page_node_id = f"page_{page.id}"
            # incident node
            existing_incident_node = db.query(KnowledgeNode).filter_by(node_id=incident_node_id).first()
            if existing_incident_node:
                existing_incident_node.label = incident.title
            else:
                db.add(KnowledgeNode(node_id=incident_node_id, label=incident.title, node_type="incident"))

            # page node
            existing_page_node = db.query(KnowledgeNode).filter_by(node_id=page_node_id).first()
            if existing_page_node:
                existing_page_node.label = f"maintenance_logs.csv p.{page.page_number}"
            else:
                db.add(KnowledgeNode(node_id=page_node_id, label=f"maintenance_logs.csv p.{page.page_number}", node_type="page"))

            # equipment node
            if incident.asset_tag:
                existing_eq_node = db.query(KnowledgeNode).filter_by(node_id=f"eq_{incident.asset_tag}").first()
                if not existing_eq_node:
                    db.add(KnowledgeNode(node_id=f"eq_{incident.asset_tag}", label=incident.asset_tag, node_type="asset"))
                db.merge(KnowledgeEdge(source_id=f"eq_{incident.asset_tag}", target_id=incident_node_id, relationship="HAS_INCIDENT"))
                db.merge(KnowledgeEdge(source_id=incident_node_id, target_id=page_node_id, relationship="DOCUMENTED_ON"))

        doc.page_count = max(doc.page_count or 0, db.query(PageIndex).filter(PageIndex.document_id == doc.id).count())
        db.commit()
        return created

    def reindex_document(self, db: Session, document_id: int) -> Dict[str, Any]:
        from models.domain import DocumentChunk
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        deleted = db.query(PageIndex).filter(PageIndex.document_id == document_id).delete()
        created = self.sync_legacy_document_pages(db, document_id=document_id)
        if not created:
            created = self.index_document_from_source(db, document_id)
        return {"document_id": document_id, "deleted_pages": deleted, "indexed_pages": created}

    def index_document_from_source(self, db: Session, document_id: int) -> int:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return 0

        file_path = self.resolve_document_path(doc.document_name if hasattr(doc, "document_name") else doc.title)
        if not file_path:
            return 0

        pages: List[Dict[str, Any]] = []
        if LlamaParse:
            try:
                parser = LlamaParse(result_type="markdown", verbose=True)
                parsed_docs = parser.load_data(file_path)
                for parsed in parsed_docs:
                    page_num = parsed.metadata.get("page_label", len(pages) + 1) if hasattr(parsed, "metadata") else len(pages) + 1
                    pages.append({
                        "page_number": int(page_num) if str(page_num).isdigit() else len(pages) + 1,
                        "text": parsed.text,
                    })
            except Exception as exc:
                print(f"[page-index] LlamaParse unavailable for {doc.title}: {exc}")
                
        if not pages:
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(file_path)
                for p_num, page in enumerate(reader.pages, start=1):
                    extracted = page.extract_text()
                    if extracted and extracted.strip():
                        pages.append({
                            "page_number": p_num,
                            "text": extracted,
                        })
            except Exception as e:
                print(f"[page-index] PyPDF2 fallback failed for {doc.title}: {e}")

        if not pages:
            pages.append({
                "page_number": 1,
                "text": (
                    f"OCR/text extraction pending for {doc.title}. "
                    "Configure LlamaParse/OCR and run re-index to populate extracted page text."
                ),
                "pending": True,
            })

        created = 0
        for page in pages:
            page_record = self.build_page_record(db, doc, page["page_number"], page["text"])
            if page.get("pending"):
                page_record.indexing_status = "pending_ocr"
            created += 1
        doc.page_count = max(doc.page_count or 0, len(pages))
        db.commit()
        return created

    def resolve_pdf_viewer(self, db: Session, page_id: int) -> Dict[str, Any]:
        page = self.get_page(db, page_id)
        if not page:
            return {}
        file_url = self._find_document_url(page.document_name)
        paragraph = find_relevant_paragraph(page.extracted_text, page.summary)
        return {
            "page_id": page.id,
            "document_id": page.document_id,
            "document_name": page.document_name,
            "page_number": page.page_number,
            "section_title": page.section_title,
            "pdf_url": f"{file_url}#page={page.page_number}" if file_url else "",
            "highlight_text": paragraph,
        }

    def _find_document_url(self, document_name: str) -> str:
        upload_path = self.resolve_document_path(document_name, uploads_only=True)
        if os.path.exists(upload_path):
            return f"/api/page-index/files/uploads/{document_name}"

        dataset_root = self.dataset_root()
        for root, _, files in os.walk(dataset_root):
            if document_name in files:
                rel_path = os.path.relpath(os.path.join(root, document_name), dataset_root)
                return f"/api/page-index/files/dataset/{rel_path}"
        return ""

    def dataset_root(self) -> str:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        return os.path.join(repo_root, "IndustrialBrain")

    def resolve_document_path(self, document_name: str, uploads_only: bool = False) -> str:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        upload_candidates = [
            os.path.join(repo_root, "backend", "uploads", document_name),
            os.path.abspath(os.path.join("uploads", document_name)),
        ]
        for path in upload_candidates:
            if os.path.exists(path):
                return path
        if uploads_only:
            return upload_candidates[0]

        dataset_root = self.dataset_root()
        for root, _, files in os.walk(dataset_root):
            if document_name in files:
                return os.path.join(root, document_name)
        return ""


def infer_section_title(document_name: str, page_number: int) -> str:
    title = os.path.splitext(document_name or "")[0].replace("_", " ").replace("-", " ")
    return f"{title} - Page {page_number}".strip(" -")


def infer_date_window(query: str) -> Optional[tuple[datetime, datetime]]:
    lowered = query.lower()
    today = datetime.utcnow()
    if "last month" in lowered or "previous month" in lowered:
        first_this_month = datetime(today.year, today.month, 1)
        last_month_end = first_this_month
        year = first_this_month.year if first_this_month.month > 1 else first_this_month.year - 1
        month = first_this_month.month - 1 if first_this_month.month > 1 else 12
        return datetime(year, month, 1), last_month_end
    return None


def page_matches_date_window(page: PageIndex, date_window: tuple[datetime, datetime]) -> bool:
    start, end = date_window
    text = page.extracted_text or page.summary or ""
    for value in re.findall(r"\b20\d{2}-\d{2}-\d{2}\b", text):
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            continue
        if start <= parsed < end:
            return True
    return False


def find_relevant_paragraph(text: str, summary: str) -> str:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]
    if not paragraphs:
        return summary or ""
    if not summary:
        return paragraphs[0]
    summary_terms = set(re.findall(r"\b[a-z0-9]{4,}\b", summary.lower()))
    return max(
        paragraphs[:12],
        key=lambda para: len(summary_terms.intersection(re.findall(r"\b[a-z0-9]{4,}\b", para.lower()))),
    )


page_index_service = PageIndexService()

