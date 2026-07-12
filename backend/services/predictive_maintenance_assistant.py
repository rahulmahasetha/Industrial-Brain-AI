"""
Predictive Maintenance Assistant

Provides maintenance risk assessment and recommendations based on:
- Equipment health scores
- Recent incident history
- Maintenance history
- Expert notes
- Sensor data patterns
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.domain import Asset, Incident, Document
from services.intent_based_retrieval_planner import IntentDetector, Intent


class PredictiveMaintenanceAssistant:
    """Analyzes equipment health and provides predictive insights"""
    
    HEALTH_THRESHOLDS = {
        "critical": (0, 40),
        "high_risk": (40, 60),
        "moderate": (60, 80),
        "healthy": (80, 100),
    }
    
    @staticmethod
    def assess_equipment_risk(
        db: Session,
        asset_tag: str,
        asset: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Assess the risk profile of equipment.
        
        Returns:
        {
            "asset_tag": "AC101",
            "current_health": 85,
            "health_status": "healthy",
            "failure_probability": 15,
            "risk_level": "low",
            "trend": "stable",
            "last_failure": "2025-12-15T10:30:00",
            "days_since_failure": 45,
            "recommendation": "Continue routine maintenance schedule"
        }
        """
        
        if not asset:
            asset = db.query(Asset).filter(Asset.tag == asset_tag).first()
        
        if not asset:
            return {
                "asset_tag": asset_tag,
                "status": "not_found",
                "message": f"Asset {asset_tag} not found in system"
            }
        
        # Get incident history
        incidents = db.query(Incident).filter(
            Incident.asset_tag == asset_tag
        ).order_by(Incident.created_at.desc()).all()
        
        # Calculate metrics
        health = asset.health_score or 100.0
        failure_prob = PredictiveMaintenanceAssistant._calculate_failure_probability(
            asset, incidents
        )
        
        # Get health status
        health_status = None
        for status, (low, high) in PredictiveMaintenanceAssistant.HEALTH_THRESHOLDS.items():
            if low <= health < high:
                health_status = status
                break
        if health_status is None:
            health_status = "healthy" if health >= 80 else "critical"
        
        # Get risk level
        risk_level = PredictiveMaintenanceAssistant._map_risk_level(health, failure_prob, incidents)
        
        # Get trend
        trend = PredictiveMaintenanceAssistant._analyze_trend(incidents)
        
        # Get last failure info
        last_failure = None
        days_since_failure = None
        if incidents:
            last_incident = incidents[0]
            last_failure = last_incident.created_at.isoformat() if last_incident.created_at else None
            if last_incident.created_at:
                days_since_failure = (datetime.utcnow() - last_incident.created_at).days
        
        # Generate recommendation
        recommendation = PredictiveMaintenanceAssistant._generate_recommendation(
            health, failure_prob, risk_level, incidents
        )
        
        return {
            "asset_tag": asset_tag,
            "asset_name": asset.name or "",
            "current_health": int(health),
            "health_status": health_status,
            "equipment_status": asset.status or "operational",
            "failure_probability": int(failure_prob),
            "risk_level": risk_level,
            "trend": trend,
            "last_failure": last_failure,
            "days_since_failure": days_since_failure,
            "recent_incidents": len([i for i in incidents if i.created_at and (datetime.utcnow() - i.created_at).days <= 90]),
            "total_incidents": len(incidents),
            "recommendation": recommendation,
            "next_inspection_due": PredictiveMaintenanceAssistant._estimate_inspection_due(health, incidents),
        }
    
    @staticmethod
    def _calculate_failure_probability(asset: Any, incidents: List[Any]) -> float:
        """Calculate probability of failure based on health and history"""
        
        # Base on health score (inverse relationship)
        base_prob = max(5, min(95, 100 - (asset.health_score or 100)))
        
        # Recent incident penalty
        recent_incidents = sum(
            1 for i in incidents
            if i.created_at and (datetime.utcnow() - i.created_at).days <= 90
        )
        recent_penalty = min(30, recent_incidents * 8)
        
        # Equipment status penalty
        status_penalty = {
            "critical": 30,
            "shutdown": 40,
            "warning": 15,
            "operational": 0
        }.get(asset.status or "operational", 0)
        
        return max(5, min(95, base_prob + recent_penalty + status_penalty))
    
    @staticmethod
    def _map_risk_level(health: float, failure_prob: float, incidents: List[Any]) -> str:
        """Map metrics to risk level"""
        
        if health < 40 or failure_prob > 80:
            return "Critical - Immediate Attention Required"
        elif health < 60 or failure_prob > 60 or len([i for i in incidents if i.created_at and (datetime.utcnow() - i.created_at).days <= 30]) > 0:
            return "High - Intervention Needed"
        elif health < 80 or failure_prob > 40:
            return "Moderate - Monitor Closely"
        else:
            return "Low - Routine Maintenance Sufficient"
    
    @staticmethod
    def _analyze_trend(incidents: List[Any]) -> str:
        """Analyze incident trend"""
        
        if not incidents:
            return "No recorded failures"
        
        # Check recent incidents
        recent_90 = [i for i in incidents if i.created_at and (datetime.utcnow() - i.created_at).days <= 90]
        recent_30 = [i for i in incidents if i.created_at and (datetime.utcnow() - i.created_at).days <= 30]
        
        if len(recent_30) >= 2:
            return "Deteriorating - Multiple failures in last 30 days"
        elif len(recent_90) >= 3:
            return "Worsening - Pattern of increased incidents"
        elif len(recent_90) >= 1:
            return "Concerning - Recent incident detected"
        elif len(incidents) > 5:
            return "Stable - Historical issues not recently recurring"
        else:
            return "Stable - Few historical incidents"
    
    @staticmethod
    def _generate_recommendation(
        health: float,
        failure_prob: float,
        risk_level: str,
        incidents: List[Any]
    ) -> str:
        """Generate actionable recommendation"""
        
        if "Critical" in risk_level:
            return "⚠️ IMMEDIATE: Schedule emergency maintenance. Equipment should not operate without inspection."
        
        if "High" in risk_level:
            return "Schedule preventive maintenance within 7 days. Increase monitoring frequency."
        
        if "Moderate" in risk_level:
            if len(incidents) > 3:
                return "Schedule maintenance within 30 days. Analyze failure patterns to prevent recurrence."
            else:
                return "Schedule routine inspection within 30 days. Monitor sensor data closely."
        
        return "Continue routine maintenance schedule. Annual inspection recommended."
    
    @staticmethod
    def _estimate_inspection_due(health: float, incidents: List[Any]) -> str:
        """Estimate when next inspection should be due"""
        
        if health < 40:
            return "Immediately (Critical)"
        elif health < 60:
            return "Within 7 days (Urgent)"
        elif health < 80 or len([i for i in incidents if i.created_at and (datetime.utcnow() - i.created_at).days <= 90]) > 0:
            return "Within 30 days"
        else:
            return "Within 90 days (Routine)"
    
    @staticmethod
    def get_predictive_insights(
        db: Session,
        asset_tag: str,
        include_maintenance_history: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive predictive insights for an asset.
        
        Combines health score, incidents, maintenance history, and expert notes.
        """
        
        # Get asset and risk assessment
        asset = db.query(Asset).filter(Asset.tag == asset_tag).first()
        risk_assessment = PredictiveMaintenanceAssistant.assess_equipment_risk(db, asset_tag, asset)
        
        if risk_assessment.get("status") == "not_found":
            return risk_assessment
        
        # Get maintenance history if requested
        maintenance_history = []
        if include_maintenance_history and asset:
            try:
                # Search for maintenance documents related to this asset
                maint_docs = db.query(Document).filter(
                    and_(
                        Document.type.ilike("%maintenance%"),
                        Document.equipment_tags.ilike(f"%{asset_tag}%") if asset_tag else True
                    )
                ).order_by(Document.created_at.desc()).limit(5).all()
                
                maintenance_history = [
                    {
                        "document": d.title,
                        "date": d.created_at.isoformat() if d.created_at else "",
                        "status": d.status
                    }
                    for d in maint_docs
                ]
            except Exception as e:
                print(f"Error fetching maintenance history: {e}")
        
        # Get expert notes
        expert_notes = []
        try:
            from models.domain import ExpertKnowledge
            notes = db.query(ExpertKnowledge).filter(
                ExpertKnowledge.target_asset == asset_tag
            ).order_by(ExpertKnowledge.created_at.desc()).limit(3).all()
            
            expert_notes = [
                {
                    "condition": n.condition,
                    "action": n.action,
                    "confidence": n.confidence,
                    "validated": n.validated
                }
                for n in notes
            ]
        except Exception as e:
            print(f"Error fetching expert notes: {e}")
            
        # Generate LLM advisory
        advisory = PredictiveMaintenanceAssistant.generate_advisory(db, asset_tag, asset, risk_assessment)
        
        return {
            "asset_tag": asset_tag,
            "risk_assessment": risk_assessment,
            "maintenance_history": maintenance_history,
            "expert_insights": expert_notes,
            "advisory": advisory,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def generate_advisory(db: Session, asset_tag: str, asset: Optional[Any], risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a natural language advisory using LLM."""
        import os
        import json
        import re
        from models.domain import Incident, Document
        
        has_api_key = bool(os.environ.get("GOOGLE_API_KEY"))
        has_groq_key = bool(os.environ.get("GROQ_API_KEY"))
        
        # Gather recent incidents
        incidents = db.query(Incident).filter(
            Incident.asset_tag == asset_tag
        ).order_by(Incident.created_at.desc()).limit(5).all()
        
        incident_summaries = "\n".join([f"- {i.created_at.strftime('%Y-%m-%d') if i.created_at else 'Unknown'}: {i.description}" for i in incidents])
        if not incident_summaries:
            incident_summaries = "No recent incidents recorded."
            
        # Estimate days since maintenance
        maint_doc = db.query(Document).filter(
            and_(
                Document.type.ilike("%maintenance%"),
                Document.equipment_tags.ilike(f"%{asset_tag}%")
            )
        ).order_by(Document.created_at.desc()).first()
        
        days_since_maint = "Unknown"
        if maint_doc and maint_doc.created_at:
            days_since_maint = str((datetime.utcnow() - maint_doc.created_at).days)
            
        if has_api_key or has_groq_key:
            try:
                primary_llm = None
                fallback_llm = None
                
                if has_groq_key:
                    from langchain_groq import ChatGroq
                    primary_llm = ChatGroq(
                        api_key=os.environ.get("GROQ_API_KEY"),
                        model="llama-3.3-70b-versatile"
                    )
                    
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
                    """You are a predictive maintenance advisor for an industrial beverage plant.

ASSET: {asset_tag}
ASSET NAME: {asset_name}
ASSET TYPE: {asset_type}
CURRENT HEALTH SCORE: {health_score}/100
FAILURE PROBABILITY: {failure_probability}%
DAYS SINCE LAST MAINTENANCE: {days_since_maintenance}
RECENT INCIDENTS (last 90 days): {incident_count}
LAST FAILURE DATE: {last_failure}

RECENT INCIDENT DETAILS:
{incident_summaries}

Generate a maintenance advisory in this exact JSON format:
{{
  "risk_level": "CRITICAL|HIGH|MODERATE|LOW",
  "headline": "One sentence summary of the asset's condition",
  "predicted_failure_window": "e.g. Within 7-14 days if unaddressed",
  "key_risk_factors": [
    "Factor 1 with specific data point",
    "Factor 2 with specific data point"
  ],
  "recommended_action": {{
    "action_type": "IMMEDIATE_SHUTDOWN|SCHEDULE_MAINTENANCE|MONITOR|ROUTINE",
    "description": "Specific action to take",
    "urgency": "Within 24h|Within 1 week|Next scheduled window",
    "estimated_cost_of_inaction": "What happens if ignored"
  }},
  "maintenance_checklist": [
    "Check item 1",
    "Check item 2",
    "Check item 3"
  ]
}}

Base the risk assessment on the actual numbers provided. Only output valid JSON."""
                )
                
                chain = prompt | primary_llm | StrOutputParser()
                try:
                    result = chain.invoke({
                        "asset_tag": asset_tag,
                        "asset_name": asset.name if asset else "Unknown",
                        "asset_type": asset.type if asset else "Unknown",
                        "health_score": risk_assessment.get("current_health", 100),
                        "failure_probability": risk_assessment.get("failure_probability", 5),
                        "days_since_maintenance": days_since_maint,
                        "incident_count": risk_assessment.get("recent_incidents", 0),
                        "last_failure": risk_assessment.get("last_failure", "None"),
                        "incident_summaries": incident_summaries
                    })
                except Exception as e:
                    if fallback_llm:
                        chain = prompt | fallback_llm | StrOutputParser()
                        result = chain.invoke({
                            "asset_tag": asset_tag,
                            "asset_name": asset.name if asset else "Unknown",
                            "asset_type": asset.type if asset else "Unknown",
                            "health_score": risk_assessment.get("current_health", 100),
                            "failure_probability": risk_assessment.get("failure_probability", 5),
                            "days_since_maintenance": days_since_maint,
                            "incident_count": risk_assessment.get("recent_incidents", 0),
                            "last_failure": risk_assessment.get("last_failure", "None"),
                            "incident_summaries": incident_summaries
                        })
                    else:
                        raise e
                
                match = re.search(r'\{.*\}', result, re.DOTALL)
                if match:
                    return json.loads(match.group())
            except Exception as e:
                print(f"LLM generate_advisory error: {e}")
                
        # Fallback
        return {
            "risk_level": "MODERATE",
            "headline": f"Asset {asset_tag} requires routine review based on recent telemetry.",
            "predicted_failure_window": "Unknown due to LLM fallback",
            "key_risk_factors": ["Unable to dynamically assess risk factors without LLM"],
            "recommended_action": {
                "action_type": "MONITOR",
                "description": "Continue standard monitoring protocols.",
                "urgency": "Next scheduled window",
                "estimated_cost_of_inaction": "Potential undetected degradation"
            },
            "maintenance_checklist": ["Perform visual inspection", "Check lubrication", "Verify sensor calibration"]
        }


# Singleton instance
predictive_maintenance_assistant = PredictiveMaintenanceAssistant()

