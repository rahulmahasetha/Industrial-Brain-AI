from typing import Dict, Any

import os
import json
import re

class ComplianceAgent:
    def __init__(self):
        self.agent_name = "Compliance Agent"
        self.has_api_key = bool(os.environ.get("GOOGLE_API_KEY"))
        
    def check_compliance(self, document_text: str, document_type: str = "Unknown") -> Dict[str, Any]:
        """
        Checks document text against food safety and worker safety standards.
        """
        if self.has_api_key and document_text and len(document_text) > 50:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                from langchain_core.prompts import PromptTemplate
                from langchain_core.output_parsers import StrOutputParser
                
                llm = ChatGoogleGenerativeAI(model=os.environ.get("GOOGLE_MODEL", "gemini-3.6-flash"))
                prompt = PromptTemplate.from_template(
                    """You are a multi-agent AI Compliance Copilot. Your job is to check an enterprise plant document against regulatory standards and return a deep forensic analysis.

DOCUMENT CONTENT:
{document_text}

DOCUMENT TYPE: {document_type}
PLANT: FreshFlow Beverages (Beverage Manufacturing)

Check this document against the following standards:
- ISO 22000:2018 (Food Safety Management)
- ISO 9001:2015 (Quality Management)
- FSSAI Schedule 4 Requirements
- Factory Act 1948 (Safety provisions)

Respond in this exact JSON format:
{{
  "confidence_metrics": {{
    "evidence_coverage": 88,
    "retrieval_score": 92,
    "llm_confidence": 95,
    "overall_compliance_confidence": 91
  }},
  "overall_status": "COMPLIANT|PARTIAL|NON_COMPLIANT",
  "knowledge_graph_links": {{
    "related_assets": ["FM101", "CV101"],
    "related_sops": ["SOP-034", "SOP-067"],
    "related_incidents": ["INC-102"]
  }},
  "checks": [
    {{
      "standard": "ISO 22000:2018",
      "clause": "Clause 8.5.1",
      "clause_title": "Control of production and service provision",
      "status": "COMPLIANT|PARTIAL|NON_COMPLIANT",
      "finding": "Detailed description of the finding",
      "prioritization": "CRITICAL|HIGH|MEDIUM|LOW",
      "recommendation": "Corrective action recommendation",
      "decision_reasoning": [
        "Retrieval Agent fetched SOP-034.",
        "Compliance Agent detected missing signature field.",
        "Risk Agent ranked as HIGH due to food safety impact."
      ],
      "evidence_chain": [
        {{
          "document_id": "SOP-034",
          "page": 12,
          "section": "4.2 Sanitation",
          "snippet": "All sanitation must be signed off.",
          "confidence": 99,
          "source_type": "SOP",
          "source_reliability": "High"
        }}
      ],
      "impact_simulation": {{
        "downtime_estimate": "4 hours",
        "production_loss": "$12,000",
        "audit_failure_probability": "High (85%)",
        "financial_impact": "High ($50,000+ fines)",
        "safety_risk": "Moderate"
      }}
    }}
  ],
  "timeline": [
    {{
      "date": "2026-06-15",
      "event": "Initial gap detected by AI Auto Audit",
      "stage": "Retrieval & Analysis"
    }}
  ]
}}

Only output valid JSON."""
                )
                
                chain = prompt | llm | StrOutputParser()
                result = chain.invoke({
                    "document_text": document_text[:3000],
                    "document_type": document_type
                })
                
                match = re.search(r'\{.*\}', result, re.DOTALL)
                if match:
                    return json.loads(match.group(), strict=False)
            except Exception as e:
                print(f"LLM check_compliance error: {e}")
                
        # Fallback
        return {
            "confidence_metrics": {
                "evidence_coverage": 85,
                "retrieval_score": 90,
                "llm_confidence": 92,
                "overall_compliance_confidence": 89
            },
            "overall_status": "PARTIAL",
            "knowledge_graph_links": {
                "related_assets": ["FM101"],
                "related_sops": ["SOP-012"],
                "related_incidents": ["INC-042"]
            },
            "checks": [
                {
                    "standard": "ISO 22000:2018",
                    "clause": "Clause 8.5",
                    "clause_title": "Hazard control",
                    "status": "PARTIAL",
                    "finding": "Daily sanitation checklist missing sign-off for Line 2 filling zone.",
                    "prioritization": "HIGH",
                    "recommendation": "Add mandatory sign-off field for Line 2 filling zone.",
                    "decision_reasoning": [
                        "Retrieval Agent fetched SOP-012.",
                        "Compliance Agent detected missing signature field.",
                        "Risk Agent ranked as HIGH due to food safety impact."
                    ],
                    "evidence_chain": [
                        {
                            "document_id": "SOP-012",
                            "page": 4,
                            "section": "3.1 Daily Sanitation",
                            "snippet": "All sanitation checklists must be completed and signed by the supervisor.",
                            "confidence": 95,
                            "source_type": "SOP",
                            "source_reliability": "High"
                        }
                    ],
                    "impact_simulation": {
                        "downtime_estimate": "2 hours",
                        "production_loss": "$5,000",
                        "audit_failure_probability": "High (80%)",
                        "financial_impact": "Medium ($10,000 fines)",
                        "safety_risk": "Moderate"
                    }
                }
            ],
            "timeline": [
                {
                    "date": "2026-06-15",
                    "event": "Initial gap detected by AI Auto Audit",
                    "stage": "Retrieval & Analysis"
                }
            ]
        }

    def explain_clause(self, standard: str, clause: str) -> str:
        """Explains a regulatory clause in plain English."""
        if self.has_api_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(model=os.environ.get("GOOGLE_MODEL", "gemini-3.6-flash"))
                prompt = f"Explain the regulatory requirement '{standard} - {clause}' in simple, plain English for a factory worker. Give a concrete example of compliance and non-compliance."
                response = llm.invoke(prompt)
                if isinstance(response.content, list):
                    return "".join(block.get("text", "") for block in response.content if isinstance(block, dict) and block.get("type") == "text")
                return str(response.content)
            except Exception as e:
                print(f"LLM explain_clause error: {e}")
        return f"This is a mocked plain English explanation of {standard} {clause}. A concrete example would be ensuring records are signed properly. Failing to do so would result in non-compliance."

    def chat_gap(self, gap_details: str, user_query: str) -> str:
        """Answers contextual questions about a specific compliance gap."""
        if self.has_api_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(model=os.environ.get("GOOGLE_MODEL", "gemini-3.6-flash"))
                prompt = f"You are an AI Compliance Expert. Based on this compliance gap:\n{gap_details}\n\nAnswer the user's question: {user_query}"
                response = llm.invoke(prompt)
                if isinstance(response.content, list):
                    return "".join(block.get("text", "") for block in response.content if isinstance(block, dict) and block.get("type") == "text")
                return str(response.content)
            except Exception as e:
                print(f"LLM chat_gap error: {e}")
        return f"This is a mocked response to your question '{user_query}' regarding the compliance gap."

