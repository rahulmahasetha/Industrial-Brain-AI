from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.domain import Incident, Asset
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter()

@router.get("/patterns")
def get_failure_patterns(db: Session = Depends(get_db)):
    """
    Analyzes historical incident reports to identify systemic patterns.
    Groups incidents by root cause to find clusters.
    """
    try:
        # Get all closed/resolved incidents with a defined root cause
        incidents = db.query(Incident).filter(Incident.root_cause != "").all()
        
        # Simple clustering by matching root cause strings (in a real advanced setup, this would use embeddings)
        patterns: Dict[str, Dict[str, Any]] = {}
        for inc in incidents:
            key = inc.root_cause.strip()
            if not key:
                continue
            
            if key not in patterns:
                patterns[key] = {
                    "id": f"PAT-{len(patterns)+1}",
                    "title": key,
                    "confidence": 0,
                    "occurrences": 0,
                    "affected_assets": set(),
                    "severity_score": 0
                }
            
            patterns[key]["occurrences"] += 1
            if inc.asset_tag:
                patterns[key]["affected_assets"].add(inc.asset_tag)
                
            # Weight severity
            sev = inc.severity.lower()
            if sev == "critical": patterns[key]["severity_score"] += 4
            elif sev == "high": patterns[key]["severity_score"] += 3
            elif sev == "medium": patterns[key]["severity_score"] += 2
            else: patterns[key]["severity_score"] += 1

        # Format output
        result = []
        for key, p in patterns.items():
            if p["occurrences"] > 1: # Only return actual patterns (occurred more than once)
                # Calculate synthetic confidence based on occurrences and severity
                conf = min(99, 60 + (p["occurrences"] * 5) + p["severity_score"])
                result.append({
                    "id": p["id"],
                    "title": p["title"],
                    "confidence": conf,
                    "occurrences": p["occurrences"],
                    "affected_assets": list(p["affected_assets"]),
                    "preventative_warning": f"Review maintenance schedule for {len(p['affected_assets'])} affected assets to prevent recurrence."
                })
        
        # Sort by highest occurrences
        result.sort(key=lambda x: x["occurrences"], reverse=True)
        return result
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


@router.get("/warnings")
def get_active_warnings(db: Session = Depends(get_db)):
    """
    Evaluates current asset conditions against historical patterns to issue active warnings.
    """
    try:
        # Find assets currently in warning or critical state
        at_risk_assets = db.query(Asset).filter(Asset.status.in_(["warning", "critical"])).all()
        
        warnings = []
        for asset in at_risk_assets:
            # Check if this asset has a history of high severity incidents
            past_incidents = db.query(Incident).filter(
                Incident.asset_tag == asset.tag,
                Incident.severity.in_(["high", "critical"])
            ).count()
            
            if past_incidents > 0 or asset.status == "critical":
                risk_level = "Critical" if asset.status == "critical" else "High"
                warnings.append({
                    "id": f"WARN-{asset.id}",
                    "asset_tag": asset.tag,
                    "asset_name": asset.name,
                    "risk_level": risk_level,
                    "message": f"Historical pattern match: {asset.tag} ({asset.name}) is exhibiting conditions that previously led to {past_incidents} high-severity failures.",
                    "temperature": asset.temperature,
                    "vibration": asset.vibration
                })
                
        return warnings
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@router.get("/stats")
def get_failure_stats(db: Session = Depends(get_db)):
    """
    Returns aggregate stats for the heatmap/charts.
    """
    try:
        total_incidents = db.query(Incident).count()
        critical_incidents = db.query(Incident).filter(Incident.severity == "critical").count()
        
        # Group by asset_tag to get chart data
        asset_counts = db.query(Incident.asset_tag, func.count(Incident.id)).group_by(Incident.asset_tag).all()
        chart_data = [{"name": tag if tag else "Unknown", "incidents": count} for tag, count in asset_counts if tag]
        chart_data.sort(key=lambda x: x["incidents"], reverse=True)
        
        return {
            "total_historical_incidents": total_incidents,
            "critical_failures": critical_incidents,
            "chart_data": chart_data[:10] # Top 10 worst offenders
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}
