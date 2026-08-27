import json
import os
from collections import defaultdict
from sqlalchemy.orm import Session
from models.domain import Incident
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class LessonsLearnedService:
    def __init__(self):
        import os
        self.has_api_key = bool(os.environ.get("GOOGLE_API_KEY"))
        self.has_groq_key = bool(os.environ.get("GROQ_API_KEY"))
        
        self.primary_llm = None
        self.fallback_llm = None
        
        if self.has_groq_key:
            try:
                from langchain_groq import ChatGroq
                self.primary_llm = ChatGroq(
                    api_key=os.environ.get("GROQ_API_KEY"),
                    model=os.environ.get("GROQ_MODEL", "qwen/qwen3.6-27b")
                )
            except Exception as e:
                print(f"Failed to init Groq in lessons learned: {e}")
                
        if self.has_api_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                model_name = os.environ.get("GOOGLE_MODEL", "gemini-3.6-flash")
                gemini_llm = ChatGoogleGenerativeAI(model=model_name)
                
                if not self.primary_llm:
                    self.primary_llm = gemini_llm
                else:
                    self.fallback_llm = gemini_llm
            except Exception as e:
                print(f"Failed to init Gemini in lessons learned: {e}")

    def analyze_patterns(self, db: Session, limit: int = 50) -> dict:
        """Analyze recent incidents to extract systemic lessons learned."""
        incidents = db.query(Incident).order_by(Incident.created_at.desc()).limit(limit).all()
        
        if not incidents:
            return {"lessons": [], "status": "no_data"}
            
        if not self.primary_llm:
            # Fallback mock analysis
            return {
                "lessons": [
                    {
                        "theme": "O-Ring Degradation",
                        "insight": "Multiple leaks across pumps suggest premature O-ring wear.",
                        "recommendation": "Switch to higher-temp Viton material for all hot-water pumps.",
                        "confidence": 85,
                        "incident_count": 3
                    }
                ],
                "status": "mock_data"
            }
            
        # Prepare context for LLM
        incident_data = []
        for inc in incidents:
            if inc.root_cause and inc.corrective_action:
                incident_data.append(
                    f"Asset: {inc.asset_tag} | Issue: {inc.title} | Cause: {inc.root_cause} | Fix: {inc.corrective_action}"
                )
                
        prompt = f"""You are an industrial failure intelligence agent.
Analyze the following recent maintenance incidents and identify 2-3 systemic patterns or 'Lessons Learned'.
Focus on recurring root causes or cross-asset failures.

INCIDENTS:
{chr(10).join(incident_data)}

Respond in EXACTLY this JSON format:
{{
  "lessons": [
    {{
      "theme": "Short title of the systemic issue",
      "insight": "1-sentence explanation of the pattern across assets",
      "recommendation": "Specific systemic corrective action",
      "confidence": 80,
      "incident_count": 2
    }}
  ]
}}
"""
        from langchain_core.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        import re
        
        try:
            pt = PromptTemplate.from_template(prompt)
            chain = pt | self.primary_llm | StrOutputParser()
            try:
                raw = chain.invoke({})
            except Exception as e:
                if self.fallback_llm:
                    chain = pt | self.fallback_llm | StrOutputParser()
                    raw = chain.invoke({})
                else:
                    raise e
                    
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                return json.loads(match.group(), strict=False)
            return {"lessons": [], "status": "parse_error"}
        except Exception as e:
            print(f"[lessons_learned] Error: {e}")
            return {"lessons": [], "status": "error", "message": str(e)}

lessons_learned_service = LessonsLearnedService()
