import os
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db
from models.domain import PageIndex
from services.ingestion import process_document_pipeline
from services.page_index_service import page_index_service

router = APIRouter()


def serialize_page(page: PageIndex):
    return {
        "id": page.id,
        "document_id": page.document_id,
        "document_name": page.document_name,
        "page_number": page.page_number,
        "section_title": page.section_title,
        "headings": split_csv(page.headings),
        "equipment_ids": split_csv(page.equipment_ids),
        "keywords": split_csv(page.keywords),
        "page_summary": page.summary,
        "summary": page.summary,
        "extracted_text": page.extracted_text,
        "tables": page.tables,
        "images": page.images,
        "chunk_ids": split_csv(page.chunk_ids),
        "embedding_id": page.embedding_id,
        "indexing_status": page.indexing_status,
        "created_at": page.created_at,
    }


def split_csv(value: str):
    return [item.strip() for item in (value or "").split(",") if item.strip()]


@router.get("/")
def list_indexed_pages(
    q: Optional[str] = None,
    document_id: Optional[int] = None,
    equipment: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
):
    page_index_service.sync_legacy_document_pages(db)
    page_index_service.sync_structured_record_pages(db)
    pages, total = page_index_service.list_pages(
        db,
        query=q,
        document_id=document_id,
        equipment=equipment,
        status=status,
        skip=skip,
        limit=min(limit, 500),
    )
    return {"total": total, "data": [serialize_page(page) for page in pages]}


@router.get("/search")
def search_indexed_pages(
    q: str,
    equipment: Optional[str] = None,
    document_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
):
    page_index_service.sync_legacy_document_pages(db)
    page_index_service.sync_structured_record_pages(db)
    pages, total = page_index_service.search_pages(
        db,
        query=q,
        equipment=equipment,
        document_id=document_id,
        skip=skip,
        limit=min(limit, 500),
    )
    return {"total": total, "data": [serialize_page(page) for page in pages]}


@router.get("/files/{source}/{file_path:path}")
def serve_pdf_file(source: str, file_path: str):
    if source == "uploads":
        root = os.path.abspath("uploads")
    elif source == "dataset":
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "IndustrialBrain", "documents"))
    else:
        raise HTTPException(status_code=404, detail="Unknown file source")

    requested = os.path.abspath(os.path.join(root, file_path))
    if not requested.startswith(root) or not os.path.exists(requested):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(requested, media_type="application/pdf")


@router.get("/{page_id}/metadata")
def get_page_metadata(page_id: int, db: Session = Depends(get_db)):
    page = page_index_service.get_page(db, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page index not found")
    return serialize_page(page)


@router.get("/{page_id}/viewer")
def get_page_viewer(page_id: int, db: Session = Depends(get_db)):
    viewer = page_index_service.resolve_pdf_viewer(db, page_id)
    if not viewer:
        raise HTTPException(status_code=404, detail="Page index not found")
    return viewer


@router.post("/documents/{document_id}/reindex")
def reindex_document(document_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    from models.domain import Document

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.file_key:
        doc.status = "processing"
        db.commit()
        # Trigger Celery Task, incremental=False to force re-index
        process_document_pipeline.delay(doc.id, incremental=False)
        return {"document_id": doc.id, "status": "processing", "message": "Full page re-index started via Celery."}
    
    # Fallback to older mechanism if no file_key (e.g. legacy local files not uploaded via storage_service)
    upload_path = os.path.abspath(os.path.join("uploads", doc.title))
    if os.path.exists(upload_path):
        doc.status = "processing"
        db.commit()
        process_document_pipeline.delay(doc.id, incremental=False)
        return {"document_id": doc.id, "status": "processing", "message": "Full page re-index started via Celery."}

    result = page_index_service.reindex_document(db, document_id)
    return {**result, "status": "indexed"}
