import json
import os
import re
from typing import Dict, Any, List
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Global Document Priority Weights (as specified by user)
DOCUMENT_PRIORITY_WEIGHTS = {
    "Incident Report": 1.00,
    "RCA Report": 0.95,
    "RCA": 0.95,
    "Inspection Report": 0.90,
    "Inspection": 0.90,
    "Sensor Data": 0.90,
    "QA Record": 0.90,
    "QA": 0.90,
    "Expert Notes": 0.85,
    "Maintenance Log": 0.80,
    "Maintenance": 0.80,
    "Equipment Manual": 0.70,
    "Manual": 0.70,
    "SOP": 0.65,
    "Compliance Certificate": 0.60,
    "Compliance": 0.60,
    "Audit Report": 0.60,
    "Checklist": 0.50,
    "Asset Specification": 0.50,
}

class RetrievalPlanner:
    """Deterministic rules engine mapping intents to retrieval strategies and response templates."""
    
    PLAN_CONFIG = {
        "Manual": {
            "agent": "Manual Agent",
            "retrieve": ["Equipment Manual", "Manual", "Asset Specification"],
            "fallback_retrieve": ["SOP", "Expert Notes"],
            "do_not_retrieve": ["Maintenance Log", "Incident Report", "Inspection Report", "Compliance Certificate", "Audit Report", "QA Record", "RCA Report", "Sensor Data"],
            "cross_document": False,
            "response_template": ["Primary Answer", "Relevant Procedure", "Related SOP", "Document", "Page Number", "Section", "Estimated Duration", "Prerequisites", "Warnings", "Step By Step Instructions"]
        },
        "SOP": {
            "agent": "SOP Agent",
            "retrieve": ["SOP", "Checklist", "Equipment Manual", "Manual"],
            "fallback_retrieve": [],
            "do_not_retrieve": ["Incident Report", "Inspection Report", "Compliance Certificate", "Audit Report", "RCA Report", "Sensor Data", "Maintenance Log", "QA Record", "Expert Notes"],
            "cross_document": False,
            "response_template": ["Primary Answer", "Relevant Procedure", "Related SOP", "Document", "Page Number", "Section", "Estimated Duration", "Prerequisites", "Warnings", "Step By Step Instructions"]
        },
        "Incident Report": {
            "agent": "Incident Agent",
            "retrieve": ["Incident Report", "Incident"],
            "fallback_retrieve": ["Maintenance Log", "Inspection Report", "RCA Report", "Sensor Data", "QA Record"],
            "do_not_retrieve": ["Equipment Manual", "Manual", "Compliance Certificate", "Audit Report", "SOP", "Checklist", "Asset Specification"],
            "cross_document": False,
            "response_template": ["Executive Summary", "Incident Overview", "Incident Details (Table)", "Root Cause", "Corrective Actions", "Preventive Actions", "Current Status", "Related Incidents", "Source Documents", "Related Questions"]
        },
        "Maintenance Log": {
            "agent": "Maintenance Agent",
            "retrieve": ["Maintenance Log", "Maintenance", "Completed Work Orders", "Technician Notes"],
            "fallback_retrieve": [],
            "do_not_retrieve": ["Equipment Manual", "Manual", "SOP", "Compliance Certificate", "Audit Report", "QA Record", "RCA Report", "Checklist", "Asset Specification", "Incident Report", "Inspection Report", "Expert Notes"],
            "cross_document": False,
            "response_template": ["Executive Summary", "Maintenance Timeline", "Recent Activities", "Pending Work", "Recommendations", "Source Documents", "Related Questions"]
        },
        "Inspection Report": {
            "agent": "Inspection Agent",
            "retrieve": ["Inspection Report", "Inspection", "Checklist"],
            "fallback_retrieve": [],
            "do_not_retrieve": ["SOP", "Equipment Manual", "Manual", "RCA Report", "Asset Specification", "Incident Report", "Maintenance Log", "Compliance Certificate", "Audit Report", "QA Record", "Expert Notes"],
            "cross_document": False,
            "response_template": ["Executive Summary", "Inspection Findings", "Observations", "Risk Level", "Recommendations", "Source Documents", "Related Questions"]
        },
        "RCA Report": {
            "agent": "RCA Agent",
            "retrieve": ["RCA Report", "RCA"],
            "fallback_retrieve": ["Incident Report", "Inspection Report", "Maintenance Log", "Expert Notes", "Sensor Data", "QA Record"],
            "do_not_retrieve": ["Compliance Certificate", "Audit Report", "SOP", "Equipment Manual", "Manual", "Checklist", "Asset Specification"],
            "cross_document": False,
            "response_template": ["Executive Summary", "Most Probable Root Cause", "Evidence", "Historical Timeline", "Corrective Actions", "Preventive Actions", "Recommendations", "Source Documents", "Related Questions"]
        },
        "QA Record": {
            "agent": "QA Agent",
            "retrieve": ["QA Record", "QA"],
            "fallback_retrieve": [],
            "do_not_retrieve": ["Equipment Manual", "Manual", "SOP", "Checklist", "Asset Specification", "RCA Report", "Sensor Data", "Incident Report", "Inspection Report", "Maintenance Log", "Compliance Certificate", "Audit Report", "Expert Notes"],
            "cross_document": False,
            "response_template": ["Executive Summary", "Quality Metrics", "Findings", "Deviations", "Recommendations", "Source Documents", "Related Questions"]
        },
        "Predictive": {
            "agent": "Predictive Agent",
            "retrieve": ["Prediction", "Sensor Data", "Maintenance Log", "Expert Notes"],
            "fallback_retrieve": [],
            "do_not_retrieve": ["SOP", "Equipment Manual", "Manual", "Compliance Certificate", "Audit Report", "Incident Report", "Inspection Report", "QA Record", "RCA Report", "Checklist"],
            "cross_document": True,
            "response_template": ["Executive Summary", "Asset Health", "Risk Level", "Failure Probability", "Remaining Useful Life (RUL)", "Supporting Evidence", "Recommendations", "Source Documents", "Related Questions"]
        },
        "Compliance Certificate": {
            "agent": "Compliance Agent",
            "retrieve": ["Compliance Certificate", "Compliance", "Audit Report"],
            "fallback_retrieve": [],
            "do_not_retrieve": ["Sensor Data", "RCA Report", "Expert Notes", "Incident Report", "Manual", "Equipment Manual", "SOP", "Checklist", "QA Record", "Maintenance Log", "Inspection Report"],
            "cross_document": False,
            "response_template": ["Executive Summary", "Compliance Status", "Findings", "Gaps", "Required Actions", "Related Standards", "Source Documents", "Related Questions"]
        },
        "Expert Knowledge": {
            "agent": "Expert Knowledge Agent",
            "retrieve": ["Expert Notes"],
            "fallback_retrieve": ["Maintenance Log", "Incident Report"],
            "do_not_retrieve": ["Compliance Certificate", "Audit Report", "QA Record", "Inspection Report", "RCA Report"],
            "cross_document": False,
            "response_template": ["Executive Summary", "Most Probable Root Cause", "Evidence", "Historical Similar Failures", "Corrective Actions", "Preventive Actions", "Source Documents"]
        },
        "Asset Overview": {
            "agent": "Asset Overview Agent",
            "retrieve": ["Everything"],
            "fallback_retrieve": ["Everything"],
            "do_not_retrieve": [],
            "cross_document": True,
            "response_template": ["Executive Summary", "Asset Information", "Current Status", "Health", "Active Issues", "Maintenance Summary", "Incident Summary", "Inspection Summary", "Predictive Summary", "Related Documents", "Related Questions"]
        },
    }

    @classmethod
    def get_plan(cls, intent: str) -> Dict[str, Any]:
        intent_key = intent
        if intent_key not in cls.PLAN_CONFIG:
            intent_key = "Asset Overview"
            
        config = cls.PLAN_CONFIG[intent_key]
        return {
            "intent": intent,
            "agent": config["agent"],
            "allowed_doc_types": config["retrieve"],
            "fallback_doc_types": config.get("fallback_retrieve", []),
            "disallowed_doc_types": config["do_not_retrieve"],
            "cross_document": config.get("cross_document", False),
            "doc_priority_weights": DOCUMENT_PRIORITY_WEIGHTS,
            "response_template": config["response_template"]
        }


