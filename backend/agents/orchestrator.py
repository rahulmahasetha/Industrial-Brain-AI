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
    "RCA": 0.95,
    "Inspection": 0.90,
    "Sensor Data": 0.90,
    "Expert Notes": 0.85,
    "Maintenance Logs": 0.80,
    "Equipment Manual": 0.70,
    "SOP": 0.65,
    "Compliance": 0.60,
    # Fallback aliases
    "Manual": 0.70,
    "Maintenance": 0.80,
    "Incident": 1.00,
}

class RetrievalPlanner:
    """Deterministic rules engine mapping intents to retrieval strategies and response templates."""
    
    PLAN_CONFIG = {
        "Manual": {
            "agent": "Manual Agent",
            "retrieve": ["Equipment Manual", "Manual"],
            "fallback_retrieve": ["SOP", "Expert Notes"],
            "do_not_retrieve": ["Incident Report", "Inspection", "Compliance", "RCA", "Sensor Data", "Maintenance Logs", "Maintenance"],
            "response_template": ["Executive Summary", "Source Document", "Prerequisites", "Checklist", "Step-by-Step Procedure", "Safety Warnings", "Related Documents", "Related Questions"]
        },
        "SOP": {
            "agent": "SOP Agent",
            "retrieve": ["SOP", "Equipment Manual", "Manual"],
            "fallback_retrieve": [],
            "do_not_retrieve": ["Incident Report", "Inspection", "Compliance", "RCA", "Sensor Data", "Maintenance Logs", "Maintenance", "Expert Notes"],
            "response_template": ["Executive Summary", "Source Document", "Prerequisites", "Checklist", "Step-by-Step Procedure", "Safety Warnings", "Related Documents", "Related Questions"]
        },
        "Incident": {
            "agent": "Incident Agent",
            "retrieve": ["Incident Report", "Incident"],
            "fallback_retrieve": ["Maintenance Logs", "Maintenance", "Inspection", "RCA", "Sensor Data"],
            "do_not_retrieve": ["Equipment Manual", "Manual", "Compliance", "SOP"],
            "response_template": ["Executive Summary", "Incident Overview", "Incident Details (Table)", "Root Cause", "Corrective Actions", "Preventive Actions", "Current Status", "Related Incidents", "Source Documents", "Related Questions"]
        },
        "Maintenance": {
            "agent": "Maintenance Agent",
            "retrieve": ["Maintenance Logs", "Maintenance", "Completed Work Orders", "Technician Notes"],
            "fallback_retrieve": ["Incident Report", "Incident", "Inspection", "Expert Notes"],
            "do_not_retrieve": ["Equipment Manual", "Manual", "SOP", "Compliance"],
            "response_template": ["Executive Summary", "Maintenance Timeline", "Recent Activities", "Pending Work", "Recommendations", "Source Documents", "Related Questions"]
        },
        "Inspection": {
            "agent": "Inspection Agent",
            "retrieve": ["Inspection Reports", "Inspection"],
            "fallback_retrieve": ["Maintenance Logs", "Maintenance", "Incident Report", "Incident", "Compliance"],
            "do_not_retrieve": ["SOP", "Equipment Manual", "Manual"],
            "response_template": ["Executive Summary", "Inspection Findings", "Observations", "Risk Level", "Recommendations", "Source Documents", "Related Questions"]
        },
        "RCA": {
            "agent": "RCA Agent",
            "retrieve": ["RCA Reports", "RCA", "Incident Report", "Incident", "Inspection Reports", "Inspection", "Maintenance Logs", "Maintenance"],
            "fallback_retrieve": ["Expert Notes", "Sensor Data"],
            "do_not_retrieve": ["Compliance", "SOP", "Equipment Manual", "Manual"],
            "response_template": ["Executive Summary", "Most Probable Root Cause", "Evidence", "Historical Timeline", "Corrective Actions", "Preventive Actions", "Recommendations", "Source Documents", "Related Questions"]
        },
        "Predictive": {
            "agent": "Predictive Agent",
            "retrieve": ["Prediction", "Sensor Data", "Maintenance Logs", "Maintenance", "Expert Notes"],
            "fallback_retrieve": [],
            "do_not_retrieve": ["SOP", "Equipment Manual", "Manual", "Compliance", "Incident Report", "Incident", "Inspection", "RCA"],
            "response_template": ["Executive Summary", "Asset Health", "Risk Level", "Failure Probability", "Remaining Useful Life (RUL)", "Supporting Evidence", "Recommendations", "Source Documents", "Related Questions"]
        },
        "Compliance": {
            "agent": "Compliance Agent",
            "retrieve": ["Compliance Documents", "Compliance", "Audit Reports"],
            "fallback_retrieve": ["Inspection Reports", "Inspection", "Maintenance Logs", "Maintenance"],
            "do_not_retrieve": ["Sensor Data", "RCA", "Expert Notes"],
            "response_template": ["Executive Summary", "Compliance Status", "Findings", "Gaps", "Required Actions", "Related Standards", "Source Documents", "Related Questions"]
        },
        "Expert Knowledge": {
            "agent": "Expert Knowledge Agent",
            "retrieve": ["Expert Notes"],
            "fallback_retrieve": ["Maintenance Logs", "Maintenance", "Incident Report", "Incident"],
            "do_not_retrieve": ["Compliance"],
            "response_template": ["Executive Summary", "Most Probable Root Cause", "Evidence", "Historical Similar Failures", "Corrective Actions", "Preventive Actions", "Source Documents"]
        },
        "Asset Overview": {
            "agent": "Asset Overview Agent",
            "retrieve": ["Everything"],
            "fallback_retrieve": ["Everything"],
            "do_not_retrieve": [],
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
        
        # Rule-based regex/keyword routing
        if any(w in lower for w in ["incident", "breakdown", "failure report"]):
            intent = "Incident"
        elif any(w in lower for w in ["sop", "startup", "shutdown", "procedure"]):
            intent = "SOP"
        elif any(w in lower for w in ["manual", "guide", "troubleshooting", "troubleshoot"]):
            intent = "Manual"
        elif any(w in lower for w in ["why", "root cause", "cause", "stopped"]):
            intent = "RCA"
        elif any(w in lower for w in ["predictive", "predict", "risk", "rul", "health"]):
            intent = "Predictive"
        elif any(w in lower for w in ["maintenance", "service", "history"]):
            intent = "Maintenance"
        elif any(w in lower for w in ["inspection", "inspect", "audit"]):
            intent = "Inspection"
        elif any(w in lower for w in ["compliance", "iso", "fssai"]):
            intent = "Compliance"
        elif any(w in lower for w in ["full details", "overview"]):
            intent = "Asset Overview"
            
        return RetrievalPlanner.get_plan(intent)

orchestrator_agent = OrchestratorAgent()
