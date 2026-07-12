"""
Intent-Based Retrieval Planner

Detects user intent and plans retrieval strategy with:
- Document type prioritization
- Evidence classification
- Root cause filtering
- Evidence ranking by weight
"""

import re
from typing import List, Dict, Any, Tuple
from enum import Enum


class Intent(Enum):
    """Supported user intents for retrieval planning"""
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"
    REASONING_ANALYSIS = "reasoning_analysis"
    PREDICTIVE_MAINTENANCE = "predictive_maintenance"
    MANUAL_LOOKUP = "manual_lookup"
    INCIDENT_LOOKUP = "incident_lookup"
    MAINTENANCE_HISTORY = "maintenance_history"
    COMPLIANCE = "compliance"
    GENERAL_QUERY = "general_query"


class EvidenceType(Enum):
    """Classification of evidence types"""
    FAILURE_EVENT = "failure_event"
    INCIDENT_REPORT = "incident_report"
    SENSOR_ALERT = "sensor_alert"
    EXPERT_OBSERVATION = "expert_observation"
    INSPECTION_FINDING = "inspection_finding"
    MAINTENANCE_EVENT = "maintenance_event"
    MANUAL_RECOMMENDATION = "manual_recommendation"


class EvidenceWeight(Dict[str, float]):
    """Weight/confidence scores for different evidence types"""
    WEIGHTS = {
        EvidenceType.INCIDENT_REPORT.value: 1.0,
        EvidenceType.SENSOR_ALERT.value: 0.90,
        EvidenceType.EXPERT_OBSERVATION.value: 0.85,
        EvidenceType.INSPECTION_FINDING.value: 0.75,
        EvidenceType.MAINTENANCE_EVENT.value: 0.55,
        EvidenceType.MANUAL_RECOMMENDATION.value: 0.40,
    }


class IntentDetector:
    """Detects user intent from query text"""
    
    # RCA keywords
    RCA_KEYWORDS = {
        "root cause", "breakdown", "stopped",
        "crashed", "malfunction", "failure reason", "cause of",
        "incident", "what went wrong", "error", "fault"
    }

    # Reasoning / Analysis keywords
    REASONING_KEYWORDS = {
        "why", "how", "what if", "what happens if", "impact",
        "failure analysis", "analyze", "explain", "correlate",
        "compare", "difference"
    }
    
    # Predictive Maintenance keywords
    PM_KEYWORDS = {
        "predict", "risk", "failure prediction", "health score",
        "remaining life", "mtbf", "reliability", "upcoming issue",
        "will fail", "chance of failure", "predictive"
    }
    
    # Manual Lookup keywords
    MANUAL_KEYWORDS = {
        "manual", "how to", "procedure", "operation", "guide",
        "troubleshoot", "steps", "instructions", "documentation",
        "specification", "datasheet"
    }
    
    # Incident Lookup keywords
    INCIDENT_KEYWORDS = {
        "incident", "accident", "event", "what happened", "history",
        "past issue", "previous problem", "occurred"
    }
    
    # Maintenance History keywords
    MAINT_KEYWORDS = {
        "maintenance", "service", "maintenance history", "work order",
        "pm schedule", "preventive", "repair", "fixed", "last serviced"
    }
    
    # Compliance keywords
    COMPLIANCE_KEYWORDS = {
        "compliance", "audit", "iso", "standard", "regulation",
        "requirement", "safety", "procedure", "certification"
    }
    
    @staticmethod
    def detect(query: str) -> Intent:
        """Detect the user's intent from the query"""
        query_lower = query.lower()
        
        # Check for each intent type
        if any(kw in query_lower for kw in IntentDetector.REASONING_KEYWORDS):
            return Intent.REASONING_ANALYSIS
            
        if any(kw in query_lower for kw in IntentDetector.RCA_KEYWORDS):
            return Intent.ROOT_CAUSE_ANALYSIS
        
        if any(kw in query_lower for kw in IntentDetector.PM_KEYWORDS):
            return Intent.PREDICTIVE_MAINTENANCE
        
        if any(kw in query_lower for kw in IntentDetector.MANUAL_KEYWORDS):
            return Intent.MANUAL_LOOKUP
        
        if any(kw in query_lower for kw in IntentDetector.INCIDENT_KEYWORDS):
            return Intent.INCIDENT_LOOKUP
        
        if any(kw in query_lower for kw in IntentDetector.MAINT_KEYWORDS):
            return Intent.MAINTENANCE_HISTORY
        
        if any(kw in query_lower for kw in IntentDetector.COMPLIANCE_KEYWORDS):
            return Intent.COMPLIANCE
        
        return Intent.GENERAL_QUERY


