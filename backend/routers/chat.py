from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Union
import datetime
import time
import re
from sqlalchemy.orm import Session
from database import get_db
from models.domain import ChatMessage as DBMessage, Incident, Asset, KnowledgeEdge, KnowledgeNode
from services.enterprise_assistant_service import enterprise_assistant
from services.graph_service import graph_engine
from services.rag_service import rag_engine

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str
    sources: Optional[List[str]] = []
    confidence: Optional[int] = None
    time: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    retry: Optional[bool] = False

class RoutingInfo(BaseModel):
    intent: Optional[str] = None
    agent: Optional[str] = None
    label: Optional[str] = None
    retrieval_priority: Optional[List[str]] = []
    mode: Optional[str] = None
    reasoning: Optional[str] = None
    response_template: Optional[str] = None
    response_sections: Optional[List[str]] = []

class BaseChatResponse(BaseModel):
    message_id: int
    role: str
    content: str
    time: str
    sources: List[str] = []
    confidence: int
    intent: Optional[str] = None
    mode: str
    grounded: Optional[bool] = None
    routing: Optional[RoutingInfo] = None
    response_type: Optional[str] = None
    debug_info: Optional[Dict[str, Any]] = None

class ConciseResponse(BaseChatResponse):
    citations: List[Dict[str, Any]] = []
    supporting_evidence: List[Dict[str, Any]] = []

class EnterpriseResponse(BaseChatResponse):
    agent: Optional[str] = None
    label: Optional[str] = None
    equipment: Optional[str] = None
    citations: List[Dict[str, Any]] = []
    supporting_evidence: List[Dict[str, Any]] = []
    enterprise: Dict[str, Any] = {}
    rca_data: Optional[Dict[str, Any]] = None

class ManualLookupResponse(EnterpriseResponse):
    response_type: str = "manual_lookup"

class RCAResponse(EnterpriseResponse):
    response_type: str = "root_cause_analysis"

def extract_equipment_id(text: str) -> Optional[str]:
    """Extract standard equipment IDs like FM101, AC101, UPS101, or FM-101."""
    pattern = r"(?<![A-Z0-9])([A-Z]{1,3})-?(\d{3})(?![A-Z0-9])"
    matches = re.findall(pattern, text.upper())
    if matches:
        prefix, digits = matches[0]
        return f"{prefix}{digits}"
    return None


def format_asset_display_name(asset: Optional[Asset], asset_tag: Optional[str]) -> str:
    if asset and getattr(asset, "name", None):
        display_name = str(asset.name).strip()
        if asset_tag and asset_tag not in display_name.upper().replace("-", ""):
            return f"{display_name} {asset_tag}"
        return display_name
    return asset_tag or "Asset"


