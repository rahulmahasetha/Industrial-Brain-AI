from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.domain import KnowledgeNode, KnowledgeEdge

router = APIRouter()

@router.get("/")
def get_knowledge_graph(db: Session = Depends(get_db)):
    nodes = db.query(KnowledgeNode).all()
    edges = db.query(KnowledgeEdge).all()

    return {
        "nodes": [
            {"id": n.node_id, "label": n.label, "type": n.node_type}
            for n in nodes
        ],
        "edges": [
            {"source": e.source_id, "target": e.target_id, "label": e.relationship}
            for e in edges
        ]
    }