class IntentBasedRetrievalPlanner:
    """Plans retrieval strategy based on detected intent"""
    
    # Intent to document type priority mapping
    INTENT_PRIORITIES = {
        Intent.ROOT_CAUSE_ANALYSIS: {
            "primary": ["Incident Report", "RCA Report"],
            "supporting": ["Maintenance Log", "Expert Notes", "Inspection Report"],
            "reference": ["Equipment Manual", "SOP"],
            "exclude": ["Preventive Maintenance", "Annual Overhaul", "Scheduled Calibration"],
        },
        Intent.REASONING_ANALYSIS: {
            "primary": ["Incident Report", "RCA Report", "Equipment Manual", "SOP"],
            "supporting": ["Maintenance Log", "Expert Notes", "Inspection Report", "QA Report", "Compliance Record"],
            "reference": [],
            "exclude": [],
        },
        Intent.PREDICTIVE_MAINTENANCE: {
            "primary": ["Sensor Data", "Health Score", "ML Predictions"],
            "supporting": ["Recent Maintenance", "Expert Notes"],
            "reference": [],
            "exclude": ["SOP Documents", "Compliance"],
        },
        Intent.MANUAL_LOOKUP: {
            "primary": ["Equipment Manual", "Page Index"],
            "supporting": ["SOP", "Troubleshooting Guide"],
            "reference": [],
            "exclude": ["Maintenance History", "Incident Reports"],
        },
        Intent.INCIDENT_LOOKUP: {
            "primary": ["Incident Reports", "RCA Reports"],
            "supporting": ["Inspection Reports", "Related Maintenance"],
            "reference": ["Equipment Manual"],
            "exclude": [],
        },
        Intent.MAINTENANCE_HISTORY: {
            "primary": ["Maintenance Logs", "Work Orders"],
            "supporting": ["Technician Notes"],
            "reference": [],
            "exclude": ["Incidents", "Compliance"],
        },
        Intent.COMPLIANCE: {
            "primary": ["Compliance Documents", "ISO Documents"],
            "supporting": ["Safety Procedures", "Audit Reports"],
            "reference": [],
            "exclude": [],
        },
        Intent.GENERAL_QUERY: {
            "primary": ["Page Index", "Equipment Manual", "Incident Reports"],
            "supporting": ["SOP", "Maintenance Logs", "Expert Notes"],
            "reference": [],
            "exclude": [],
        },
    }
    
    @staticmethod
    def plan_query(query: str, asset_tag: str = "", history: str = "") -> Dict[str, Any]:
        import os
        import json
        import re
        has_api_key = bool(os.environ.get("GOOGLE_API_KEY"))
        has_groq_key = bool(os.environ.get("GROQ_API_KEY"))
        
        if (has_api_key or has_groq_key) and query:
            try:
                primary_llm = None
                fallback_llm = None
                
                if has_groq_key:
                    try:
                        from langchain_groq import ChatGroq
                        primary_llm = ChatGroq(
                            api_key=os.environ.get("GROQ_API_KEY"),
                            model="llama-3.3-70b-versatile"
                        )
                    except Exception as e:
                        print(f"Failed to init Groq planner: {e}")
                    
                if has_api_key:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    gemini_llm = ChatGoogleGenerativeAI(model=os.environ.get("GOOGLE_MODEL", "gemini-2.5-flash"))
                    if not primary_llm:
                        primary_llm = gemini_llm
                    else:
                        fallback_llm = gemini_llm
                        
                if not primary_llm:
                    raise ValueError("No LLM successfully initialized")

                from langchain_core.prompts import PromptTemplate
                from langchain_core.output_parsers import StrOutputParser
                
                prompt = PromptTemplate.from_template(
                    """You are a retrieval planning agent for an industrial knowledge base. Given a user query, determine the optimal retrieval strategy.

USER QUERY: {query}
ASSET CONTEXT: {asset_tag} (may be empty)
CONVERSATION HISTORY: {history}

Available document collections:
- maintenance_logs: Equipment repair history, work orders, technician notes
- incidents: Fault reports, breakdown records, injury reports  
- sops: Standard Operating Procedures, step-by-step work instructions
- manuals: Equipment manuals, technical specifications
- compliance: Audit reports, regulatory certificates, inspection records
- rca: Root cause analysis reports from past failures
- expert_notes: Informal expert knowledge, tribal knowledge notes

Retrieval Strategies:
- EXACT_METADATA: Use when the query contains exact IDs (e.g., ML-1234, INC-007, SOP-01).
- STRUCTURED_SQL: Use when the query asks for filters (e.g., by date, severity, technician name, status).
- KNOWLEDGE_GRAPH: Use when the query explores relationships for an asset.
- VECTOR_SEARCH: Use for natural language questions needing semantic search.

Respond in this exact JSON format:
{{
  "intent": "Manual|SOP|Incident|Inspection|Maintenance|Compliance|Asset|General",
  "retrieval_strategy": "EXACT_METADATA|STRUCTURED_SQL|KNOWLEDGE_GRAPH|VECTOR_SEARCH",
  "primary_collections": ["top 2 collections to search first"],
  "secondary_collections": ["1-2 fallback collections"],
  "search_queries": [
    "reformulated query 1 optimized for search",
    "reformulated query 2 with different keywords"
  ],
  "exact_ids_extracted": ["list of exact IDs if present like ML-1234", "INC-001"],
  "structured_filters": {{"severity": "High", "status": "Closed", "technician": "name", "date_range": "2023"}},
  "asset_filter": "asset tag to filter by, or null",
  "time_filter": "recent|all",
  "reasoning": "Why you chose these collections and strategy"
}}

Only output valid JSON."""
                )
                
                chain = prompt | primary_llm | StrOutputParser()
                try:
                    result = chain.invoke({
                        "query": query,
                        "asset_tag": asset_tag,
                        "history": history
                    })
                except Exception as e:
                    if fallback_llm:
                        chain = prompt | fallback_llm | StrOutputParser()
                        result = chain.invoke({
                            "query": query,
                            "asset_tag": asset_tag,
                            "history": history
                        })
                    else:
                        raise e
                
                match = re.search(r'\{.*\}', result, re.DOTALL)
                if match:
                    return json.loads(match.group())
            except Exception as e:
                print(f"LLM plan_query error: {e}")
                
        # Fallback
        return {
            "intent": "GENERAL",
            "primary_collections": ["manuals", "sops"],
            "secondary_collections": ["expert_notes"],
            "search_queries": [query],
            "asset_filter": asset_tag if asset_tag else None,
            "time_filter": "all",
            "requires_sensor_data": False,
            "reasoning": "Fallback to general search due to missing API key or LLM error."
        }
    
    @staticmethod
    def get_retrieval_strategy(intent: Intent) -> Dict[str, List[str]]:
        """Get the document retrieval priority for a given intent"""
        return IntentBasedRetrievalPlanner.INTENT_PRIORITIES.get(
            intent,
            IntentBasedRetrievalPlanner.INTENT_PRIORITIES[Intent.GENERAL_QUERY]
        )
    
    @staticmethod
    def rank_documents(
        documents: List[Any],
        intent: Intent
    ) -> List[Tuple[Any, float]]:
        """
        Rank documents based on intent priority.
        
        Returns list of tuples (document, score)
        """
        strategy = IntentBasedRetrievalPlanner.get_retrieval_strategy(intent)
        ranked = []
        
        for doc in documents:
            doc_type = doc.metadata.get("type", "") if hasattr(doc, "metadata") else ""
            
            # Check if document is excluded
            if doc_type in strategy.get("exclude", []):
                continue
            
            # Assign score based on priority tier
            if doc_type in strategy.get("primary", []):
                score = 1.0
            elif doc_type in strategy.get("supporting", []):
                score = 0.7
            elif doc_type in strategy.get("reference", []):
                score = 0.4
            else:
                score = 0.2
            
            ranked.append((doc, score))
        
        # Sort by score descending
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked


