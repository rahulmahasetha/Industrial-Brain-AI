from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.domain import Document, Asset, Incident, ComplianceRecord, PageIndex, KnowledgeNode, KnowledgeEdge

router = APIRouter()

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_assets = db.query(Asset).count()
    attention_assets = db.query(Asset).filter(Asset.status.in_(["warning", "critical"])).count()
    total_docs = db.query(Document).count()
    total_pages = db.query(PageIndex).count()
    page_rows = db.query(PageIndex.chunk_ids).all()
    total_chunks = sum(len([c for c in (row[0] or "").split(",") if c.strip()]) for row in page_rows)
    total_graph_nodes = db.query(KnowledgeNode).count()
    total_relationships = db.query(KnowledgeEdge).count()
    indexed_docs = db.query(Document).filter(Document.status == "processed").count()
    pending_docs = db.query(Document).filter(Document.status.in_(["processing", "pending"])).count()
    
    # Calculate compliance readiness
    total_compliance = db.query(ComplianceRecord).count()
    compliant_count = db.query(ComplianceRecord).filter(ComplianceRecord.status == "compliant").count()
    compliance_pct = round((compliant_count / total_compliance) * 100) if total_compliance > 0 else 0

    # Calculate brain score from asset health average
    avg_health = db.query(func.avg(Asset.health_score)).scalar() or 0
    brain_score = round(avg_health)
    
    # Additional intelligence metrics
    from models.domain import ExpertKnowledge
    total_expert_rules = db.query(ExpertKnowledge).count()
    active_incidents = db.query(Incident).filter(Incident.status.in_(["open", "in progress", "investigating"])).count()

    return {
        "brain_score": brain_score,
        "monitored_assets": total_assets,
        "assets_requiring_attention": attention_assets,
        "knowledge_documents": total_docs,
        "total_documents": total_docs,
        "total_indexed_pages": total_pages,
        "total_chunks": total_chunks,
        "total_knowledge_graph_nodes": total_graph_nodes,
        "total_relationships": total_relationships,
        "indexed_documents": indexed_docs,
        "pending_documents": pending_docs,
        "compliance_readiness": compliance_pct,
        "total_expert_rules": total_expert_rules,
        "active_incidents": active_incidents
    }

@router.get("/incidents/recent")
def get_recent_incidents(db: Session = Depends(get_db)):
    incidents = db.query(Incident).order_by(Incident.created_at.desc()).limit(10).all()
    results = []
    for inc in incidents:
        results.append({
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
        })
    return results

@router.get("/lessons-learned")
def get_lessons_learned(db: Session = Depends(get_db)):
    """Analyze recent incidents to extract systemic patterns."""
    from services.lessons_learned_service import lessons_learned_service
    return lessons_learned_service.analyze_patterns(db)
