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

@router.post("/auto-audit")
def auto_audit(db: Session = Depends(get_db)):
    """Run the massive ComplianceAgent AI Auto Audit across documents and return forensic data."""
    from agents.compliance_agent import compliance_agent
    # Trigger the agent (mocking a generic global check for now)
    result = compliance_agent.check_compliance("GLOBAL AUDIT TRIGGERED", "Global Audit")
    return result

class ExplainRequest(BaseModel):
    standard: str
    clause: str

@router.post("/explain")
def explain_clause(request: ExplainRequest):
    """Explain a specific regulatory clause."""
    from agents.compliance_agent import compliance_agent
    explanation = compliance_agent.explain_clause(request.standard, request.clause)
    return {"explanation": explanation}

class ChatGapRequest(BaseModel):
    gap_details: str
    query: str

@router.post("/chat")
def chat_compliance_gap(request: ChatGapRequest):
    """Answer questions about a specific compliance gap."""
    from agents.compliance_agent import compliance_agent
    response = compliance_agent.chat_gap(request.gap_details, request.query)
    return {"response": response}

@router.get("/heatmap")
def get_compliance_heatmap(db: Session = Depends(get_db)):
    """Return asset-based compliance heatmap data."""
    try:
        records = db.query(ComplianceRecord).filter(ComplianceRecord.asset_tag != "").all()
        
        heatmap_data = {}
        for r in records:
            if r.asset_tag not in heatmap_data:
                heatmap_data[r.asset_tag] = {"asset_tag": r.asset_tag, "compliant": 0, "non_compliant": 0, "gaps": 0, "critical_risks": 0}
            
            if r.status == "compliant":
                heatmap_data[r.asset_tag]["compliant"] += 1
            elif r.status == "non_compliant":
                heatmap_data[r.asset_tag]["non_compliant"] += 1
            elif r.status == "gap":
                heatmap_data[r.asset_tag]["gaps"] += 1
                
            if r.risk_level in ["high", "critical"]:
                heatmap_data[r.asset_tag]["critical_risks"] += 1
                
        return list(heatmap_data.values())
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