class EvidenceClassifier:
    """Classifies retrieved documents into evidence types"""
    
    # Keywords to classify evidence types
    FAILURE_KEYWORDS = {
        "failure", "failed", "breakdown", "malfunction", "crashed",
        "jammed", "blocked", "overheating", "overheated", "trip",
        "fault", "error", "broken", "stopped working"
    }
    
    INCIDENT_KEYWORDS = {
        "incident", "accident", "event", "near miss", "safety",
        "injury", "environmental", "quality issue", "contamination"
    }
    
    SENSOR_KEYWORDS = {
        "sensor", "alert", "alarm", "exceeded", "threshold",
        "pressure", "temperature", "vibration", "anomaly"
    }
    
    EXPERT_KEYWORDS = {
        "note", "observation", "expert", "analyst", "assessment",
        "opinion", "recommendation", "insight", "analysis"
    }
    
    INSPECTION_KEYWORDS = {
        "inspection", "check", "visual", "examination", "finding",
        "defect", "wear", "damage", "observation"
    }
    
    MAINTENANCE_KEYWORDS = {
        "maintenance", "pm", "preventive", "scheduled", "routine",
        "calibration", "overhaul", "lubrication", "service",
        "work order", "technician"
    }
    
    @staticmethod
    def classify(document: Any) -> EvidenceType:
        """Classify a document into an evidence type"""
        
        # Extract searchable content
        title = document.metadata.get("title", "") if hasattr(document, "metadata") else ""
        doc_type = document.metadata.get("type", "") if hasattr(document, "metadata") else ""
        content = getattr(document, "page_content", "")
        section = document.metadata.get("section_name", "") if hasattr(document, "metadata") else ""
        
        searchable = f"{title} {doc_type} {section} {content}".lower()
        
        # Check for incident report first (highest priority)
        if "incident" in doc_type.lower() or any(kw in searchable for kw in EvidenceClassifier.INCIDENT_KEYWORDS):
            return EvidenceType.INCIDENT_REPORT
        
        # Check for sensor alerts
        if "sensor" in doc_type.lower() or any(kw in searchable for kw in EvidenceClassifier.SENSOR_KEYWORDS):
            return EvidenceType.SENSOR_ALERT
        
        # Check for expert observations
        if "expert" in doc_type.lower() or "note" in doc_type.lower() or any(kw in searchable for kw in EvidenceClassifier.EXPERT_KEYWORDS):
            return EvidenceType.EXPERT_OBSERVATION
        
        # Check for inspection findings
        if "inspection" in doc_type.lower() or any(kw in searchable for kw in EvidenceClassifier.INSPECTION_KEYWORDS):
            return EvidenceType.INSPECTION_FINDING
        
        # Check for maintenance events
        if "maintenance" in doc_type.lower() or any(kw in searchable for kw in EvidenceClassifier.MAINTENANCE_KEYWORDS):
            return EvidenceType.MAINTENANCE_EVENT
        
        # Check for failure events (but not maintenance)
        if any(kw in searchable for kw in EvidenceClassifier.FAILURE_KEYWORDS):
            return EvidenceType.FAILURE_EVENT
        
        # Default to manual recommendation
        return EvidenceType.MANUAL_RECOMMENDATION


