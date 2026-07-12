from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, ensure_runtime_schema
import models.domain  # Load models for Base.metadata.create_all
from routers import dashboard, chat, documents, assets, knowledge_graph, auth, compliance, expert, rca, page_index, users, search

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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat Copilot"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(page_index.router, prefix="/api/page-index", tags=["Page Index"])
app.include_router(assets.router, prefix="/api/assets", tags=["Assets"])
app.include_router(knowledge_graph.router, prefix="/api/knowledge-graph", tags=["Knowledge Graph"])
app.include_router(compliance.router, prefix="/api/compliance", tags=["Compliance"])
app.include_router(expert.router, prefix="/api/expert", tags=["Expert Knowledge"])
app.include_router(rca.router, prefix="/api/rca", tags=["Root Cause Analysis"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(search.router)

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "FreshFlow Beverages Knowledge Intelligence"}

