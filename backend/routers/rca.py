from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.domain import Incident
from pydantic import BaseModel
from typing import List
from agents.rca_agent import rca_agent

router = APIRouter()

class RCARequest(BaseModel):
    description: str
    asset_tag: str = ""

@router.get("/incidents")
def get_incidents(db: Session = Depends(get_db)):
    incidents = db.query(Incident).order_by(Incident.created_at.desc()).all()
    return [{
        "id": inc.id,
        "title": inc.title,
        "description": inc.description,
        "asset_tag": inc.asset_tag,
        "severity": inc.severity,
        "status": inc.status,
        "root_cause": inc.root_cause,
        "corrective_action": inc.corrective_action,
        "reported_by": inc.reported_by,
        "assigned_to": inc.assigned_to,
    } for inc in incidents]

@router.post("/analyze")
def analyze_root_cause(request: RCARequest):
    result = rca_agent.analyze_anomaly(request.description, request.asset_tag)
    return result