def query_database_context(message: str, db: Session) -> tuple[str, list, Optional[str], Optional[str]]:
    """
    GraphRAG implementation:
    1. Extract equipment ID
    2. Query Knowledge Graph
    3. Query targeted Asset/Incident data
    Returns (context_string, sources_list, asset_tag)
    """
    asset_tag = extract_equipment_id(message)
    context_parts = []
    sources = []
    graph_context = None
    
    if asset_tag:
        # 1. Targeted Asset Query
        asset = db.query(Asset).filter(Asset.tag == asset_tag).first()
        if asset:
            context_parts.append(
                f"## Asset Status ({asset_tag}):\n"
                f"- Name: {asset.name}\n"
                f"- Type: {asset.type}\n"
                f"- Health: {asset.health_score:.0f}%\n"
                f"- Status: {asset.status}\n"
                f"- Next PM: {asset.next_maintenance}"
            )
            sources.append("Asset Database")
            
            # 2. Targeted Incident Query (Strict)
            incidents = db.query(Incident).filter(Incident.asset_tag == asset_tag).order_by(Incident.created_at.desc()).limit(5).all()
            if incidents:
                rows = [f"- [{i.severity.upper()}] {i.title} | Status: {i.status} | Cause: {i.root_cause}" for i in incidents]
                context_parts.append("## Incidents for " + asset_tag + ":\n" + "\n".join(rows))
                sources.append("Incidents Database")
            else:
                status_text = asset.status.replace("_", " ").title() if asset.status else "Operational"
                display_name = format_asset_display_name(asset, asset_tag)
                context_parts.append(
                    f"No recorded failure incidents found for {display_name}. Current health: {asset.health_score:.0f}%, Status: {status_text}."
                )
        
        # 3. Knowledge Graph Query
        subgraph = graph_engine.get_subgraph_for_asset(asset_tag, db)
        graph_nodes = [node for node in subgraph.get("nodes", []) if node.get("id") != f"eq_{asset_tag}"]
        if graph_nodes:
            connected_items = []
            for node in graph_nodes:
                node_type = (node.get("type") or "document").replace("_", " ")
                connected_items.append(f"{node.get('label', node.get('id'))} ({node_type})")

            if connected_items:
                context_parts.append("## Connected Documents in Knowledge Graph:\n- " + "\n- ".join(connected_items))
                sources.append("Neo4j Knowledge Graph")
                graph_context = ", ".join(connected_items)

    else:
        # Fallback to general search if no asset specified
        msg_lower = message.lower()
        if any(k in msg_lower for k in ["incident", "failure", "alert"]):
            incidents = db.query(Incident).order_by(Incident.created_at.desc()).limit(5).all()
            if incidents:
                rows = [f"- [{i.severity.upper()}] {i.title} | Asset: {i.asset_tag}" for i in incidents]
                context_parts.append("## Recent Incidents:\n" + "\n".join(rows))
                sources.append("Incidents Database")
                
        if any(k in msg_lower for k in ["maintenance", "overdue"]):
            assets = db.query(Asset).filter(Asset.next_maintenance != None).order_by(Asset.health_score.asc()).limit(5).all()
            if assets:
                rows = [f"- {a.tag} | {a.name} | Next PM: {a.next_maintenance}" for a in assets]
                context_parts.append("## Maintenance Schedule:\n" + "\n".join(rows))
                sources.append("Maintenance Database")

    return "\n\n".join(context_parts), sources, asset_tag, graph_context