class OrchestratorAgent:
    """Uses LLM to classify user intent and generate an orchestration plan."""
    
    def __init__(self):
        self.has_api_key = bool(os.environ.get("GOOGLE_API_KEY"))
        if self.has_api_key:
            from langchain_google_genai import ChatGoogleGenerativeAI
            model_name = os.environ.get("GOOGLE_MODEL", "gemini-2.5-flash")
            self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.0)
        else:
            self.llm = None

    def classify_intent(self, query: str) -> Dict[str, Any]:
        """Classify user query and return full retrieval plan using rule-based keywords."""
        
        lower = query.lower()
        intent = "Asset Overview"
        
        # Rule-based regex/keyword routing (strict priorities)
        # IMPORTANT: More specific multi-word phrases MUST come before single-word matches.
        if any(w in lower for w in ["qa record", "qa report", "quality record", "quality"]):
            intent = "QA Record"
        elif any(w in lower for w in ["rca report", "why", "root cause", "cause", "stopped", "rca"]):
            intent = "RCA Report"
        elif any(w in lower for w in ["compliance certificate", "compliance record", "compliance", "iso", "fssai", "audit report", "audit"]):
            intent = "Compliance Certificate"
        elif any(w in lower for w in ["incident report", "incident", "breakdown", "failure report"]):
            intent = "Incident Report"
        elif any(w in lower for w in ["inspection report", "inspection", "inspect"]):
            intent = "Inspection Report"
        elif any(w in lower for w in [
            "maintenance schedule", "pm schedule", "preventive maintenance",
            "lubrication schedule", "calibration schedule",
            "manual", "guide", "troubleshooting", "troubleshoot", "asset specification",
        ]):
            # PM schedules, calibration schedules, and lubrication schedules live in equipment manuals
            intent = "Manual"
        elif any(w in lower for w in ["maintenance log", "maintenance", "service", "history"]):
            intent = "Maintenance Log"
        elif any(w in lower for w in ["sop", "startup", "shutdown", "procedure", "checklist"]):
            intent = "SOP"
        elif any(w in lower for w in ["predictive", "predict", "risk", "rul", "health"]):
            intent = "Predictive"
        elif any(w in lower for w in ["full details", "overview"]):
            intent = "Asset Overview"
            
        return RetrievalPlanner.get_plan(intent)

orchestrator_agent = OrchestratorAgent()

