from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import get_db
from models.domain import Asset, Document, Incident

router = APIRouter(prefix="/api/search", tags=["Global Search"])

@router.get("")
def global_search(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """
    Perform a global keyword search across Assets, Documents, and Incidents.
    Uses basic SQL ILIKE without invoking the LLM.
    """
    search_term = f"%{q}%"
    results = []

    # 1. Search Assets
    assets = db.query(Asset).filter(
        or_(
            Asset.tag.ilike(search_term),
            Asset.name.ilike(search_term),
            Asset.type.ilike(search_term)
        )
    ).limit(5).all()

    for a in assets:
        results.append({
            "id": a.id,
            "result_type": "asset",
            "title": a.name,
            "subtitle": f"Tag: {a.tag} | Type: {a.type}",
            "link": f"/dashboard" # Frontend will handle navigation
        })

    # 2. Search Documents
    documents = db.query(Document).filter(
        or_(
            Document.title.ilike(search_term),
            Document.type.ilike(search_term),
            Document.equipment_tags.ilike(search_term)
        )
    ).limit(5).all()

    for d in documents:
        results.append({
            "id": d.id,
            "result_type": "document",
            "title": d.title,
            "subtitle": f"Type: {d.type} | Size: {d.size}",
            "link": f"/documents"
        })

    # 3. Search Incidents
    incidents = db.query(Incident).filter(
        or_(
            Incident.title.ilike(search_term),
            Incident.asset_tag.ilike(search_term),
            Incident.description.ilike(search_term)
        )
    ).limit(5).all()

    for i in incidents:
        results.append({
            "id": i.id,
            "result_type": "incident",
            "title": i.title,
            "subtitle": f"Status: {i.status} | Severity: {i.severity}",
            "link": f"/rca"
        })

    return results