def format_enterprise_response(enterprise: dict) -> str:
    route = enterprise.get("intent_routing", {})
    procedure = enterprise.get("procedure_response", {})
    rca = enterprise.get("root_cause_analysis", {})
    asset = enterprise.get("asset_information", {})
    incidents = enterprise.get("historical_incidents", {})
    maintenance = enterprise.get("maintenance_history", {})
    inspection = enterprise.get("inspection_findings", {})
    manual = enterprise.get("manual_recommendation", {})
    expert = enterprise.get("expert_recommendation", {})
    risk = enterprise.get("predictive_risk", {})
    actions = enterprise.get("recommended_actions", {})
    evidence = enterprise.get("evidence", [])

    def lines(items):
        return "\n".join([f"- {item}" for item in items if item]) or "- N/A"

    def bullet_list(items):
        return "\n".join([f"- {item}" for item in items if item]) or "- N/A"

    def confidence_label(value):
        if value is None:
            return "Medium"
        try:
            score = int(value)
        except (TypeError, ValueError):
            return str(value)
        if score >= 80:
            return "High"
        if score >= 60:
            return "Medium"
        return "Low"

    def grouped_evidence(items):
        grouped = []
        seen = set()
        for item in items[:5]:
            key = (item.get("document_name") or "", item.get("section") or "", item.get("incident_id") or "", item.get("maintenance_id") or "")
            if key in seen:
                continue
            seen.add(key)
            grouped.append(item)
        return grouped

    def citation_list(items):
        return "\n".join([
            f"- {item.get('document_name')} p.{item.get('page_number') or 'N/A'} | {item.get('section') or 'N/A'}"
            for item in grouped_evidence(items)
        ]) or "- No source citations available"

    def timeline_text(items):
        if not items:
            return "- No incident history available"
        lines_out = []
        for index, item in enumerate(items[:5]):
            date = item.get("date") or "Unknown"
            title = item.get("title") or "Event"
            severity = item.get("severity") or "Unknown"
            root_cause = item.get("root_cause") or "N/A"
            lines_out.append(f"{date}: {title} ({severity}) — {root_cause}")
            if index < len(items[:5]) - 1:
                lines_out.append("↓")
        return "\n".join(lines_out)

    if route.get("intent") in {"startup_procedure", "shutdown_procedure", "sop"} and procedure:
        # ── Applicable Equipment ──────────────────────────────────────────────
        applicable_eq: list = procedure.get("applicable_equipment") or []
        eq_list = "\n".join(f"- {eq}" for eq in applicable_eq) if applicable_eq else "- See document reference"

        # ── Purpose ───────────────────────────────────────────────────────────
        purpose = procedure.get("purpose") or "Standard operating procedure for safe equipment operation."

        # ── Prerequisites ─────────────────────────────────────────────────────
        prereqs = procedure.get("prerequisites") or []
        prereq_list = "\n".join(f"- {p}" for p in prereqs) if prereqs else "- N/A"

        # ── Required PPE ──────────────────────────────────────────────────────
        ppe_items = procedure.get("required_ppe") or []
        ppe_list = "\n".join(f"- {p}" for p in ppe_items) if ppe_items else "- Standard PPE required"

        # ── Step-by-Step Procedure ────────────────────────────────────────────
        steps = procedure.get("step_by_step_instructions") or []
        steps_text = (
            "\n".join(f"{i + 1}. {step}" for i, step in enumerate(steps))
            if steps else "- Refer to the indexed procedure document for detailed steps."
        )

        # ── Safety Warnings ───────────────────────────────────────────────────
        all_warnings = list(procedure.get("warnings") or []) + list(procedure.get("safety_checks") or [])
        warnings_text = "\n".join(f"⚠ {w}" for w in all_warnings) if all_warnings else "- Follow site safety standards and permit-to-work requirements."

        # ── Completion Criteria ───────────────────────────────────────────────
        criteria = procedure.get("completion_criteria") or []
        criteria_text = "\n".join(f"✓ {c}" for c in criteria) if criteria else "- N/A"

        # ── Content Status ────────────────────────────────────────────────────
        doc_status = procedure.get("content_status", "complete")
        partial_notice = (
            "\n> ⚠ Procedure document found. Detailed content is partially indexed."
            if doc_status == "partial" else ""
        )

        # ── Document Reference ────────────────────────────────────────────────
        doc_ref = procedure.get("document") or "Not indexed"
        page_ref = procedure.get("page_number") or "N/A"
        section_ref = procedure.get("section") or "N/A"
        conf_val = procedure.get("confidence") or 0
        conf_label = "High" if conf_val >= 90 else "Medium" if conf_val >= 70 else "Low"

        # ── Source Citations ──────────────────────────────────────────────────
        sop_evidence = grouped_evidence(evidence)
        sop_citations = citation_list(sop_evidence) if sop_evidence else "- No indexed source citations available."

        return f"""# SOP: {procedure.get("sop_name") or procedure.get("relevant_procedure") or "Standard Operating Procedure"}

**Applicable Equipment:**
{eq_list}

**Purpose:** {purpose}

---

## Prerequisites
{prereq_list}

## Required PPE
{ppe_list}

## Step-by-Step Procedure
{steps_text}{partial_notice}

## Safety Warnings
{warnings_text}

## Completion Criteria
{criteria_text}

---

## Document Reference
- **Document Name:** {doc_ref}
- **Page Number:** {page_ref}
- **Section:** {section_ref}
- **Confidence:** {conf_label} ({conf_val}%)

## Source Citations
{sop_citations}
"""

    if route.get("intent") == "manual_lookup":
        manual = enterprise.get("manual_recommendation") or procedure
        summary_text = manual.get("summary") or manual.get("primary_answer") or "No manual summary is available."
        instructions = manual.get("key_instructions") or []
        instructions_text = "\n".join(f"- {inst}" for inst in instructions) if instructions else "- No key instructions extracted."
        document = manual.get("document") or "Not indexed"
        page_number = manual.get("page_number") or "N/A"
        section = manual.get("section") or "N/A"
        confidence_val = manual.get("confidence") or 0
        confidence_label = "High" if confidence_val >= 90 else "Medium" if confidence_val >= 70 else "Low"
        sources_text = citation_list(evidence)

        return f"""# Manual Lookup: {document}

**Summary:**
{summary_text}

## Key Instructions
{instructions_text}

## Document Reference
- **Document Name:** {document}
- **Page Number:** {page_number}
- **Section:** {section}
- **Confidence:** {confidence_label} ({confidence_val}%)

## Sources
{sources_text}
"""

    if route.get("intent") == "root_cause_analysis":
        concise_evidence = grouped_evidence(evidence)
        evidence_text = "\n".join([
            f"- {item.get('document_name')} | p.{item.get('page_number') or 'N/A'} | {item.get('section')} | {item.get('excerpt')}"
            for item in concise_evidence
        ]) or "- No evidence available"
        recurring_marker = "Recurring failures observed" if "recurring" in (incidents.get("trend") or "").lower() or len(incidents.get("timeline", [])) > 1 else "No recurring pattern"
        return f"""# Executive Summary
{enterprise.get("primary_answer") or enterprise.get("executive_summary", "No summary available.")}

# Root Cause
{rca.get('most_probable_root_cause') or 'No confirmed cause available.'}

# Business Impact
Asset: {asset.get('asset_name')} | Health: {asset.get('current_health')} | Status: {asset.get('operational_status')} | Risk: {risk.get('risk_level')} | Failure Probability: {risk.get('failure_probability')}

# Corrective Action
{bullet_list(actions.get('immediate_actions', []))}

# Preventive Action
{bullet_list(actions.get('preventive_actions', []))}

# Evidence
{evidence_text}

# Source Citations
{citation_list(concise_evidence)}

# AI Explainability
- Reasoning Score: {confidence_label(rca.get('confidence_score'))}
- Maintenance History: {maintenance.get('recent_maintenance')} | {maintenance.get('pending_maintenance')}
- Sensor Data: {asset.get('current_health')} health, status {asset.get('operational_status')}
- Inspection: {inspection.get('latest_inspection')} — {inspection.get('observations')}
- Expert Notes: {bullet_list(expert.get('best_practices', []))}
- Historical Pattern: {incidents.get('trend') or 'No recurring pattern available'}

# Failure Timeline
{timeline_text(incidents.get('timeline', []))}
- {recurring_marker}
"""

    evidence_lines = "\n".join([
        f"- {item.get('document_name')} p.{item.get('page_number') or 'N/A'} — {item.get('excerpt')}"
        for item in grouped_evidence(evidence)
    ]) or "- No evidence available"
    return f"""# Executive Summary
{enterprise.get('primary_answer') or enterprise.get('executive_summary', 'No summary available.')}

# Root Cause
{rca.get('most_probable_root_cause') or 'No confirmed cause available.'}

# Business Impact
Asset: {asset.get('asset_name')} | Health: {asset.get('current_health')} | Status: {asset.get('operational_status')}

# Corrective Action
- {lines(actions.get('immediate_actions', []))}

# Preventive Action
- {lines(actions.get('preventive_actions', []))}

# Evidence
{evidence_lines}
"""

