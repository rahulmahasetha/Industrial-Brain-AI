from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.domain import ExpertKnowledge
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class ExpertKnowledgeResponse(BaseModel):
    id: int
    condition: str
    action: str
    target_asset: str
    confidence: float
    source_expert: str
    validated: bool

    class Config:
        from_attributes = True

class ExpertKnowledgeCreate(BaseModel):
    condition: str
    action: str
    target_asset: str = ""
    confidence: float = 0.0
    source_expert: str = ""

class ExpertExtractRequest(BaseModel):
    text: str
    source_id: str = "Unknown"
    asset_tag: str = ""

@router.get("/", response_model=List[ExpertKnowledgeResponse])
def get_expert_knowledge(db: Session = Depends(get_db)):
    return db.query(ExpertKnowledge).order_by(ExpertKnowledge.confidence.desc()).all()

@router.post("/")
def add_expert_knowledge(entry: ExpertKnowledgeCreate, db: Session = Depends(get_db)):
    db_entry = ExpertKnowledge(
        condition=entry.condition,
        action=entry.action,
        target_asset=entry.target_asset,
        confidence=entry.confidence,
        source_expert=entry.source_expert,
        validated=False
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return {"status": "success", "id": db_entry.id}

@router.post("/extract")
def extract_expert_knowledge(request: ExpertExtractRequest):
    """Use the ExpertKnowledgeAgent LLM to extract structured Condition-Action-Asset triples from text."""
    from agents.compliance_agent import expert_agent
    result = expert_agent.extract_knowledge(request.text, request.source_id, request.asset_tag)
    return result


