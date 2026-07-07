from typing import Dict, Any, TypedDict, List, Tuple
from langgraph.graph import StateGraph, END
import os
import json
import re
from dotenv import load_dotenv
from datetime import datetime

from services.intent_based_retrieval_planner import (
    Intent,
    IntentDetector,
    IntentBasedRetrievalPlanner,
    EvidenceClassifier,
    RootCauseFilter,
    ConfidenceCalculator,
    EvidenceType,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class AgentState(TypedDict):
    anomaly: str
    asset_tag: str
    intent: str
    logs: list
    documentation_context: str
    retrieved_documents: list
    evidence_classified: dict
    causes: list
    filtered_causes: list
    confidence_score: int
    recommendations: list
    similar_incidents: list


class RootCauseAnalysisAgent:
    def __init__(self):
        self.agent_name = "RCA Agent"
        self.has_api_key = bool(os.environ.get("GOOGLE_API_KEY"))
        self.graph = self._build_graph()
        
    def _build_graph(self):
        """Builds a LangGraph workflow for root cause analysis with intent-based retrieval."""
        workflow = StateGraph(AgentState)
        workflow.add_node("detect_intent", self.detect_intent)
        workflow.add_node("gather_sensor_data", self.gather_sensor_data)
        workflow.add_node("retrieve_documentation", self.retrieve_documentation)
        workflow.add_node("classify_evidence", self.classify_evidence)
        workflow.add_node("analyze_causes", self.analyze_causes)
        workflow.add_node("filter_root_causes", self.filter_root_causes)
        workflow.add_node("find_similar_incidents", self.find_similar_incidents)
        workflow.add_node("generate_recommendations", self.generate_recommendations)
        workflow.add_node("format_response", self.format_response)
        
        workflow.set_entry_point("detect_intent")
        workflow.add_edge("detect_intent", "gather_sensor_data")
        workflow.add_edge("gather_sensor_data", "retrieve_documentation")
        workflow.add_edge("retrieve_documentation", "classify_evidence")
        workflow.add_edge("classify_evidence", "analyze_causes")
        workflow.add_edge("analyze_causes", "filter_root_causes")
        workflow.add_edge("filter_root_causes", "find_similar_incidents")
        workflow.add_edge("find_similar_incidents", "generate_recommendations")
        workflow.add_edge("generate_recommendations", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile()
    
    def detect_intent(self, state: AgentState):
        """Detect intent from anomaly description."""
        intent = IntentDetector.detect(state['anomaly'])
        return {"intent": intent.value}
        
    def gather_sensor_data(self, state: AgentState):
        """Fetch recent incidents and sensor data from DB for the asset."""
        try:
            from database import SessionLocal
            from models.domain import Incident
            
            db = SessionLocal()
            incidents = db.query(Incident).filter(
                Incident.asset_tag == state['asset_tag']
            ).order_by(Incident.created_at.desc()).limit(10).all()
            db.close()
            
            logs = []
            for i in incidents:
                logs.append({
                    "id": i.id,
                    "title": i.title,
                    "description": i.description,
                    "severity": i.severity,
                    "created_at": i.created_at.isoformat() if i.created_at else "",
                })
            
            return {"logs": logs or []}
        except Exception as e:
            print(f"Error fetching sensor data: {e}")
            return {"logs": []}

    def retrieve_documentation(self, state: AgentState):
        """
        Retrieve documentation using intent-based priority.
        
        For RCA, this means:
        1. Incident Reports (highest priority)
        2. RCA Reports
        3. Maintenance Logs
        4. Expert Notes
        5. Inspection Reports
        """
        try:
            from services.ingestion import get_chroma_vectorstore
            
            vectorstore = get_chroma_vectorstore()
            retriever = vectorstore.as_retriever(search_kwargs={"k": 15})  # Get more documents
            
            query = f"{state['asset_tag']} {state['anomaly']}"
            all_docs = retriever.invoke(query)
            
            # Rank documents by intent priority
            intent = Intent(state['intent'])
            ranked_docs = IntentBasedRetrievalPlanner.rank_documents(all_docs, intent)
            
            # Take top 8 ranked documents
            top_docs = [doc for doc, score in ranked_docs[:8]]
            
            return {
                "retrieved_documents": top_docs,
                "documentation_context": "\n\n".join([doc.page_content for doc in top_docs])
            }
        except Exception as e:
            print(f"Error retrieving documentation: {e}")
            return {"retrieved_documents": [], "documentation_context": ""}
    
    def classify_evidence(self, state: AgentState):
        """Classify retrieved documents into evidence types."""
        classified = {}
        source_to_type = {}
        
        for doc in state['retrieved_documents']:
            evidence_type = EvidenceClassifier.classify(doc)
            title = doc.metadata.get("title", "Unknown") if hasattr(doc, "metadata") else "Unknown"
            
            if evidence_type.value not in classified:
                classified[evidence_type.value] = []
            
            classified[evidence_type.value].append({
                "title": title,
                "content": doc.page_content[:500]  # Truncate for brevity
            })
            
            source_to_type[title] = evidence_type
        
        return {
            "evidence_classified": classified,
        }
        
    def analyze_causes(self, state: AgentState):
        """
        Use LLM or heuristics to determine root causes.
        
        IMPORTANT: Filters out preventive maintenance as root cause.
        """
        context = state.get("documentation_context", "")
        anomaly = state.get("anomaly", "")
        logs = state.get("logs", [])
        evidence_classified = state.get("evidence_classified", {})
        
        causes = []
        
        if self.has_api_key and anomaly:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                from langchain_core.prompts import PromptTemplate
                from langchain_core.output_parsers import StrOutputParser
                
                llm = ChatGoogleGenerativeAI(model=os.environ.get("GOOGLE_MODEL", "gemini-2.5-flash"))
                
                # Build context with evidence classification
                evidence_summary = "\n".join([
                    f"- {evidence_type}: {len(docs)} sources"
                    for evidence_type, docs in evidence_classified.items()
                ])
                
                prompt = PromptTemplate.from_template(
                    """You are an industrial Root Cause Analysis expert for a beverage manufacturing plant (Bharat Industrial Works / FreshFlow Beverages).

Given the following anomaly report and retrieved evidence from plant documents, perform a structured root cause analysis.

ANOMALY: {anomaly}
ASSET: {asset_tag}
INTENT: {intent}

RETRIEVED EVIDENCE:
{context}

RECENT INCIDENT HISTORY:
{logs}

CLASSIFIED EVIDENCE:
{evidence_summary}

Your task:
1. Identify the most likely root cause (primary)
2. Identify 2-3 contributing causes (secondary)
3. For each cause, cite the specific document/source that supports it
4. Assign a confidence score (0-100) based on how well the evidence supports the conclusion

IMPORTANT: The root cause must directly explain the symptom described in the anomaly. "Preventive maintenance schedule" is NEVER a root cause — it is a maintenance type. A root cause must be a physical or process failure mechanism (e.g. "worn O-ring causing pressure loss", "clogged inlet filter reducing flow", "miscalibrated pressure sensor giving false alert").

If the evidence does not clearly support a root cause, say confidence is LOW and explain what additional data is needed.

Respond in this exact JSON format:
{{
  "primary_cause": {{
    "description": "...",
    "mechanism": "...",
    "evidence_source": "document_id or incident_id",
    "confidence": 85
  }},
  "contributing_causes": [
    {{
      "description": "...",
      "evidence_source": "...",
      "confidence": 70
    }}
  ],
  "overall_confidence": 80,
  "reasoning": "Step-by-step explanation of how you reached this conclusion"
}}

Only output valid JSON. No preamble or markdown."""
                )
                chain = prompt | llm | StrOutputParser()
                result = chain.invoke({
                    "anomaly": anomaly,
                    "asset_tag": state.get("asset_tag", ""),
                    "intent": state.get("intent", ""),
                    "logs": json.dumps(logs[:3], indent=2),
                    "evidence_summary": evidence_summary,
                    "context": context[:2000]
                })
                
                # Parse the new JSON format
                match = re.search(r'\{.*\}', result, re.DOTALL)
                if match:
                    parsed_result = json.loads(match.group())
                    
                    # Convert to expected format for downstream nodes
                    primary = parsed_result.get("primary_cause", {})
                    if primary:
                        causes.append({
                            "description": primary.get("description", ""),
                            "probability": primary.get("confidence", 85),
                            "mechanism": primary.get("mechanism", ""),
                            "evidence_type": primary.get("evidence_source", "")
                        })
                        
                    for cc in parsed_result.get("contributing_causes", []):
                        causes.append({
                            "description": cc.get("description", ""),
                            "probability": cc.get("confidence", 50),
                            "evidence_type": cc.get("evidence_source", "")
                        })
                        
                    # We can store reasoning and overall confidence in state if needed, 
                    # but for now we'll just extract the causes for the downstream filters
            except Exception as e:
                print(f"LLM analyze_causes error: {e}")
        
        # Fallback: keyword-based analysis
        if not causes:
            anomaly_lower = anomaly.lower()
            if any(k in anomaly_lower for k in ["jam", "blocked", "blockage", "stuck"]):
                causes.append({"description": "Material blockage or foreign object obstruction", "probability": 85})
                causes.append({"description": "Mechanical jam due to wear", "probability": 55})
            elif any(k in anomaly_lower for k in ["vibrat", "bearing", "noise"]):
                causes.append({"description": "Bearing wear or degradation", "probability": 80})
                causes.append({"description": "Shaft misalignment", "probability": 50})
            elif any(k in anomaly_lower for k in ["temp", "overheat", "hot"]):
                causes.append({"description": "Inadequate lubrication in bearings", "probability": 75})
                causes.append({"description": "Cooling system malfunction", "probability": 55})
            elif any(k in anomaly_lower for k in ["leak", "seal", "pressure"]):
                causes.append({"description": "Mechanical seal degradation", "probability": 75})
                causes.append({"description": "O-ring wear or material failure", "probability": 55})
            else:
                causes.append({"description": "Bearing failure due to degradation", "probability": 70})
                causes.append({"description": "Blockage in fluid pathways", "probability": 45})
        
        # Remove any preventive maintenance entries (keep only valid physical/process root causes)
        causes = [c for c in causes if RootCauseFilter.is_valid_root_cause(c.get("description", ""), EvidenceType.FAILURE_EVENT)]
        
        return {"causes": causes if causes else [{"description": "Unable to determine specific root cause", "probability": 50}]}
    
    def filter_root_causes(self, state: AgentState):
        """
        Filter root causes to ensure only valid causes are returned.
        
        This ensures:
        1. No preventive maintenance as root cause
        2. Only supported evidence types
        3. Confidence scores are calculated
        """
        causes = state.get("causes", [])
        evidence_classified = state.get("evidence_classified", {})
        
        # Create evidence type mapping
        evidence_types = {}
        for evidence_type, docs in evidence_classified.items():
            for doc in docs:
                evidence_types[doc.get("title", "")] = EvidenceType(evidence_type)
        
        # Filter using RootCauseFilter
        filtered = RootCauseFilter.filter_root_causes(causes, evidence_types)
        
        # Calculate confidence for top cause
        confidence = 50
        if filtered:
            top_cause = filtered[0]
            # Base confidence on probability + evidence quality
            prob = top_cause.get("probability", 50) / 100.0
            
            # Bonus if we have incident reports or sensor alerts
            has_strong_evidence = len(evidence_classified.get("incident_report", [])) > 0 or \
                                 len(evidence_classified.get("sensor_alert", [])) > 0
            
            base_conf = prob * 100
            if has_strong_evidence:
                confidence = min(95, int(base_conf * 1.1))
            else:
                confidence = int(base_conf)
        
        return {
            "filtered_causes": filtered,
            "confidence_score": confidence
        }
    
    def find_similar_incidents(self, state: AgentState):
        """Find similar past incidents to provide historical context."""
        similar = []
        
        try:
            from database import SessionLocal
            from models.domain import Incident
            
            db = SessionLocal()
            
            # Search for incidents with similar descriptions
            search_term = state['anomaly'].split()[0] if state['anomaly'] else ""
            if search_term and len(search_term) > 2:
                incidents = db.query(Incident).filter(
                    (Incident.description.ilike(f"%{search_term}%")) |
                    (Incident.root_cause.ilike(f"%{search_term}%"))
                ).order_by(Incident.created_at.desc()).limit(3).all()
                
                for inc in incidents:
                    similar.append({
                        "id": inc.id,
                        "title": inc.title,
                        "root_cause": inc.root_cause,
                        "corrective_action": inc.corrective_action,
                        "resolved": inc.status == "closed"
                    })
            
            db.close()
        except Exception as e:
            print(f"Error finding similar incidents: {e}")
        
        return {"similar_incidents": similar}

        
    def generate_recommendations(self, state: AgentState):
        """Generate actionable recommendations based on root causes."""
        filtered_causes = state.get("filtered_causes", [])
        anomaly = state.get("anomaly", "")
        context = state.get("documentation_context", "")
        similar_incidents = state.get("similar_incidents", [])
        asset_tag = state.get("asset_tag", "Unknown")
        
        recommendations = {}
        
        if not filtered_causes:
            return {"recommendations": {
                "immediate_actions": [{"action": "Perform comprehensive equipment inspection", "priority": "HIGH", "estimated_time": "1 hour", "responsible_team": "Maintenance"}],
                "preventive_actions": [],
                "parts_required": [],
                "estimated_downtime": "Unknown"
            }}
        
        if self.has_api_key and anomaly:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                from langchain_core.prompts import PromptTemplate
                from langchain_core.output_parsers import StrOutputParser
                
                llm = ChatGoogleGenerativeAI(model=os.environ.get("GOOGLE_MODEL", "gemini-2.5-flash"))
                prompt = PromptTemplate.from_template(
                    """You are a senior maintenance engineer at an industrial beverage plant.

Based on the root cause analysis below, generate specific, actionable recommendations.

ANOMALY: {anomaly}
ASSET: {asset_tag}
ROOT CAUSES: {filtered_causes}
SIMILAR PAST INCIDENTS: {similar_incidents}

Generate recommendations in this exact JSON format:
{{
  "immediate_actions": [
    {{
      "action": "...",
      "priority": "CRITICAL|HIGH|MEDIUM",
      "estimated_time": "e.g. 2 hours",
      "responsible_team": "e.g. Maintenance Team",
      "sop_reference": "SOP-034 Section 4.2 (if applicable)"
    }}
  ],
  "preventive_actions": [
    {{
      "action": "...",
      "frequency": "e.g. Weekly",
      "standard_reference": "ISO 22000 Clause 8.5 (if applicable)"
    }}
  ],
  "parts_required": ["part name 1", "part name 2"],
  "estimated_downtime": "e.g. 4-6 hours"
}}

Base recommendations on the evidence. If a similar incident occurred before, reference what was done then. Only output valid JSON."""
                )
                chain = prompt | llm | StrOutputParser()
                result = chain.invoke({
                    "anomaly": anomaly,
                    "asset_tag": asset_tag,
                    "filtered_causes": json.dumps(filtered_causes[:2], indent=2),
                    "similar_incidents": json.dumps(similar_incidents[:2], indent=2)
                })
                
                match = re.search(r'\{.*\}', result, re.DOTALL)
                if match:
                    recommendations = json.loads(match.group())
            except Exception as e:
                print(f"LLM generate_recommendations error: {e}")
        
        # Fallback recommendations based on anomaly type
        if not recommendations:
            anomaly_lower = anomaly.lower()
            if any(k in anomaly_lower for k in ["jam", "blocked"]):
                recommendations = {
                    "immediate_actions": [
                        {"action": "Immediately stop equipment to prevent damage", "priority": "CRITICAL", "estimated_time": "15 mins", "responsible_team": "Operators"},
                        {"action": "Inspect and remove blockage or foreign material", "priority": "HIGH", "estimated_time": "1 hour", "responsible_team": "Maintenance"}
                    ],
                    "preventive_actions": [
                        {"action": "Document findings for preventive measures", "frequency": "Monthly", "standard_reference": ""}
                    ],
                    "parts_required": [],
                    "estimated_downtime": "1-2 hours"
                }
            elif any(k in anomaly_lower for k in ["vibrat", "noise"]):
                recommendations = {
                    "immediate_actions": [
                        {"action": "Isolate equipment and perform visual inspection", "priority": "HIGH", "estimated_time": "30 mins", "responsible_team": "Maintenance"},
                        {"action": "Check bearing clearances and lubrication levels", "priority": "MEDIUM", "estimated_time": "1 hour", "responsible_team": "Maintenance"}
                    ],
                    "preventive_actions": [
                        {"action": "Verify shaft alignment using laser alignment tool", "frequency": "Quarterly", "standard_reference": ""}
                    ],
                    "parts_required": ["Bearings (if damaged)"],
                    "estimated_downtime": "2-4 hours"
                }
            elif any(k in anomaly_lower for k in ["temp", "overheat"]):
                recommendations = {
                    "immediate_actions": [
                        {"action": "Cool equipment and allow to reach ambient temperature", "priority": "CRITICAL", "estimated_time": "2 hours", "responsible_team": "Operators"},
                        {"action": "Check lubrication level and quality", "priority": "HIGH", "estimated_time": "30 mins", "responsible_team": "Maintenance"}
                    ],
                    "preventive_actions": [
                        {"action": "Inspect cooling system for blockages", "frequency": "Monthly", "standard_reference": ""}
                    ],
                    "parts_required": ["Coolant/Lubricant"],
                    "estimated_downtime": "2-3 hours"
                }
            else:
                recommendations = {
                    "immediate_actions": [
                        {"action": "Isolate and tag equipment to prevent operation", "priority": "CRITICAL", "estimated_time": "15 mins", "responsible_team": "Safety/Operators"},
                        {"action": "Perform detailed physical inspection", "priority": "HIGH", "estimated_time": "2 hours", "responsible_team": "Maintenance"}
                    ],
                    "preventive_actions": [
                        {"action": "Review maintenance history and sensor data", "frequency": "As needed", "standard_reference": ""}
                    ],
                    "parts_required": [],
                    "estimated_downtime": "Unknown"
                }
        
        return {"recommendations": recommendations}
    
    def format_response(self, state: AgentState):
        """Format response in the structured output format required."""
        # Build executive summary
        filtered_causes = state.get("filtered_causes", [])
        anomaly = state.get("anomaly", "")
        asset_tag = state.get("asset_tag", "Unknown")
        confidence = state.get("confidence_score", 50)
        recommendations = state.get("recommendations", [])
        similar_incidents = state.get("similar_incidents", [])
        evidence_classified = state.get("evidence_classified", {})
        retrieved_documents = state.get("retrieved_documents", [])
        
        top_cause = filtered_causes[0] if filtered_causes else {"description": "Unknown", "probability": 0}
        
        # Build structured response
        response = {
            "executive_summary": f"Equipment {asset_tag} anomaly: {anomaly}. Analysis indicates the most probable root cause is {top_cause.get('description', 'unknown')}.",
            "most_probable_root_cause": top_cause.get('description', 'Unknown'),
            "confidence": f"{confidence}%",
            "alternative_causes": [
                c.get('description', 'Unknown')
                for c in filtered_causes[1:] if len(filtered_causes) > 1
            ][:2],
            "evidence_used": {
                evidence_type: len(docs)
                for evidence_type, docs in evidence_classified.items()
            },
            "evidence_sources": [
                doc.metadata.get("title", "Unknown")
                for doc in retrieved_documents[:5]
            ] if retrieved_documents else [],
            "historical_similar_incidents": similar_incidents,
            "recommended_actions": recommendations,
            "sources_cited": [
                doc.metadata.get("title", "Unknown")
                for doc in retrieved_documents
            ] if retrieved_documents else []
        }
        
        return response
        
    def analyze_anomaly(self, description: str, asset_tag: str = None) -> Dict[str, Any]:
        """
        Executes the LangGraph agent workflow to deduce root causes.
        
        Returns structured response with:
        - Executive summary
        - Most probable root cause
        - Confidence score
        - Evidence used
        - Historical context
        - Recommended actions
        - Source citations
        """
        print(f"[{self.agent_name}] Executing enhanced workflow for: {description} (Asset: {asset_tag})")
        
        initial_state = {
            "anomaly": description,
            "asset_tag": asset_tag or "Unknown",
            "intent": Intent.ROOT_CAUSE_ANALYSIS.value,
            "logs": [],
            "documentation_context": "",
            "retrieved_documents": [],
            "evidence_classified": {},
            "causes": [],
            "filtered_causes": [],
            "confidence_score": 50,
            "recommendations": [],
            "similar_incidents": []
        }
        
        result = self.graph.invoke(initial_state)
        return result


rca_agent = RootCauseAnalysisAgent()