@router.get("/history")
def get_chat_history(db: Session = Depends(get_db)):
    return db.query(DBMessage).order_by(DBMessage.id).all()

@router.delete("/history")
def clear_chat_history(db: Session = Depends(get_db)):
    db.query(DBMessage).delete()
    db.commit()
    return {"status": "success"}

@router.delete("/history/{message_id}")
def delete_chat_message(message_id: int, db: Session = Depends(get_db)):
    msg = db.query(DBMessage).filter(DBMessage.id == message_id).first()
    if msg:
        db.delete(msg)
        db.commit()
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Message not found")

@router.post("/feedback")
def submit_feedback(feedback: dict, db: Session = Depends(get_db)):
    from models.domain import Feedback
    fb = Feedback(
        message_id=feedback.get("message_id"),
        rating=feedback.get("rating"),
        comment=feedback.get("comment", "")
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return {"status": "success", "feedback_id": fb.id}

@router.get("/feedback")
def list_feedback(db: Session = Depends(get_db)):
    from models.domain import Feedback
    return db.query(Feedback).order_by(Feedback.created_at.desc()).all()

from services.cache_service import cache_service

@router.post("")
def chat_copilot(request: ChatRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    now_str = datetime.datetime.now().strftime("%I:%M %p")
    
    # 0. Check Cache (unless retry is requested)
    cache_key = f"chat:llm_response:{request.message.strip().lower()}"
    if not request.retry:
        cached_entry = cache_service.get(cache_key)
        if cached_entry:
            print(f"[Chat] Cache hit for query: {cache_key}")
            # Update time and save DB message
            cached_response = cached_entry.copy()
            cached_response["time"] = now_str
            cached_response["cached"] = True
            
            user_msg = DBMessage(role="user", content=request.message, time=now_str)
            db.add(user_msg)
            db.flush()
            
            bot_msg = DBMessage(
                role="assistant",
                content=cached_response.get("content", ""),
                time=now_str,
                sources=",".join(cached_response.get("sources", [])[:12]),
                confidence=cached_response.get("confidence", 0),
            )
            db.add(bot_msg)
            db.commit()
            db.refresh(bot_msg)
            cached_response["message_id"] = bot_msg.id
            
            total_time = time.time() - start_time
            if cached_response.get("debug_info"):
                cached_response["debug_info"]["total_response_time_ms"] = round(total_time * 1000, 2)
                
            return cached_response
            
    # Save user message to DB
    user_msg = DBMessage(role="user", content=request.message, time=now_str)
    db.add(user_msg)
    db.flush()

    # 1. Lightweight query router decides concise vs full_card path.
    t0_intent = time.time()
    if rag_engine.has_api_key and rag_engine.init_error:
        print(f"[Chat] RAG Engine init failed: {rag_engine.init_error}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI initialization failed. Check GOOGLE_MODEL/GOOGLE_EMBEDDING_MODEL and your Gemini credentials.",
        )

    query_route = rag_engine.route_query(request.message)
    mode = query_route.get("mode", "full_card")

    # 2. Intelligent Orchestration Layer (New Architecture)
    # Classify intent, select agent, and get the retrieval plan & priority weights
    from agents.orchestrator import orchestrator_agent
    retrieval_plan = orchestrator_agent.classify_intent(request.message)
    routed_intent_name = retrieval_plan.get("intent")
    agent_name = retrieval_plan.get("agent")
    t1_intent = time.time()
    intent_time_ms = round((t1_intent - t0_intent) * 1000, 2)

    # 3. GraphRAG Database Extraction
    # Only inject raw Asset/Incident/Maintenance DB rows for cross-document intents.
    # For single-document intents (QA, Inspection, SOP, Manual, etc.), skip to prevent cross-contamination.
    t0_retrieval = time.time()
    is_cross_document = retrieval_plan.get("cross_document", False)
    
    if is_cross_document:
        db_context, db_sources, asset_tag, graph_context = query_database_context(request.message, db)
    else:
        # Still extract asset_tag for metadata filtering, but don't inject DB context
        asset_tag = extract_equipment_id(request.message)
        db_context = ""
        db_sources = []
        graph_context = None

    # 3a. PREDICTIVE INTELLIGENCE LAYER
    # If this is a predictive query, compute a structured risk assessment from live data
    # and inject it as authoritative context before RAG retrieval runs.
    if routed_intent_name == "Predictive" and asset_tag:
        try:
            from services.predictive_maintenance_assistant import PredictiveMaintenanceAssistant
            insights = PredictiveMaintenanceAssistant.get_predictive_insights(db, asset_tag)
            risk = insights.get("risk_assessment", {})
            advisory = insights.get("advisory", {})
            
            predictive_context = (
                f"\n## Predictive Intelligence Report for {asset_tag}\n"
                f"**Asset Name:** {risk.get('asset_name', asset_tag)}\n"
                f"**Current Health Score:** {risk.get('current_health', 'N/A')}/100\n"
                f"**Health Status:** {risk.get('health_status', 'N/A').replace('_', ' ').title()}\n"
                f"**Equipment Status:** {risk.get('equipment_status', 'N/A').replace('_', ' ').title()}\n"
                f"**Failure Probability:** {risk.get('failure_probability', 'N/A')}%\n"
                f"**Risk Level:** {risk.get('risk_level', 'N/A')}\n"
                f"**Trend:** {risk.get('trend', 'N/A')}\n"
                f"**Recent Incidents (90 days):** {risk.get('recent_incidents', 0)}\n"
                f"**Total Historical Incidents:** {risk.get('total_incidents', 0)}\n"
                f"**Days Since Last Failure:** {risk.get('days_since_failure', 'No recorded failures')}\n"
                f"**Next Inspection Due:** {risk.get('next_inspection_due', 'N/A')}\n"
                f"**Recommendation:** {risk.get('recommendation', 'N/A')}\n"
            )
            
            if advisory and isinstance(advisory, dict):
                predictive_context += (
                    f"\n### AI Maintenance Advisory\n"
                    f"**Risk Level:** {advisory.get('risk_level', 'N/A')}\n"
                    f"**Headline:** {advisory.get('headline', 'N/A')}\n"
                    f"**Predicted Failure Window:** {advisory.get('predicted_failure_window', 'N/A')}\n"
                )
                risk_factors = advisory.get("key_risk_factors", [])
                if risk_factors:
                    predictive_context += "**Key Risk Factors:**\n" + "\n".join(f"  - {f}" for f in risk_factors) + "\n"
                
                rec = advisory.get("recommended_action", {})
                if rec:
                    predictive_context += (
                        f"**Recommended Action:** {rec.get('action_type', 'N/A')} — {rec.get('description', 'N/A')}\n"
                        f"**Urgency:** {rec.get('urgency', 'N/A')}\n"
                        f"**Cost of Inaction:** {rec.get('estimated_cost_of_inaction', 'N/A')}\n"
                    )
                checklist = advisory.get("maintenance_checklist", [])
                if checklist:
                    predictive_context += "**Maintenance Checklist:**\n" + "\n".join(f"  - {c}" for c in checklist) + "\n"
            
            db_context = predictive_context + ("\n\n" + db_context if db_context else "")
            if "Predictive Intelligence Engine" not in db_sources:
                db_sources.insert(0, "Predictive Intelligence Engine")
            print(f"[Predictive] Risk assessment injected for {asset_tag}: Health={risk.get('current_health')}%, FailureProb={risk.get('failure_probability')}%")
        except Exception as e:
            print(f"[Predictive] Failed to compute insights for {asset_tag}: {e}")
    elif routed_intent_name == "Predictive" and not asset_tag:
        # Fleet-level predictive summary when no specific asset is mentioned
        try:
            all_assets = db.query(Asset).order_by(Asset.health_score.asc()).limit(10).all()
            if all_assets:
                fleet_rows = []
                for a in all_assets:
                    status_emoji = "🔴" if a.health_score < 40 else ("🟡" if a.health_score < 70 else "🟢")
                    fleet_rows.append(
                        f"  - {status_emoji} **{a.tag}** ({a.name}): Health={a.health_score:.0f}%, Status={a.status}, Next PM={a.next_maintenance or 'Not scheduled'}"
                    )
                fleet_context = (
                    "\n## Fleet Health Overview\n"
                    "Assets sorted by health score (lowest first — most at risk):\n"
                    + "\n".join(fleet_rows)
                )
                db_context = fleet_context + ("\n\n" + db_context if db_context else "")
                if "Predictive Intelligence Engine" not in db_sources:
                    db_sources.insert(0, "Predictive Intelligence Engine")
                print(f"[Predictive] Fleet overview injected for {len(all_assets)} assets")
        except Exception as e:
            print(f"[Predictive] Fleet overview failed: {e}")
    
    # 4. Page-first GraphRAG retrieval. Graph context narrows pages; Chroma ranks
    # page-scoped chunks; Gemini receives exact pages only.
    conversation_history = request.history or [
        {"role": msg.role, "content": msg.content}
        for msg in db.query(DBMessage)
            .order_by(DBMessage.id.desc())
            .limit(12)
            .all()[::-1]
    ]


    try:
        if mode == "concise":
            rag_response = rag_engine.query(
                request.message,
                context_docs=[db_context] if db_context else None,
                asset_tag=asset_tag,
                graph_context=graph_context,
                db=db,
                synthesize=True,
                retrieval_plan=retrieval_plan,
                history=conversation_history,
                direct_answer=True,
            )
            answer = rag_response.get("answer")
            final_sources = list(dict.fromkeys((rag_response.get("sources") or []) + db_sources))
            confidence = rag_response.get("confidence", 72)

            bot_msg = DBMessage(
                role="assistant",
                content=answer,
                time=now_str,
                sources=",".join(final_sources[:12]),
                confidence=confidence,
            )
            db.add(bot_msg)
            db.commit()
            db.refresh(bot_msg)

            total_time = time.time() - start_time
            if "debug_info" not in rag_response:
                rag_response["debug_info"] = {}
            rag_response["debug_info"]["intent_routing_time_ms"] = intent_time_ms
            rag_response["debug_info"]["total_response_time_ms"] = round(total_time * 1000, 2)
            
            response_obj = {
                "message_id": bot_msg.id,
                "role": "assistant",
                "content": answer,
                "sources": final_sources,
                "confidence": confidence,
                "time": now_str,
                "intent": rag_response.get("intent"),
                "mode": mode,
                "response_type": "concise",
                "grounded": bool(final_sources),
                "routing": {
                    "mode": mode,
                    "reasoning": query_route.get("reasoning"),
                },
                "citations": rag_response.get("citations", []),
                "supporting_evidence": rag_response.get("supporting_evidence", []),
                "debug_info": rag_response.get("debug_info", {}),
            }
            
            # Save to cache
            cache_service.set(cache_key, response_obj, ttl=600)
            
            return response_obj

        t0_rag = time.time()
        rag_response = rag_engine.query(
            request.message,
            context_docs=[db_context] if db_context else None,
            asset_tag=asset_tag,
            graph_context=graph_context,
            db=db,
            synthesize=True,
            retrieval_plan=retrieval_plan,
            history=conversation_history,
        )
        t1_rag = time.time()
        if "debug_info" not in rag_response:
            rag_response["debug_info"] = {}
        rag_response["debug_info"]["rag_time_ms"] = round((t1_rag - t0_rag) * 1000, 2)

    except Exception as e:
        print(f"[RAG] retrieval or generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable. Please try again shortly."
        )

    # 5. Extract the dynamic response data from the RAG JSON output
    parsed_json = rag_response.get("parsed_json", {})
    dynamic_data = parsed_json.get("data", {})
    answer = rag_response.get("answer", "")
    confidence = rag_response.get("confidence", 80)
    final_sources = list(dict.fromkeys((rag_response.get("sources") or []) + db_sources))
    intent_mapping = {
        "RCA": "root_cause_analysis",
        "Predictive": "predictive_maintenance",
        "manual_lookup": "manual_lookup",
        "startup_procedure": "startup_procedure",
        "shutdown_procedure": "shutdown_procedure",
        "sop": "sop"
    }
    response_type = intent_mapping.get(routed_intent_name, routed_intent_name)

    bot_msg = DBMessage(
        role="assistant",
        content=answer,
        time=now_str,
        sources=",".join(final_sources[:12]),
        confidence=confidence,
    )
    db.add(bot_msg)
    db.commit()
    db.refresh(bot_msg)

    response_obj = {
        "message_id": bot_msg.id,
        "role": "assistant",
        "content": answer,
        "sources": final_sources,
        "confidence": confidence,
        "time": now_str,
        "intent": routed_intent_name,
        "agent": agent_name,
        "citations": rag_response.get("citations", []),
        "supporting_evidence": rag_response.get("supporting_evidence", []),
        "enterprise": dynamic_data,
        "mode": mode,
        "response_type": response_type,
        "grounded": bool(final_sources),
        "safety_flag": rag_response.get("safety_flag", False),
        "follow_up_suggestions": rag_response.get("follow_up_suggestions", []),
        "routing": {
            "intent": routed_intent_name,
            "agent": agent_name,
            "retrieval_priority": retrieval_plan.get("allowed_doc_types"),
            "mode": mode,
            "reasoning": query_route.get("reasoning"),
            "response_template": "dynamic",
            "response_sections": retrieval_plan.get("response_template"),
        },
        "debug_info": rag_response.get("debug_info", {}),
    }

    # Add timing
    total_time = time.time() - start_time
    response_obj["debug_info"]["intent_routing_time_ms"] = intent_time_ms
    response_obj["debug_info"]["total_response_time_ms"] = round(total_time * 1000, 2)
    response_obj["debug_info"]["cache_stats"] = cache_service.get_stats()
    
    # Save to cache
    cache_service.set(cache_key, response_obj, ttl=600)
    
    return response_obj

from fastapi.responses import StreamingResponse

@router.post("/stream")
def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    now_str = datetime.datetime.now().strftime("%I:%M %p")
    
    # Save user message
    user_msg = DBMessage(role="user", content=request.message, time=now_str)
    db.add(user_msg)
    db.flush()

    query_route = rag_engine.route_query(request.message)
    mode = query_route.get("mode", "full_card")

    from agents.orchestrator import orchestrator_agent
    retrieval_plan = orchestrator_agent.classify_intent(request.message)
    routed_intent_name = retrieval_plan.get("intent")

    db_context, db_sources, asset_tag, graph_context = query_database_context(request.message, db)

    conversation_history = request.history or [
        {"role": msg.role, "content": msg.content}
        for msg in db.query(DBMessage)
            .order_by(DBMessage.id.desc())
            .limit(12)
            .all()[::-1]
    ]

    generator = rag_engine.query(
        request.message,
        context_docs=[db_context] if db_context else None,
        asset_tag=asset_tag,
        graph_context=graph_context,
        db=db,
        synthesize=True,
        retrieval_plan=retrieval_plan,
        history=conversation_history,
        direct_answer=(mode == "concise"),
        stream=True
    )

    return StreamingResponse(generator, media_type="text/event-stream")
