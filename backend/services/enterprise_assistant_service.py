import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.domain import Asset, ComplianceRecord, Document, ExpertKnowledge, Incident, PageIndex
from services.graph_service import graph_engine
from services.page_index_service import detect_intent, extract_equipment_ids, infer_procedure_type, page_index_service


INTENT_ROUTES = {
    "startup_procedure": {
        "label": "Startup Procedure",
        "agent": "SOP Agent",
        "priority": ["SOP Documents", "Equipment Manual", "Page Index", "Expert Notes"],
    },
    "shutdown_procedure": {
        "label": "Shutdown Procedure",
        "agent": "SOP Agent",
        "priority": ["SOP Documents", "Equipment Manual", "Page Index", "Expert Notes"],
    },
    "sop": {
        "label": "SOP",
        "agent": "SOP Agent",
        "priority": ["SOP Documents", "Equipment Manual", "Page Index", "Expert Notes"],
    },
    "maintenance": {
        "label": "Maintenance",
        "agent": "Maintenance Agent",
        "priority": ["Maintenance Logs", "Equipment Manual", "Page Index", "Expert Notes"],
    },
    "root_cause_analysis": {
        "label": "Root Cause Analysis",
        "agent": "RCA Agent",
        "priority": ["Incident Reports", "Maintenance Logs", "Sensor Data", "Inspection Reports", "Page Index"],
    },
    "incident_search": {
        "label": "Incident Search",
        "agent": "Incident Agent",
        "priority": ["Incident Reports", "Maintenance Logs", "Page Index", "Knowledge Graph"],
    },
    "predictive_maintenance": {
        "label": "Predictive Maintenance",
        "agent": "Predictive Maintenance Agent",
        "priority": ["Sensor Data", "Maintenance Logs", "Incident Reports", "Inspection Reports", "Page Index"],
    },
    "compliance": {
        "label": "Compliance",
        "agent": "Compliance Agent",
        "priority": ["Compliance Documents", "SOP Documents", "Inspection Reports", "Page Index"],
    },
    "manual_lookup": {
        "label": "Manual Lookup",
        "agent": "Manual Lookup Agent",
        "priority": ["Equipment Manual", "Page Index", "SOP Documents", "Expert Notes"],
    },
    "inspection": {
        "label": "Inspection",
        "agent": "Inspection Agent",
        "priority": ["Inspection Reports", "Maintenance Logs", "Sensor Data", "Page Index"],
    },
    "expert_knowledge": {
        "label": "Expert Knowledge",
        "agent": "Expert Knowledge Agent",
        "priority": ["Expert Notes", "Equipment Manual", "Maintenance Logs", "Page Index"],
    },
}