class RootCauseFilter:
    """Filters and validates root cause candidates"""
    
    # Never valid as primary root cause — these are maintenance types, not failure mechanisms
    INVALID_ROOT_CAUSES = {
        "preventive maintenance", "annual overhaul", "scheduled calibration",
        "routine inspection", "pm schedule", "routine service",
        "planned maintenance", "maintenance schedule",
        "preventive maintenance schedule", "lack of maintenance",
        "delayed maintenance", "insufficient training",
        "human error", "operator error", "poor maintenance",
        "inadequate maintenance", "maintenance not performed",
        "normal wear and tear", "aging equipment",
    }
    
    # Valid evidence types for root cause (weighted by reliability)
    VALID_ROOT_CAUSE_TYPES = {
        EvidenceType.FAILURE_EVENT,
        EvidenceType.INCIDENT_REPORT,
        EvidenceType.SENSOR_ALERT,
        EvidenceType.EXPERT_OBSERVATION,
    }
    
    @staticmethod
    def is_valid_root_cause(cause_text: str, evidence_type: EvidenceType) -> bool:
        """
        Determine if a cause is valid as a root cause.
        
        Returns True if valid, False if it's maintenance or scheduled activity.
        """
        cause_lower = cause_text.lower()
        
        # Check if it's in the invalid list
        if any(invalid in cause_lower for invalid in RootCauseFilter.INVALID_ROOT_CAUSES):
            return False
        
        # Check if evidence type supports root cause assignment
        if evidence_type not in RootCauseFilter.VALID_ROOT_CAUSE_TYPES:
            return False
        
        return True
    
    @staticmethod
    def filter_root_causes(
        causes: List[Dict[str, Any]],
        evidence_types: Dict[str, EvidenceType]
    ) -> List[Dict[str, Any]]:
        """
        Filter root causes to remove invalid ones.
        
        Args:
            causes: List of causes with {'description', 'probability', 'source'}
            evidence_types: Mapping of source to EvidenceType
        
        Returns:
            Filtered list of valid root causes
        """
        valid_causes = []
        
        for cause in causes:
            cause_text = cause.get("description", "")
            source = cause.get("source", "")
            evidence_type = evidence_types.get(source, EvidenceType.MANUAL_RECOMMENDATION)
            
            if RootCauseFilter.is_valid_root_cause(cause_text, evidence_type):
                valid_causes.append(cause)
        
        return valid_causes if valid_causes else causes


