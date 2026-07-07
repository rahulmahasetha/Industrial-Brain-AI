from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.domain import ComplianceRecord
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class ComplianceResponse(BaseModel):
    id: int
    standard: str
    section: str
    requirement: str
    status: str
    risk_level: str
    asset_tag: str
    due_date: str
    last_audit: str
    notes: str

    class Config:
        from_attributes = True

class ComplianceCheckRequest(BaseModel):
    document_text: str
    document_type: str = "Unknown"

@router.get("/", response_model=List[ComplianceResponse])
def get_compliance_records(db: Session = Depends(get_db)):
    return db.query(ComplianceRecord).all()

@router.get("/summary")
def get_compliance_summary(db: Session = Depends(get_db)):
    total = db.query(ComplianceRecord).count()
    compliant = db.query(ComplianceRecord).filter(ComplianceRecord.status == "compliant").count()
    non_compliant = db.query(ComplianceRecord).filter(ComplianceRecord.status == "non_compliant").count()
    gaps = db.query(ComplianceRecord).filter(ComplianceRecord.status == "gap").count()
    overdue = db.query(ComplianceRecord).filter(ComplianceRecord.status == "overdue").count()

    return {
        "total": total,
        "compliant": compliant,
        "non_compliant": non_compliant,
        "gaps": gaps,
        "overdue": overdue,
        "compliance_percentage": round((compliant / total) * 100) if total > 0 else 0,
        "critical_items": non_compliant + overdue
    }

@router.post("/check")
def check_document_compliance(request: ComplianceCheckRequest):
    """Run the ComplianceAgent LLM to audit a document against regulatory standards."""
    from agents.compliance_agent import compliance_agent
    result = compliance_agent.check_compliance(request.document_text, request.document_type)
    return result

