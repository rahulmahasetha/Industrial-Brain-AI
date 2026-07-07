from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.domain import Document
from pydantic import BaseModel
from typing import List, Dict
import datetime
import os
import shutil
from services.ingestion import process_document_pipeline

router = APIRouter()

class DocumentCreate(BaseModel):
    title: str
    type: str
    size: str

class DocumentResponse(DocumentCreate):
    id: int
    status: str
    
    class Config:
        from_attributes = True

class DocumentStats(BaseModel):
    total_documents: int
    by_category: Dict[str, int]

class CategoryCount(BaseModel):
    name: str
    count: int
    icon: str
    description: str

@router.get("/", response_model=List[DocumentResponse])
def get_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return docs

@router.get("/stats/category-counts", response_model=List[CategoryCount])
def get_document_statistics(db: Session = Depends(get_db)):
    """Get document counts by category with metadata for dashboard cards"""
    
    # Map of document types to display metadata
    category_metadata = {
        "Manual": {"icon": "📘", "description": "Equipment Manuals"},
        "Equipment Manual": {"icon": "📘", "description": "Equipment Manuals"},
        "SOP": {"icon": "📋", "description": "Standard Operating Procedures"},
        "SOP Document": {"icon": "📋", "description": "Standard Operating Procedures"},
        "Maintenance Log": {"icon": "🔧", "description": "Maintenance Records"},
        "Incident Report": {"icon": "⚠️", "description": "Safety & Incidents"},
        "Inspection Report": {"icon": "🔍", "description": "Inspection Records"},
        "Quality Report": {"icon": "📊", "description": "Quality Assurance"},
        "QA Record": {"icon": "📊", "description": "Quality Assurance"},
        "Compliance Document": {"icon": "🛡️", "description": "Compliance & Standards"},
        "Compliance": {"icon": "🛡️", "description": "Compliance & Standards"},
        "Expert Note": {"icon": "🧠", "description": "Expert Knowledge"},
        "Expert Notes": {"icon": "🧠", "description": "Expert Knowledge"},
        "Training Manual": {"icon": "📚", "description": "Training Materials"},
        "Training": {"icon": "📚", "description": "Training Materials"},
        "RCA Report": {"icon": "🔍", "description": "Root Cause Analysis"},
    }
    
    # Query counts by document type
    type_counts = db.query(Document.type, func.count(Document.id)).group_by(Document.type).all()
    
    results = []
    for doc_type, count in type_counts:
        if doc_type:
            metadata = category_metadata.get(doc_type, {
                "icon": "📄",
                "description": doc_type
            })
            results.append(CategoryCount(
                name=metadata.get("description", doc_type),
                count=count,
                icon=metadata.get("icon", "📄"),
                description=metadata.get("description", doc_type)
            ))
    
    # Sort by count descending for better visualization
    results.sort(key=lambda x: x.count, reverse=True)
    
    return results

def format_size(size_in_bytes):
    if size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    return f"{size_in_bytes / (1024 * 1024):.1f} MB"

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_type: str = "Manual",
    db: Session = Depends(get_db)
):
    # Ensure uploads directory exists
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{file.filename}"
    
    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    size_str = format_size(os.path.getsize(file_path))
        
    # Save to DB
    db_doc = Document(title=file.filename, type=doc_type, size=size_str, status="processing")
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    # Trigger background task
    background_tasks.add_task(process_document_pipeline, db_doc.id, file_path)
    
    return {"status": "success", "message": "Document uploaded and processing started.", "id": db_doc.id}