class ConfidenceCalculator:
    """Calculates confidence scores based on evidence quality and agreement"""
    
    @staticmethod
    def calculate_base_confidence(evidence_type: EvidenceType) -> float:
        """Get base confidence score for an evidence type"""
        return EvidenceWeight.WEIGHTS.get(evidence_type.value, 0.5)
    
    @staticmethod
    def boost_with_agreement(
        base_confidence: float,
        supporting_sources: List[str],
        evidence_types: Dict[str, EvidenceType]
    ) -> float:
        """
        Boost confidence if multiple sources agree on the root cause.
        
        Returns confidence score 0-100
        """
        confidence = base_confidence * 100
        
        # Bonus for multiple evidence sources
        if len(supporting_sources) > 1:
            # Calculate average weight of supporting sources
            weights = [
                EvidenceWeight.WEIGHTS.get(
                    evidence_types.get(src, EvidenceType.MANUAL_RECOMMENDATION).value, 0.5
                )
                for src in supporting_sources
            ]
            avg_weight = sum(weights) / len(weights)
            confidence = min(95, (confidence + avg_weight * 100) / 2)
        
        return int(confidence)


# Export main components
__all__ = [
    "Intent",
    "EvidenceType",
    "IntentDetector",
    "IntentBasedRetrievalPlanner",
    "EvidenceClassifier",
    "RootCauseFilter",
    "ConfidenceCalculator",
]