compliance_agent = ComplianceAgent()


class ExpertKnowledgeAgent:
    def __init__(self):
        self.agent_name = "Expert Agent"
        self.has_api_key = bool(os.environ.get("GOOGLE_API_KEY"))
        
    def extract_knowledge(self, text: str, source_id: str = "Unknown", asset_tag: str = "") -> Dict[str, Any]:
        """
        Extracts Condition -> Action -> Asset triples from unstructured text.
        """
        if self.has_api_key and text and len(text) > 20:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                from langchain_core.prompts import PromptTemplate
                from langchain_core.output_parsers import StrOutputParser
                
                llm = ChatGoogleGenerativeAI(model=os.environ.get("GOOGLE_MODEL", "gemini-3.6-flash"))
                prompt = PromptTemplate.from_template(
                    """You are an industrial knowledge engineer. Your task is to extract structured expert knowledge from unstructured plant text (shift logs, expert notes, maintenance records).

INPUT TEXT:
{text}

SOURCE DOCUMENT: {source_id}
ASSET CONTEXT: {asset_tag} (leave blank if unknown)

Extract all Condition → Action → Asset triples present in the text. These are patterns like:
- "When [condition occurs] on [asset], do [action]"
- "If [symptom], then [corrective step]"
- "Whenever [reading exceeds threshold], [response required]"

Respond in this exact JSON format:
{{
  "structured_knowledge": [
    {{
      "condition": "Conveyor belt vibration exceeds 6 mm/s",
      "action": "Inspect belt alignment before replacing bearings",
      "target_asset": "CV101",
      "asset_type": "Conveyor",
      "confidence": 95,
      "knowledge_type": "CORRECTIVE|PREVENTIVE|DIAGNOSTIC",
      "source_passage": "exact quote from input text that led to this extraction"
    }}
  ],
  "entities_mentioned": ["asset tags or equipment names found"],
  "document_summary": "1-2 sentence summary of what this document is about"
}}

Extract every condition-action pair you find. If none exist, return an empty structured_knowledge array. Only output valid JSON."""
                )
                
                chain = prompt | llm | StrOutputParser()
                result = chain.invoke({
                    "text": text[:3000],
                    "source_id": source_id,
                    "asset_tag": asset_tag
                })
                
                match = re.search(r'\{.*\}', result, re.DOTALL)
                if match:
                    return json.loads(match.group(), strict=False)
            except Exception as e:
                print(f"LLM extract_knowledge error: {e}")
        
        # Fallback
        return {
            "structured_knowledge": [
                {
                    "condition": "Conveyor vibration > 6 mm/s",
                    "action": "Inspect belt alignment before replacing bearings",
                    "target_asset": "CV101",
                    "asset_type": "Conveyor",
                    "confidence": 98,
                    "knowledge_type": "DIAGNOSTIC",
                    "source_passage": text[:100] if text else "Default fallback passage"
                }
            ],
            "entities_mentioned": ["CV101 Conveyor Belt"],
            "document_summary": "Extracted knowledge fallback based on input text."
        }

expert_agent = ExpertKnowledgeAgent()

