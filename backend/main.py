from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, ensure_runtime_schema
import models.domain  # Load models for Base.metadata.create_all
from routers import dashboard, chat, documents, knowledge_graph, auth, compliance, expert, rca, page_index, users, search, failure_intelligence

# Create DB tables
Base.metadata.create_all(bind=engine)
ensure_runtime_schema()

app = FastAPI(
    title="FreshFlow Beverages Knowledge Intelligence API",
    description="Knowledge Intelligence Platform API for beverage manufacturing and bottling operations",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat Copilot"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(page_index.router, prefix="/api/page-index", tags=["Page Index"])
app.include_router(knowledge_graph.router, prefix="/api/knowledge-graph", tags=["Knowledge Graph"])
app.include_router(compliance.router, prefix="/api/compliance", tags=["Compliance"])
app.include_router(expert.router, prefix="/api/expert", tags=["Expert Knowledge"])
app.include_router(rca.router, prefix="/api/rca", tags=["Root Cause Analysis"])
app.include_router(failure_intelligence.router, prefix="/api/failure-intelligence", tags=["Failure Intelligence"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(search.router)

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "FreshFlow Beverages Knowledge Intelligence"}

from pydantic import BaseModel
from typing import List, Dict, Any
from sqlalchemy import MetaData, text

class MigrationBatch(BaseModel):
    table_name: str
    records: List[Dict[str, Any]]

@app.post("/api/internal/truncate-table")
def truncate_table(table_name: str):
    metadata = MetaData()
    metadata.reflect(bind=engine)
    if table_name not in metadata.tables:
        return {"status": "error", "message": "Table not found"}
    try:
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/internal/migrate-batch")
def migrate_batch(batch: MigrationBatch):
    metadata = MetaData()
    metadata.reflect(bind=engine)
    if batch.table_name not in metadata.tables:
        return {"status": "error", "message": f"Table {batch.table_name} not found"}
        
    table = metadata.tables[batch.table_name]
    try:
        with engine.begin() as conn:
            conn.execute(table.insert(), batch.records)
        return {"status": "success", "inserted": len(batch.records)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/internal/reset-sequences")
def reset_sequences():
    metadata = MetaData()
    metadata.reflect(bind=engine)
    results = []
    try:
        with engine.begin() as conn:
            for table in metadata.sorted_tables:
                try:
                    result = conn.execute(text(f"SELECT MAX(id) FROM {table.name}"))
                    max_id = result.scalar()
                    if max_id is not None:
                        seq_query = f"SELECT setval(pg_get_serial_sequence('{table.name}', 'id'), :max_id)"
                        conn.execute(text(seq_query), {"max_id": max_id})
                        results.append(f"Reset {table.name} to {max_id}")
                except Exception:
                    pass
        return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