def _split_csv(value: str) -> List[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def _risk_level(asset: Optional[Asset], incidents: List[Incident]) -> str:
    if not asset:
        return "Unknown"
    severe_recent = any((i.severity or "").lower() in {"high", "critical"} for i in incidents[:3])
    if asset.status in {"critical", "shutdown"} or asset.health_score < 55:
        return "Critical"
    if severe_recent or asset.status == "warning" or asset.health_score < 80:
        return "High"
    if incidents:
        return "Medium"
    return "Low"


def _failure_probability(asset: Optional[Asset], incidents: List[Incident]) -> int:
    if not asset:
        return 35
    base = max(5, min(95, int(100 - asset.health_score)))
    recent_penalty = min(35, len(incidents[:6]) * 6)
    if asset.status == "critical":
        base += 30
    elif asset.status == "warning":
        base += 15
    return max(5, min(95, base + recent_penalty))


def _trend(incidents: List[Incident]) -> str:
    if len(incidents) >= 4:
        return "Recurring reliability pattern; multiple events exist across the asset history."
    if len(incidents) >= 2:
        return "Intermittent repeat events; monitor for escalation."
    if len(incidents) == 1:
        return "Single known event in the available history."
    return "No recorded incident trend in the available history."


def _page_to_evidence(page: PageIndex, confidence: int = 78) -> Dict[str, Any]:
    maintenance_match = re.search(r"\bML-\d+\b", page.extracted_text or "")
    incident_match = re.search(r"\bINC\d+\b", page.extracted_text or page.document_name or "")
    inspection_match = re.search(r"\bINS\d+\b", page.extracted_text or page.document_name or "")
    excerpt = page.summary or (page.extracted_text or "")[:240]
    if _contains_internal_status(excerpt):
        excerpt = f"Procedure document identified from metadata: {page.document_name}."
    return {
        "document_name": page.document_name,
        "page_number": page.page_number,
        "section": page.section_title or "N/A",
        "page_index_id": page.id,
        "incident_id": incident_match.group(0) if incident_match else "",
        "maintenance_id": maintenance_match.group(0) if maintenance_match else "",
        "inspection_id": inspection_match.group(0) if inspection_match else "",
        "confidence": confidence,
        "excerpt": excerpt,
    }


def _contains_internal_status(value: str) -> bool:
    lowered = (value or "").lower()
    return any(term in lowered for term in [
        "ocr/text extraction pending",
        "ocr pending",
        "embedding pending",
        "index pending",
        "parser",
        "llamaparse",
        "chromadb",
        "configure llamaparse",
    ])


class EnterpriseAssistantService:
    def classify_intent(self, query: str) -> Dict[str, Any]:
        lowered = query.lower()
        if any(term in lowered for term in ["startup", "start-up", "start up", "commission", "start procedure"]):
            key = "startup_procedure"
        elif any(term in lowered for term in ["shutdown", "shut down", "stop procedure", "stopping procedure"]):
            key = "shutdown_procedure"
        elif any(term in lowered for term in ["sop", "standard operating procedure", "procedure", "steps", "instruction"]):
            key = "sop"
        elif any(term in lowered for term in ["predict", "failure probability", "rul", "remaining useful", "risk forecast"]):
            key = "predictive_maintenance"
        elif any(term in lowered for term in ["why", "root cause", "rca", "failed", "failure", "trip cause"]):
            key = "root_cause_analysis"
        elif any(term in lowered for term in ["incident", "history", "previous failure", "past failure", "event"]):
            key = "incident_search"
        elif any(term in lowered for term in ["inspection", "inspect", "finding", "observation"]):
            key = "inspection"
        elif any(term in lowered for term in ["compliance", "audit", "permit", "standard", "regulation", "iso", "factory act"]):
            key = "compliance"
        elif any(term in lowered for term in ["manual", "datasheet", "oem", "specification", "lookup"]):
            key = "manual_lookup"
        elif any(term in lowered for term in ["expert", "best practice", "senior engineer", "tribal knowledge"]):
            key = "expert_knowledge"
        elif any(term in lowered for term in ["maintenance", "pm", "service", "overhaul", "repair"]):
            key = "maintenance"
        else:
            fallback = detect_intent(query)
            key = {
                "root_cause": "root_cause_analysis",
                "procedure": "sop",
                "maintenance": "maintenance",
                "compliance": "compliance",
            }.get(fallback, "manual_lookup")

        route = INTENT_ROUTES[key]
        return {
            "intent": key,
            "label": route["label"],
            "agent": route["agent"],
            "retrieval_priority": route["priority"],
        }

    def generate(self, db: Session, query: str, asset_tag: Optional[str] = None, routed_intent: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        route = routed_intent or self.classify_intent(query)
        intent = route["intent"]
        extracted = extract_equipment_ids(query)
        asset_tag = asset_tag or (extracted[0] if extracted else None)

        page_index_service.sync_legacy_document_pages(db)
        page_index_service.sync_structured_record_pages(db)
        page_index_service.sync_procedure_metadata(db)

        asset = db.query(Asset).filter(Asset.tag == asset_tag).first() if asset_tag else None
        incidents = []
        if asset_tag:
            incidents = (
                db.query(Incident)
                .filter(Incident.asset_tag == asset_tag)
                .order_by(Incident.created_at.desc())
                .limit(12)
                .all()
            )

        subgraph = graph_engine.get_subgraph_for_asset(asset_tag, db) if asset_tag else {"nodes": [], "edges": []}
        graph_terms = [node.get("label") or node.get("id") for node in subgraph.get("nodes", [])]
        graph_terms = [term for term in graph_terms if term and term != asset_tag]
        self._ensure_connected_documents_indexed(db, asset_tag, graph_terms)

        routed_query = self._routed_query(query, intent)
        procedure_type = self._procedure_type_for_intent(intent)
        pages, _ = page_index_service.search_pages(
            db,
            query=routed_query,
            equipment=asset_tag,
            graph_terms=graph_terms,
            procedure_type=procedure_type,
            limit=16,
        )
        manual_pages = self._find_pages(db, asset_tag, self._manual_terms(intent), ["Manual"], procedure_type=procedure_type)
        sop_pages = self._find_pages(db, asset_tag, self._sop_terms(intent, query), ["SOP"], procedure_type=procedure_type)
        inspection_pages = self._find_pages(db, asset_tag, ["inspection", "risk", "observation"], ["Inspection"])
        compliance_pages = self._find_pages(db, asset_tag, ["compliance", "safety", "permit", "audit"], ["Compliance"])
        manual_pages = manual_pages or self._fallback_document_pages(db, "Manual", asset_tag, self._manual_terms(intent), procedure_type=procedure_type)
        sop_pages = sop_pages or self._fallback_document_pages(db, "SOP", asset_tag, self._sop_terms(intent, query), procedure_type=procedure_type)
        if not any((page.document_name or "").startswith("INS") for page in inspection_pages):
            inspection_pages = inspection_pages + self._fallback_document_pages(db, "Inspection", asset_tag, ["inspection", "risk"])
        if not any(self._is_compliance_document(page.document_name) for page in compliance_pages):
            compliance_pages = compliance_pages + self._fallback_document_pages(db, "Compliance", asset_tag, ["permit", "safety", "compliance"])

        expert_notes = self._expert_notes(db, asset_tag, query)
        latest_incident = incidents[0] if incidents else None
        risk = _risk_level(asset, incidents)
        probability = _failure_probability(asset, incidents)
        if self._is_procedure_intent(intent):
            evidence = self._build_sop_evidence(pages, manual_pages, sop_pages)
        else:
            evidence = self._build_evidence(
                pages,
                manual_pages,
                sop_pages,
                inspection_pages,
                compliance_pages,
                incidents,
                expert_notes,
                asset,
            )

        root_cause = latest_incident.root_cause if latest_incident else "No confirmed root cause in connected records."
        summary = self._summary(asset, latest_incident, root_cause, risk)

        if intent == "manual_lookup":
            manual_lookup_response = self._manual_lookup_response(
                query=query,
                asset=asset,
                sop_pages=sop_pages,
                manual_pages=manual_pages,
                pages=pages,
                expert_notes=expert_notes,
                incidents=incidents,
                probability=probability,
                risk=risk,
            )
            primary_answer = manual_lookup_response.get("primary_answer", summary)
            procedure_response = manual_lookup_response
        else:
            procedure_response = self._procedure_response(
                query=query,
                intent=intent,
                asset=asset,
                sop_pages=sop_pages,
                manual_pages=manual_pages,
                pages=pages,
                expert_notes=expert_notes,
                incidents=incidents,
                probability=probability,
                risk=risk,
            )
            primary_answer = procedure_response["primary_answer"] if self._is_procedure_intent(intent) else summary

        enterprise = {
            "intent_routing": route,
            "primary_answer": primary_answer,
            "executive_summary": primary_answer if self._is_procedure_intent(intent) or intent == "manual_lookup" else summary,
            "procedure_response": procedure_response,
            "manual_lookup_response": procedure_response if intent == "manual_lookup" else None,
            "response_template": self._response_template(intent),
            "response_sections": self._response_sections(intent),
            "asset_information": {
                "asset_name": asset.name if asset else asset_tag or "Unknown asset",
                "asset_type": asset.type if asset else "Unknown",
                "department": self._department(asset),
                "current_health": f"{asset.health_score:.0f}%" if asset else "Unknown",
                "operational_status": asset.status if asset else "Unknown",
                "sensor_snapshot": {
                    "temperature": asset.temperature if asset else None,
                    "vibration": asset.vibration if asset else None,
                    "power_draw": asset.power_draw if asset else None,
                    "lube_oil_level": asset.lube_oil_level if asset else "Unknown",
                },
            },
            "root_cause_analysis": {
                "most_probable_root_cause": root_cause,
                "confidence_score": 88 if latest_incident else 45,
                "supporting_evidence": [
                    latest_incident.description if latest_incident else "No incident row was found for this asset.",
                    latest_incident.corrective_action if latest_incident else "Use graph/page-index evidence before taking action.",
                ],
            },
            "historical_incidents": {
                "timeline": [
                    {
                        "date": i.created_at.date().isoformat() if i.created_at else "Unknown",
                        "title": i.title,
                        "severity": i.severity,
                        "root_cause": i.root_cause,
                    }
                    for i in incidents[:6]
                ],
                "frequency": f"{len(incidents)} connected incident/maintenance events found",
                "trend": _trend(incidents),
            },
            "maintenance_history": {
                "recent_maintenance": latest_incident.corrective_action if latest_incident else "No recent maintenance found",
                "pending_maintenance": asset.next_maintenance if asset and asset.next_maintenance else "Not scheduled in dataset",
                "technician": latest_incident.reported_by or latest_incident.assigned_to if latest_incident else "Unknown",
            },
            "inspection_findings": {
                "latest_inspection": inspection_pages[0].document_name if inspection_pages else "No direct indexed inspection found",
                "observations": self._safe_page_summary(
                    inspection_pages[0],
                    "Inspection document metadata is available; detailed observations require parsed inspection content."
                ) if inspection_pages else "Use maintenance symptoms and sensor trend as proxy until inspections are available.",
                "risk_level": risk,
            },
            "compliance_record": {
                "latest_compliance": compliance_pages[0].document_name if compliance_pages else "No compliance record found",
                "observations": self._safe_page_summary(
                    compliance_pages[0],
                    "Compliance document metadata is available; detailed observations require parsed content."
                ) if compliance_pages else "Use manual lookup for specific compliance standards.",
            },
            "manual_recommendation": {
                "relevant_maintenance_procedure": self._manual_recommendation(manual_pages, sop_pages, latest_incident),
                "document": self._document_name(manual_pages, sop_pages),
                "page_number": self._page_number(manual_pages, sop_pages),
                "section": self._section(manual_pages, sop_pages),
            },
            "expert_recommendation": {
                "best_practices": [note.condition for note in expert_notes[:3]] or [
                    "No asset-specific expert note found; follow OEM manual and site SOP."
                ]
            },
            "predictive_risk": {
                "failure_probability": f"{probability}%",
                "risk_level": risk,
                "estimated_remaining_useful_life": self._rul(asset, incidents, probability),
                "recommended_next_inspection": self._next_inspection(risk),
            },
            "recommended_actions": {
                "immediate_actions": self._immediate_actions(latest_incident, risk),
                "preventive_actions": self._preventive_actions(asset_tag, latest_incident),
                "long_term_improvements": [
                    "Trend vibration, temperature, current, and suction/discharge pressure against failure history.",
                    "Convert repeated corrective events into a preventive maintenance trigger.",
                    "Keep page-indexed manuals, inspections, SOPs, and compliance records linked to the asset graph.",
                ],
            },
            "evidence": evidence,
            "knowledge_graph_nodes_used": subgraph.get("nodes", [])[:18],
            "knowledge_graph_edges_used": subgraph.get("edges", [])[:24],
            "reasoning_timeline": [
                {"step": "Intent Detection", "detail": f"Detected intent: {route['label']}"},
                {"step": "Agent Routing", "detail": f"Routed to {route['agent']} with priority: {', '.join(route['retrieval_priority'])}."},
                {"step": "Procedure Type Filter", "detail": f"Applied procedure_type={procedure_type or 'N/A'} before semantic retrieval."},
                {"step": "Asset Filter", "detail": f"Applied asset filter: {asset_tag or 'none'}"},
                {"step": "Neo4j Graph Search", "detail": f"Collected {len(subgraph.get('nodes', []))} graph nodes and {len(subgraph.get('edges', []))} relationships."},
                {"step": "Page Index Search", "detail": f"Retrieved {len(pages)} page-index matches before semantic ranking."},
                {"step": "Semantic Retrieval", "detail": "Applied metadata-filtered semantic ranking when vector services are available."},
                {"step": "Multi-document Evidence Aggregation", "detail": f"Aggregated {len(evidence)} evidence records across operational sources."},
                {"step": "Gemini Analysis", "detail": "Structured response is ready for Gemini synthesis; deterministic fallback used when LLM is unavailable."},
                {"step": "Final Response", "detail": "Rendered as enterprise cards with evidence and citations."},
            ],
            "sources_covered": self._sources_covered(evidence, asset, expert_notes),
        }

        return enterprise

    def _is_procedure_intent(self, intent: str) -> bool:
        return intent in {"startup_procedure", "shutdown_procedure", "sop"}

    def _manual_lookup_response(
        self,
        query: str,
        asset: Optional[Asset],
        sop_pages: List[PageIndex],
        manual_pages: List[PageIndex],
        pages: List[PageIndex],
        expert_notes: List[ExpertKnowledge],
        incidents: List[Incident],
        probability: int,
        risk: str,
    ) -> Dict[str, Any]:
        page = self._select_procedure_page("manual_lookup", sop_pages, manual_pages, pages)
        asset_name = asset.name if asset else "the selected asset"
        procedure_name = page.section_title if page else "Manual lookup result"
        confidence = self._procedure_confidence(page, "manual_lookup", asset)
        document = page.document_name if page else "Not indexed"
        page_number = page.page_number if page else "N/A"
        section = page.section_title if page else "N/A"
        summary = self._safe_page_summary(page, "No manual content available in indexed documents.")
        instructions = self._extract_steps(page.extracted_text if page else "", "manual_lookup", asset_name) if page else []
        if not instructions and page:
            instructions = [summary] if summary else []

        return {
            "primary_answer": f"Found manual reference for {asset_name}: {procedure_name}." if page else f"No indexed manual reference found for {asset_name}.",
            "document": document,
            "page_number": page_number,
            "section": section,
            "confidence": confidence,
            "content_status": "complete" if page else "missing",
            "summary": summary,
            "key_instructions": instructions,
            "related_manual": document,
            "search_terms": query,
            "manual_pages_found": len(manual_pages),
            "page_index_id": page.id if page else None,
        }

    def _response_template(self, intent: str) -> str:
        templates = {
            "startup_procedure": "startup",
            "shutdown_procedure": "startup",
            "sop": "procedure",
            "root_cause_analysis": "root_cause",
            "incident_search": "incident",
            "maintenance": "maintenance",
            "inspection": "inspection",
            "compliance": "compliance",
            "manual_lookup": "manual",
            "expert_knowledge": "expert",
            "predictive_maintenance": "predictive",
            "knowledge_graph": "graph",
            "asset_overview": "asset",
        }
        return templates.get(intent, "general")

    def _response_sections(self, intent: str) -> List[str]:
        mapping = {
            "startup_procedure": ["Procedure", "Prerequisites", "Steps", "Safety Checks", "Warnings", "Documents", "Pages"],
            "shutdown_procedure": ["Procedure", "Prerequisites", "Steps", "Safety Checks", "Warnings", "Documents", "Pages"],
            "sop": ["Procedure", "Prerequisites", "Steps", "Safety Checks", "Warnings", "Documents", "Pages"],
            "root_cause_analysis": ["Executive Summary", "Root Cause", "Business Impact", "Corrective Action", "Preventive Action", "Evidence", "AI Explainability", "Failure Timeline"],
            "incident_search": ["Incident Summary", "Severity", "Timeline", "Recommended Action"],
            "maintenance": ["Last Maintenance", "Pending Work", "Technician", "Cost", "Related Insights"],
            "inspection": ["Latest Inspection", "Findings", "Risk Level", "Recommended Follow-up"],
            "compliance": ["Compliance Score", "Missing Documents", "Required Actions", "Related Insights"],
            "manual_lookup": ["Manual Summary", "Relevant Page", "Key Instructions", "Related Insights"],
            "expert_knowledge": ["Expert Guidance", "Recommended Action", "Confidence", "Source Notes"],
            "predictive_maintenance": ["Health Score", "Failure Probability", "Remaining Useful Life", "Trend"],
            "knowledge_graph": ["Asset Summary", "Connected Documents", "Connected Incidents", "Connected SOPs", "Connected Inspections", "Graph Statistics"],
            "asset_overview": ["Asset Summary", "Current Health", "Status", "Key Metrics", "Related Insights"],
        }
        return mapping.get(intent, ["Summary", "Evidence", "Recommended Actions", "Related Insights"])

    def _routed_query(self, query: str, intent: str) -> str:
        if intent == "startup_procedure":
            return f"{query} startup start-up SOP standard operating procedure safe start sequence"
        if intent == "shutdown_procedure":
            return f"{query} shutdown stop SOP standard operating procedure safe isolation"
        if intent == "sop":
            return f"{query} SOP standard operating procedure steps safety checks"
        if intent == "manual_lookup":
            return f"{query} manual OEM equipment specification operation maintenance"
        return query

    def _procedure_type_for_intent(self, intent: str) -> Optional[str]:
        if intent == "startup_procedure":
            return "STARTUP"
        if intent == "shutdown_procedure":
            return "SHUTDOWN"
        if intent == "maintenance":
            return "MAINTENANCE"
        if intent == "sop":
            return None
        return None

    def _sop_terms(self, intent: str, query: str) -> List[str]:
        if intent == "startup_procedure":
            return ["startup", "start-up", "start up", "pre-start", "filling", "machine"]
        if intent == "shutdown_procedure":
            return ["shutdown", "shut down", "stop", "isolation", "filling", "machine"]
        if intent == "sop":
            return ["sop", "procedure", "step", "instruction", "safety"]
        return ["startup", "shutdown", "procedure", "sop"]

    def _manual_terms(self, intent: str) -> List[str]:
        if intent == "startup_procedure":
            return ["manual", "startup", "operation", "pre-start", "commissioning"]
        if intent == "shutdown_procedure":
            return ["manual", "shutdown", "operation", "stop", "isolation"]
        return ["manual", "maintenance procedure", "operation", "filling", "machine"]

    def _procedure_response(
        self,
        query: str,
        intent: str,
        asset: Optional[Asset],
        sop_pages: List[PageIndex],
        manual_pages: List[PageIndex],
        pages: List[PageIndex],
        expert_notes: List[ExpertKnowledge],
        incidents: List[Incident],
        probability: int,
        risk: str,
    ) -> Dict[str, Any]:
        procedure_page = self._select_procedure_page(intent, sop_pages, manual_pages, pages)
        asset_name = asset.name if asset else "the selected asset"
        asset_label = asset.name if asset else "Bottle Filling Machine FM101" if "fm101" in query.lower() else asset_name
        intent_label = INTENT_ROUTES[intent]["label"] if intent in INTENT_ROUTES else "Procedure"
        procedure_name = procedure_page.section_title if procedure_page else f"{intent_label} for {asset_name}"
        procedure_confidence = self._procedure_confidence(procedure_page, intent, asset)

        if self._is_procedure_intent(intent) and not procedure_page:
            procedure_label = "startup" if intent == "startup_procedure" else "shutdown" if intent == "shutdown_procedure" else "SOP"
            primary_answer = f"No {procedure_label} procedure was found for {asset_label}."
        elif self._is_procedure_intent(intent) and procedure_confidence < 65:
            procedure_label = "startup" if intent == "startup_procedure" else "shutdown" if intent == "shutdown_procedure" else "SOP"
            primary_answer = f"No verified {procedure_label} procedure found."
        else:
            primary_answer = (
                f"The applicable {intent_label.lower()} for {asset_name} is "
                f"{procedure_name}."
                if self._is_procedure_intent(intent)
                else f"Routed to {INTENT_ROUTES.get(intent, INTENT_ROUTES['manual_lookup'])['agent']} for {asset_name}."
            )

        step_source = procedure_page.extracted_text if procedure_page else ""
        steps = self._extract_steps(step_source, intent, asset_name) if procedure_confidence >= 65 else []
        safety_checks = self._safety_checks(intent, asset, incidents)
        related_sop = procedure_page.document_name if procedure_page else "No indexed SOP found"

        related_incidents = [
            {
                "date": incident.created_at.date().isoformat() if incident.created_at else "Unknown",
                "title": incident.title,
                "root_cause": incident.root_cause,
                "severity": incident.severity,
            }
            for incident in incidents[:4]
        ]
        expert_tips = [note.condition for note in expert_notes[:3]]
        predictive_alerts = []
        if probability >= 60:
            predictive_alerts.append(f"Failure probability is elevated at {probability}%; complete checks before executing the procedure.")
        if risk in {"Critical", "High"}:
            predictive_alerts.append(f"{risk} operational risk: supervisor approval and post-procedure monitoring are recommended.")
        if not predictive_alerts:
            predictive_alerts.append("No high predictive alert from current sensor and incident context.")

        applicable_equipment = self._extract_applicable_equipment(procedure_page, asset.tag if asset else None)
        required_ppe = self._required_ppe(intent, procedure_page)
        completion_criteria = self._completion_criteria(intent, procedure_page)
        purpose = self._sop_purpose(intent, procedure_page, asset_name)
        content_status = self._content_status(procedure_page, procedure_confidence)

        return {
            "primary_answer": primary_answer,
            "sop_name": procedure_name,
            "applicable_equipment": applicable_equipment,
            "purpose": purpose,
            "relevant_procedure": procedure_name,
            "procedure_type": self._procedure_type_for_intent(intent) or "GENERAL",
            "confidence": procedure_confidence,
            "content_status": content_status,
            "estimated_duration": self._estimated_duration(intent),
            "prerequisites": self._prerequisites(intent, asset_name),
            "required_ppe": required_ppe,
            "step_by_step_instructions": steps,
            "safety_checks": safety_checks,
            "warnings": self._procedure_warnings(intent, incidents, risk),
            "completion_criteria": completion_criteria,
            "related_sop": related_sop,
            "document": procedure_page.document_name if procedure_page else "Not indexed",
            "page_number": procedure_page.page_number if procedure_page else "N/A",
            "section": procedure_page.section_title if procedure_page else "N/A",
            "page_index_id": procedure_page.id if procedure_page else None,
            "quick_actions": self._generate_quick_actions(intent, asset_name, procedure_name),
            "optional_context": {
                "historical_incidents": related_incidents,
                "expert_tips": expert_tips or ["No asset-specific expert tip found; follow site SOP and OEM manual."],
                "predictive_alerts": predictive_alerts,
            },
        }

    def _generate_quick_actions(self, intent: str, asset_name: str, procedure_name: str) -> List[str]:
        if intent in {"startup_procedure", "shutdown_procedure", "sop"}:
            return [
                f"Are there any active alerts or recent incidents for {asset_name}?",
                f"Show the maintenance history for {asset_name}.",
                f"What are the compliance and safety requirements for {asset_name}?"
            ]
        elif intent in {"root_cause_analysis", "incident_search"}:
            return [
                f"What is the predictive failure probability for {asset_name}?",
                f"Show me the asset knowledge graph for {asset_name}.",
                f"Are there expert recommendations to prevent this on {asset_name}?"
            ]
        elif intent in {"predictive_maintenance", "maintenance", "inspection"}:
            return [
                f"Show recent incident reports for {asset_name}.",
                f"What is the standard operating procedure for {asset_name}?",
                f"Show expert insights and best practices for {asset_name}."
            ]
        else:
            return [
                f"What is the current health status of {asset_name}?",
                f"Show recent incidents for {asset_name}.",
                f"Show predictive maintenance risk for {asset_name}."
            ]

    def _select_procedure_page(
        self,
        intent: str,
        sop_pages: List[PageIndex],
        manual_pages: List[PageIndex],
        pages: List[PageIndex],
    ) -> Optional[PageIndex]:
        ordered = sop_pages + manual_pages + pages
        if not ordered:
            return None
        if intent == "startup_procedure":
            for page in ordered:
                haystack = f"{page.document_name} {page.section_title} {page.summary} {page.extracted_text}".lower()
                if any(term in haystack for term in ["startup", "start-up", "start up"]):
                    return page
        if intent == "shutdown_procedure":
            for page in ordered:
                haystack = f"{page.document_name} {page.section_title} {page.summary} {page.extracted_text}".lower()
                if any(term in haystack for term in ["shutdown", "shut down", "stop"]):
                    return page
        return ordered[0]

    def _procedure_confidence(self, page: Optional[PageIndex], intent: str, asset: Optional[Asset]) -> int:
        if not page:
            return 0
        expected = self._procedure_type_for_intent(intent)
        haystack = f"{page.document_name} {page.section_title} {page.summary} {page.extracted_text}".lower()
        score = 20
        if expected and self._page_matches_procedure_type(page, expected):
            score += 35
        if intent == "startup_procedure" and any(term in haystack for term in ["startup", "start-up", "start up"]):
            score += 25
        if intent == "shutdown_procedure" and any(term in haystack for term in ["shutdown", "shut down", "stop"]):
            score += 25
        if "sop" in haystack:
            score += 10
        if asset and (asset.type or "").lower() in haystack:
            score += 10
        if asset and (asset.tag or "").lower() in haystack:
            score += 10
        return min(score, 100)

    def _extract_steps(self, text: str, intent: str, asset_name: str) -> List[str]:
        lines = [line.strip(" -\t") for line in (text or "").splitlines() if line.strip()]
        numbered = [
            re.sub(r"^\d+[\).:-]?\s*", "", line).strip()
            for line in lines
            if re.match(r"^\d+[\).:-]?\s+\S+", line)
        ]
        cleaned = [line for line in numbered if len(line) > 8][:8]
        if cleaned:
            return cleaned

        if intent == "startup_procedure":
            return [
                f"Verify work permits, guards, coupling area, and process line-up for {asset_name}.",
                "Confirm suction and discharge valves are in the required startup positions.",
                "Check lubrication, seal flush, cooling water, and electrical availability.",
                "Start the driver locally or from the control system as per site SOP.",
                "Ramp up gradually and verify pressure, flow, vibration, temperature, and current.",
                "Record startup readings and keep the asset under enhanced observation.",
            ]
        if intent == "shutdown_procedure":
            return [
                f"Notify operations and confirm {asset_name} can be stopped safely.",
                "Reduce load or flow gradually to avoid hydraulic or thermal shock.",
                "Stop the driver using the approved control point.",
                "Close or isolate valves according to SOP and process requirement.",
                "Apply LOTO if maintenance or inspection will follow.",
                "Record final readings and abnormal observations.",
            ]
        return [
            "Review the applicable SOP and confirm the asset tag, service, and operating mode.",
            "Complete pre-job safety checks and permit requirements.",
            "Execute the procedure step-by-step without bypassing interlocks.",
            "Validate operating parameters after completion.",
            "Document readings, exceptions, and follow-up actions.",
        ]

    def _safety_checks(self, intent: str, asset: Optional[Asset], incidents: List[Incident]) -> List[str]:
        checks = [
            "Confirm permit-to-work and authorization are in place.",
            "Verify PPE, area barricading, and communication with control room.",
            "Confirm all guards, covers, and emergency stops are functional.",
        ]
        if asset and (asset.vibration or 0) > 7:
            checks.append("High vibration history: verify bearing/coupling condition before procedure execution.")
        if incidents and any("valve" in (incident.root_cause or "").lower() for incident in incidents[:4]):
            checks.append("Valve-related failure history: independently verify valve positions before startup/shutdown.")
        if intent == "startup_procedure":
            checks.append("Do not start unless suction path, seal flush, lubrication, and cooling are proven available.")
        if intent == "shutdown_procedure":
            checks.append("Confirm downstream process impact and depressurization/isolation plan before stopping.")
        return checks

    def _estimated_duration(self, intent: str) -> str:
        if intent == "startup_procedure":
            return "20-30 minutes including pre-start checks"
        if intent == "shutdown_procedure":
            return "15-25 minutes including isolation checks"
        return "Depends on site SOP scope"

    def _prerequisites(self, intent: str, asset_name: str) -> List[str]:
        common = [
            f"Confirm the asset tag and operating mode for {asset_name}.",
            "Approved work permit or operating instruction is available.",
            "Control room and field operator communication is established.",
        ]
        if intent == "startup_procedure":
            common.extend([
                "Suction/discharge line-up is verified.",
                "Lubrication, seal flush, cooling, and electrical supply are available.",
            ])
        elif intent == "shutdown_procedure":
            common.extend([
                "Downstream process impact is approved.",
                "Isolation and depressurization plan is available.",
            ])
        return common

    def _procedure_warnings(self, intent: str, incidents: List[Incident], risk: str) -> List[str]:
        warnings = []
        if risk in {"Critical", "High"}:
            warnings.append(f"{risk} asset risk: execute only with supervisor awareness and enhanced monitoring.")
        if any("valve" in (incident.root_cause or "").lower() for incident in incidents[:5]):
            warnings.append("Previous valve-position issue found; independently verify valve positions.")
        if intent == "startup_procedure":
            warnings.append("Do not start if suction pressure, seal flush, or lubrication is outside limits.")
        elif intent == "shutdown_procedure":
            warnings.append("Avoid abrupt shutdown unless emergency conditions require it.")
        return warnings

    def _ensure_connected_documents_indexed(self, db: Session, asset_tag: Optional[str], graph_terms: List[str]) -> None:
        if not asset_tag:
            return
        candidates = set(graph_terms)
        candidates.update([f"Manual_{asset_tag}.pdf", "maintenance_logs.csv"])
        for term in list(candidates)[:20]:
            if not str(term).lower().endswith((".pdf", ".csv")):
                continue
            doc = db.query(Document).filter(Document.title == term).first()
            if doc and not db.query(PageIndex).filter(PageIndex.document_id == doc.id).first():
                page_index_service.index_document_from_source(db, doc.id)

    def _find_pages(self, db: Session, asset_tag: Optional[str], terms: List[str], doc_types: List[str], procedure_type: Optional[str] = None) -> List[PageIndex]:
        pages = db.query(PageIndex).order_by(PageIndex.document_name, PageIndex.page_number).limit(500).all()
        if procedure_type:
            pages = [page for page in pages if self._page_matches_procedure_type(page, procedure_type)]
        doc_type_terms = [term.lower() for term in doc_types]
        search_terms = [term.lower() for term in terms]
        matched = []
        for page in pages:
            haystack = " ".join([
                page.document_name or "",
                page.section_title or "",
                page.keywords or "",
                page.summary or "",
                page.extracted_text or "",
            ]).lower()
            asset_match = not asset_tag or asset_tag.lower() in haystack or not page.equipment_ids
            procedure_specific = any(term in search_terms for term in ["startup", "start-up", "start up", "shutdown", "shut down"])
            if procedure_specific:
                strict_terms = [term for term in search_terms if term in {"startup", "start-up", "start up", "shutdown", "shut down"}]
                term_match = any(term in haystack for term in strict_terms)
            else:
                term_match = any(term in haystack for term in doc_type_terms + search_terms)
            if asset_match and term_match:
                matched.append(page)
        return matched[:4]

    def _fallback_document_pages(
        self,
        db: Session,
        doc_type: str,
        asset_tag: Optional[str],
        preferred_terms: Optional[List[str]] = None,
        procedure_type: Optional[str] = None,
    ) -> List[PageIndex]:
        q = db.query(Document).filter(Document.type == doc_type)
        docs = q.all()
        preferred_terms = [term.lower() for term in preferred_terms or []]
        if procedure_type:
            docs = [doc for doc in docs if self._document_matches_procedure_type(doc, procedure_type)]
        if asset_tag:
            preferred = [
                doc for doc in docs
                if asset_tag.lower() in (doc.title or "").lower() or asset_tag.lower() in (doc.equipment_tags or "").lower()
            ]
            docs = preferred or docs
        if preferred_terms:
            scored_docs = []
            for doc in docs:
                title = (doc.title or "").lower()
                score = sum(1 for term in preferred_terms if term in title)
                scored_docs.append((score, doc))
            scored_docs.sort(key=lambda item: (-item[0], item[1].title or ""))
            docs = [doc for _, doc in scored_docs]
        for doc in docs[:3]:
            page = db.query(PageIndex).filter(PageIndex.document_id == doc.id).order_by(PageIndex.page_number).first()
            if not page:
                page_index_service.index_document_from_source(db, doc.id)
                page = db.query(PageIndex).filter(PageIndex.document_id == doc.id).order_by(PageIndex.page_number).first()
            if page and (not procedure_type or self._page_matches_procedure_type(page, procedure_type)):
                return [page]
        return []

    def _page_matches_procedure_type(self, page: PageIndex, procedure_type: str) -> bool:
        return page_index_service.page_matches_procedure_type(page, procedure_type)

    def _document_matches_procedure_type(self, doc: Document, procedure_type: str) -> bool:
        return infer_procedure_type(document_name=doc.title or "") == procedure_type

    def _expert_notes(self, db: Session, asset_tag: Optional[str], query: str) -> List[ExpertKnowledge]:
        if not asset_tag:
            return []
        terms = [asset_tag, asset_tag.replace("-", ""), query[:40]]
        filters = [ExpertKnowledge.condition.ilike(f"%{term}%") for term in terms if term]
        return db.query(ExpertKnowledge).filter(or_(*filters)).limit(5).all() if filters else []

    def _build_evidence(
        self,
        pages: List[PageIndex],
        manual_pages: List[PageIndex],
        sop_pages: List[PageIndex],
        inspection_pages: List[PageIndex],
        compliance_pages: List[PageIndex],
        incidents: List[Incident],
        expert_notes: List[ExpertKnowledge],
        asset: Optional[Asset],
    ) -> List[Dict[str, Any]]:
        evidence = []
        for page in list(dict.fromkeys(pages + manual_pages + sop_pages + inspection_pages + compliance_pages))[:14]:
            evidence.append(_page_to_evidence(page, 82))
        for incident in incidents[:6]:
            evidence.append({
                "document_name": "maintenance_logs.csv",
                "page_number": incident.id,
                "section": incident.title,
                "page_index_id": self._page_id_for_incident(incident),
                "incident_id": f"INC-{incident.id}",
                "maintenance_id": f"ML-{1000 + incident.id}",
                "inspection_id": "",
                "confidence": 90,
                "excerpt": f"{incident.asset_tag}: {incident.description} Root cause: {incident.root_cause}",
            })
        if asset:
            evidence.append({
                "document_name": "sensor_data/sensor_readings.csv",
                "page_number": "",
                "section": "Latest sensor snapshot",
                "page_index_id": None,
                "incident_id": "",
                "maintenance_id": "",
                "inspection_id": "",
                "confidence": 76,
                "excerpt": f"Temperature {asset.temperature}, vibration {asset.vibration}, current {asset.power_draw}, status {asset.status}.",
            })
        for note in expert_notes[:3]:
            evidence.append({
                "document_name": "expert_knowledge.txt",
                "page_number": "",
                "section": "Expert note",
                "page_index_id": None,
                "incident_id": "",
                "maintenance_id": "",
                "inspection_id": "",
                "confidence": 72,
                "excerpt": note.condition,
            })
        return evidence

    def _page_id_for_incident(self, incident: Incident) -> Optional[int]:
        return None

    def _department(self, asset: Optional[Asset]) -> str:
        if not asset:
            return "Unknown"
        if "Utilities" in (asset.location or ""):
            return "Utilities"
        return asset.location or "Operations"

    def _summary(self, asset: Optional[Asset], incident: Optional[Incident], root_cause: str, risk: str) -> str:
        asset_name = asset.name if asset else "The asset"
        if incident:
            return f"{asset_name} risk is {risk}; latest connected event points to {root_cause}."
        return f"{asset_name} has {risk} risk based on available graph, page-index, and sensor evidence."

    def _manual_recommendation(self, manual_pages: List[PageIndex], sop_pages: List[PageIndex], incident: Optional[Incident]) -> str:
        if sop_pages:
            return self._safe_page_summary(sop_pages[0], "Follow the identified SOP for safe isolation, inspection, and restart.")
        if manual_pages:
            return self._safe_page_summary(manual_pages[0], "Follow OEM troubleshooting and preventive maintenance instructions.")
        if incident:
            return incident.corrective_action or "Review the applicable manual/SOP before restart."
        return "No direct manual recommendation found; index the OEM manual for detailed procedure."

    def _safe_page_summary(self, page: PageIndex, fallback: str) -> str:
        summary = page.summary or ""
        if not summary or _contains_internal_status(summary):
            return fallback
        return summary

    def _document_name(self, manual_pages: List[PageIndex], sop_pages: List[PageIndex]) -> str:
        page = (sop_pages or manual_pages or [None])[0]
        return page.document_name if page else "Not indexed"

    def _page_number(self, manual_pages: List[PageIndex], sop_pages: List[PageIndex]) -> Any:
        page = (sop_pages or manual_pages or [None])[0]
        return page.page_number if page else "N/A"

    def _section(self, manual_pages: List[PageIndex], sop_pages: List[PageIndex]) -> str:
        page = (sop_pages or manual_pages or [None])[0]
        return page.section_title if page else "N/A"

    def _rul(self, asset: Optional[Asset], incidents: List[Incident], probability: int) -> str:
        if probability >= 70:
            return "Less than 30 operating days without intervention"
        if probability >= 45:
            return "30-90 operating days; verify with condition monitoring"
        if incidents:
            return "90+ operating days if corrective actions remain effective"
        return "Unknown; insufficient historical failures"

    def _next_inspection(self, risk: str) -> str:
        if risk in {"Critical", "High"}:
            return (datetime.utcnow() + timedelta(days=7)).date().isoformat()
        if risk == "Medium":
            return (datetime.utcnow() + timedelta(days=30)).date().isoformat()
        return (datetime.utcnow() + timedelta(days=90)).date().isoformat()

    def _immediate_actions(self, incident: Optional[Incident], risk: str) -> List[str]:
        actions = []
        if incident and incident.corrective_action:
            actions.append(incident.corrective_action)
        if risk in {"Critical", "High"}:
            actions.append("Inspect asset before continued operation and verify safe operating envelope.")
        actions.append("Validate current sensor readings against normal operating limits.")
        return actions

    def _preventive_actions(self, asset_tag: Optional[str], incident: Optional[Incident]) -> List[str]:
        actions = [
            "Add condition-based alerts for vibration, temperature, and current trend changes.",
            "Attach indexed manual, SOP, inspection, and compliance evidence to the asset graph.",
        ]
        if incident and "valve" in (incident.root_cause or "").lower():
            actions.insert(0, "Add valve position verification after maintenance and before restart.")
        if asset_tag:
            actions.append(f"Create a recurring inspection checklist for {asset_tag}.")
        return actions

    def _sources_covered(self, evidence: List[Dict[str, Any]], asset: Optional[Asset], expert_notes: List[ExpertKnowledge]) -> Dict[str, bool]:
        names = " ".join(str(item.get("document_name", "")).lower() for item in evidence)
        sections = " ".join(str(item.get("section", "")).lower() for item in evidence)
        return {
            "equipment_manual": "manual" in names,
            "maintenance_logs": "maintenance_logs" in names,
            "incident_reports": any(item.get("incident_id") for item in evidence),
            "inspection_reports": any(item.get("inspection_id") for item in evidence) or "ins" in names or "inspection" in names,
            "sensor_data": asset is not None,
            "sop_documents": "sop" in names,
            "compliance_documents": self._is_compliance_text(names + " " + sections),
            "expert_notes": bool(expert_notes),
        }

    # ── SOP Agent helpers ────────────────────────────────────────────────────

    def _extract_applicable_equipment(self, page: Optional[PageIndex], asset_tag: Optional[str]) -> List[str]:
        """Return all equipment IDs found in the SOP page. Supports multi-asset SOPs."""
        found: set = set()
        if page:
            sources = " ".join([
                page.equipment_ids or "",
                page.keywords or "",
                page.extracted_text or "",
                page.document_name or "",
                page.section_title or "",
            ])
            found.update(extract_equipment_ids(sources))
        if asset_tag:
            found.add(asset_tag.upper().replace("-", ""))
        if not found:
            return [asset_tag] if asset_tag else []
        type_map = {
            "UPS": "Power Backup", "WT": "Water Treatment Unit", "BW": "Bottle Washing Machine",
            "FM": "Bottle Filling Machine", "CM": "Bottle Capping Machine", "LB": "Labeling Machine",
            "CV": "Conveyor Belt", "AC": "Air Compressor", "BL": "Boiler", "CH": "Chiller",
            "DG": "Diesel Generator", "CP": "Control Panel", "TK": "Water Storage Tank",
            "M": "Mixing Tank", "P": "Water Transfer Pump",
        }
        result = []
        for eq_id in sorted(found):
            prefix = next((p for p in sorted(type_map, key=len, reverse=True) if eq_id.startswith(p)), None)
            label = f"{type_map[prefix]} {eq_id}" if prefix else eq_id
            result.append(label)
        return result

    def _required_ppe(self, intent: str, page: Optional[PageIndex]) -> List[str]:
        """Infer required PPE from page text; fall back to intent-based defaults."""
        PPE_MAP = {
            "helmet": "Safety Helmet",
            "hard hat": "Hard Hat",
            "glove": "Chemical-Resistant Gloves",
            "goggle": "Safety Goggles",
            "face shield": "Face Shield",
            "safety shoe": "Safety Shoes / Steel-Toe Boots",
            "coverall": "Flame-Resistant Coverall",
            "scba": "SCBA (Self-Contained Breathing Apparatus)",
            "ear": "Ear Protection",
            "harness": "Fall Arrest Harness",
            "respirator": "Respirator",
        }
        found: List[str] = []
        if page and page.extracted_text:
            text_lower = page.extracted_text.lower()
            for keyword, label in PPE_MAP.items():
                if keyword in text_lower and label not in found:
                    found.append(label)
        if found:
            return found
        base = ["Safety Helmet", "Chemical-Resistant Gloves", "Safety Shoes / Steel-Toe Boots", "Safety Goggles"]
        if intent == "startup_procedure":
            base.append("Flame-Resistant Coverall")
        elif intent == "shutdown_procedure":
            base.extend(["Flame-Resistant Coverall", "Face Shield"])
        return base

    def _completion_criteria(self, intent: str, page: Optional[PageIndex]) -> List[str]:
        """Extract or generate post-completion verifiable criteria."""
        CRITERIA_PATTERNS = [
            r"(?:verify|confirm)[^.\n]{8,80}\.",
            r"reading[^.\n]{0,60}within[^.\n]{0,60}\.",
            r"no leak[^.\n]{0,60}\.",
            r"normal operating[^.\n]{0,60}\.",
            r"pressure[^.\n]{0,60}stable[^.\n]{0,60}\.",
        ]
        found: List[str] = []
        if page and page.extracted_text:
            for pattern in CRITERIA_PATTERNS:
                for m in re.findall(pattern, page.extracted_text.lower())[:2]:
                    criterion = m.strip().capitalize()
                    if criterion and criterion not in found:
                        found.append(criterion)
        if found:
            return found[:5]
        if intent == "startup_procedure":
            return [
                "Flow rate and discharge pressure are within normal operating range.",
                "Motor current draw is within nameplate amperage.",
                "No abnormal vibration, noise, or heat detected at bearings/couplings.",
                "Seal flush and lube oil systems are functioning normally.",
                "Control room confirms stable process conditions after startup.",
            ]
        if intent == "shutdown_procedure":
            return [
                "Asset is confirmed at standstill and process flow has ceased.",
                "All isolation valves are in the correct closed/locked position.",
                "LOTO applied if maintenance or inspection follows.",
                "No residual pressure confirmed at vent and drain points.",
                "Control room notified of successful shutdown.",
            ]
        return [
            "Procedure steps completed without bypassing any interlocks.",
            "All operating parameters recorded in the operations log.",
            "Control room acknowledgment received and documented.",
        ]

    def _build_sop_evidence(
        self,
        pages: List[PageIndex],
        manual_pages: List[PageIndex],
        sop_pages: List[PageIndex],
    ) -> List[Dict[str, Any]]:
        """Build evidence list for SOP intents — only SOP/manual pages, no incidents/sensors/expert notes."""
        evidence: List[Dict[str, Any]] = []
        seen: set = set()
        for page in list(dict.fromkeys(sop_pages + manual_pages + pages))[:10]:
            if page.id in seen:
                continue
            seen.add(page.id)
            evidence.append(_page_to_evidence(page, 84))
        return evidence

    def _sop_purpose(self, intent: str, page: Optional[PageIndex], asset_name: str) -> str:
        """Return a clean one-line purpose statement for the SOP."""
        if page:
            summary = page.summary or ""
            if summary and not _contains_internal_status(summary) and len(summary) > 20:
                return summary
            if page.section_title and not _contains_internal_status(page.section_title):
                verb = "startup" if intent == "startup_procedure" else "shutdown" if intent == "shutdown_procedure" else "operation"
                return f"This procedure defines the safe {verb} sequence for {asset_name} as documented in {page.document_name}."
        if intent == "startup_procedure":
            return (
                f"This SOP defines the pre-start checks and safe startup sequence for {asset_name} "
                "to ensure correct commissioning and protection of equipment and personnel."
            )
        if intent == "shutdown_procedure":
            return (
                f"This SOP defines the controlled shutdown and safe isolation procedure for {asset_name} "
                "to protect equipment and prepare for maintenance or standby."
            )
        return f"This standard operating procedure provides step-by-step instructions for safe operation of {asset_name}."

    def _content_status(self, page: Optional[PageIndex], procedure_confidence: int) -> str:
        """Return 'complete', 'partial', or 'not_found' — never exposes parser/OCR/embedding terms."""
        if not page:
            return "not_found"
        text = page.extracted_text or ""
        summary = page.summary or ""
        if _contains_internal_status(text) or _contains_internal_status(summary):
            return "partial"
        if len(text.strip()) < 80:
            return "partial"
        if procedure_confidence >= 65:
            return "complete"
        return "partial"

    # ── Compliance helpers ────────────────────────────────────────────────────

    def _is_compliance_document(self, document_name: str) -> bool:
        return self._is_compliance_text(document_name or "")

    def _is_compliance_text(self, value: str) -> bool:
        lowered = value.lower()
        return any(term in lowered for term in ["compliance", "factory", "iso", "permit", "risk_assessment", "safety_audit", "qms"])


enterprise_assistant = EnterpriseAssistantService()
