from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.domain import Asset
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class AssetResponse(BaseModel):
    id: int
    tag: str
    name: str
    type: str
    location: str
    health_score: float
    status: str
    temperature: float
    vibration: float
    power_draw: float
    lube_oil_level: str
    last_maintenance: str
    next_maintenance: str
    mtbf_hours: int

    class Config:
        from_attributes = True

@router.get("/", response_model=List[AssetResponse])
def get_assets(db: Session = Depends(get_db)):
    return db.query(Asset).order_by(Asset.health_score.asc()).all()

@router.get("/{asset_tag}")
def get_asset_detail(asset_tag: str, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.tag == asset_tag).first()
    if not asset:
        return {"error": "Asset not found"}
    return {
        "id": asset.id,
        "tag": asset.tag,
        "name": asset.name,
        "type": asset.type,
        "location": asset.location,
        "health_score": asset.health_score,
        "status": asset.status,
        "temperature": asset.temperature,
        "vibration": asset.vibration,
        "power_draw": asset.power_draw,
        "lube_oil_level": asset.lube_oil_level,
        "last_maintenance": asset.last_maintenance,
        "next_maintenance": asset.next_maintenance,
        "mtbf_hours": asset.mtbf_hours,
    }

@router.get("/{asset_tag}/health")
def get_asset_health(asset_tag: str, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.tag == asset_tag).first()
    if not asset:
        return {"error": "Asset not found"}
    return {
        "asset_id": asset.tag,
        "name": asset.name,
        "health_score": asset.health_score,
        "status": asset.status,
        "temperature": asset.temperature,
        "vibration": asset.vibration,
        "power_draw": asset.power_draw,
        "lube_oil_level": asset.lube_oil_level,
        "last_maintenance": asset.last_maintenance,
        "next_maintenance": asset.next_maintenance,
        "mtbf_hours": asset.mtbf_hours,
    }

@router.get("/{asset_tag}/advisory")
def get_asset_advisory(asset_tag: str, db: Session = Depends(get_db)):
    """Generate a natural language predictive maintenance advisory for the asset."""
    from agents.predictive_maintenance import predictive_maintenance_agent
    result = predictive_maintenance_agent.generate_advisory(asset_tag, db)
    return result
