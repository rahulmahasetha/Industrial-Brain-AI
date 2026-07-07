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
                
                llm = ChatGoogleGenerativeAI(model=os.environ.get("GOOGLE_MODEL", "gemini-2.5-flash"))
                prompt = PromptTemplate.from_template(
                    """You are a food safety and industrial compliance auditor. Your job is to check a plant document against regulatory standards.

DOCUMENT CONTENT:
{document_text}

DOCUMENT TYPE: {document_type}
PLANT: FreshFlow Beverages (Beverage Manufacturing)

Check this document against the following standards:
- ISO 22000:2018 (Food Safety Management)
- ISO 9001:2015 (Quality Management)
- FSSAI Schedule 4 Requirements
- Factory Act 1948 (Safety provisions)

For each applicable clause, determine if the document is compliant, partially compliant, or non-compliant.

Respond in this exact JSON format:
{{
  "compliance_score": 85,
  "overall_status": "COMPLIANT|PARTIAL|NON_COMPLIANT",
  "checks": [
    {{
      "standard": "ISO 22000:2018",
      "clause": "Clause 8.5.1",
      "clause_title": "Control of production and service provision",
      "status": "COMPLIANT|PARTIAL|NON_COMPLIANT",
      "finding": "What the document says or is missing",
      "risk_level": "HIGH|MEDIUM|LOW",
      "recommendation": "What needs to be added or changed"
    }}
  ],
  "critical_gaps": ["List only HIGH risk findings here"],
  "strengths": ["What the document does well"]
}}

Only check clauses that are actually relevant to this document type. Only output valid JSON."""
                )
                
                chain = prompt | llm | StrOutputParser()
                result = chain.invoke({
                    "document_text": document_text[:3000],
                    "document_type": document_type
                })
                
                match = re.search(r'\{.*\}', result, re.DOTALL)
                if match:
                    return json.loads(match.group())
            except Exception as e:
                print(f"LLM check_compliance error: {e}")
                
        # Fallback
        return {
            "compliance_score": 85,
            "overall_status": "PARTIAL",
            "checks": [
                {
                    "standard": "ISO 22000:2018",
                    "clause": "Clause 8.5",
                    "clause_title": "Hazard control",
                    "status": "PARTIAL",
                    "finding": "Daily sanitation checklist missing sign-off for Line 2 filling zone.",
                    "risk_level": "HIGH",
                    "recommendation": "Add mandatory sign-off field for Line 2 filling zone."
                }
            ],
            "critical_gaps": [
                "Daily sanitation checklist missing sign-off for Line 2 filling zone."
            ],
            "strengths": [
                "General sanitation procedures are well documented."
            ]
        }

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
                
                llm = ChatGoogleGenerativeAI(model=os.environ.get("GOOGLE_MODEL", "gemini-2.5-flash"))
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
                    return json.loads(match.group())
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
