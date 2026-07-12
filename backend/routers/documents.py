from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.domain import Document
from pydantic import BaseModel
from typing import List, Dict, Optional
import datetime
import os
import shutil
from services.ingestion import process_document_pipeline
from services.storage_service import storage_service
import uuid

router = APIRouter()

class DocumentCreate(BaseModel):
    title: str
    type: str
    size: str

class DocumentResponse(DocumentCreate):
    id: int
    status: str
    equipment_tags: Optional[str] = ""
    created_at: Optional[datetime.datetime] = None
    
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
def get_documents(q: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Document)
    if q:
        query = query.filter(
            (Document.title.ilike(f"%{q}%")) |
            (Document.type.ilike(f"%{q}%")) |
            (Document.equipment_tags.ilike(f"%{q}%"))
        )
    docs = query.order_by(Document.created_at.desc()).all()
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
    
    # Group counts by display description name
    grouped = {}
    for doc_type, count in type_counts:
        if doc_type:
            metadata = category_metadata.get(doc_type, {
                "icon": "📄",
                "description": doc_type
            })
            name = metadata.get("description", doc_type)
            icon = metadata.get("icon", "📄")
            
            if name in grouped:
                grouped[name]["count"] += count
            else:
                grouped[name] = {
                    "count": count,
                    "icon": icon,
                    "description": name
                }
                
    results = [
        CategoryCount(
            name=name,
            count=data["count"],
            icon=data["icon"],
            description=data["description"]
        )
        for name, data in grouped.items()
    ]
    
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
    doc_type: str = Form("Manual"),
    db: Session = Depends(get_db)
):
    # Use unique filename to avoid collisions
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    
    # Upload to Object Storage abstraction
    file_key = storage_service.upload_file(file.file, unique_filename, file.content_type)
        
    size_str = format_size(file.size or 0)
        
    # Save to DB
    db_doc = Document(
        title=file.filename, 
        type=doc_type, 
        size=size_str, 
        status="processing",
        file_key=file_key,
        storage_provider=os.environ.get("STORAGE_PROVIDER", "local")
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    # Trigger background task. If Celery is not explicitly enabled or fails,
    # run it in FastAPI's background thread directly.
    use_celery = os.environ.get("USE_CELERY", "false").lower() == "true"
    if use_celery:
        try:
            process_document_pipeline.delay(db_doc.id)
            msg = "Document uploaded and processing started via Celery."
        except Exception as e:
            print(f"[documents] Celery enqueue failed: {e}. Falling back to FastAPI BackgroundTasks.")
            background_tasks.add_task(process_document_pipeline, db_doc.id)
            msg = "Document uploaded and processing started via background thread (Celery fallback)."
    else:
        background_tasks.add_task(process_document_pipeline, db_doc.id)
        msg = "Document uploaded and processing started via background thread."
        
    return {"status": "success", "message": msg, "id": db_doc.id}


@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    try:
        # 1. Delete physical file from storage
        if doc.file_key:
            try:
                storage_service.delete_file(doc.file_key)
            except Exception as e:
                print(f"[documents] Failed to delete file {doc.file_key} from storage: {e}")
            
        # 2. Delete database records (Chunks, PageIndex, DocumentPage)
        from models.domain import DocumentChunk, PageIndex, DocumentPage
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        db.query(PageIndex).filter(PageIndex.document_id == document_id).delete()
        db.query(DocumentPage).filter(DocumentPage.document_id == document_id).delete()
        
        # 3. Remove from vector database (if langchain is available)
        from services.ingestion import LANGCHAIN_AVAILABLE, get_chroma_vectorstore
        if LANGCHAIN_AVAILABLE:
            try:
                vectorstore = get_chroma_vectorstore()
                vectorstore.delete(where={"document_id": document_id})
            except Exception as e:
                print(f"[documents] Failed to delete from vector store: {e}")
                
        # 4. Remove from Knowledge Graph
        from services.graph_service import graph_engine
        try:
            graph_engine._remove_document_projection(db, document_id)
        except Exception as e:
            print(f"[documents] Failed to delete Knowledge Graph entities: {e}")
        
        # 5. Delete the Document metadata row
        db.delete(doc)
        db.commit()
        
        return {"status": "success", "message": f"Document '{doc.title}' deleted successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

