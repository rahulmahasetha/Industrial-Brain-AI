from collections import Counter
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import get_db
from models.domain import KnowledgeEdge, KnowledgeNode
from services.graph_service import graph_engine

router = APIRouter()


@router.get("/")
def get_knowledge_graph(
    db: Session = Depends(get_db),
    # Omitted parameters retain the existing full-graph API response.
    limit: Optional[int] = Query(None, ge=1, le=1000),
    node_types: Optional[str] = None,
    q: Optional[str] = None,
):
    query = db.query(KnowledgeNode)
    if node_types:
        query = query.filter(KnowledgeNode.node_type.in_([x.strip().lower() for x in node_types.split(",") if x.strip()]))
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(or_(KnowledgeNode.node_id.ilike(term), KnowledgeNode.label.ilike(term)))
    if limit and not q and not node_types:
        # Load a representative sample of roots of EVERY type present in the database
        # to ensure all types are visible in the filter checklist, then fetch their adjacent neighbors.
        all_db_types = [r[0] for r in db.query(KnowledgeNode.node_type).distinct().all() if r[0]]
        
        # We want to distribute the limit: 50% roots of various types, 50% neighbors
        roots_budget = max(10, int(limit * 0.5))
        neighbors_budget = limit - roots_budget
        
        per_type_limit = max(1, roots_budget // len(all_db_types)) if all_db_types else roots_budget
        
        roots = []
        for t in all_db_types:
            roots += db.query(KnowledgeNode).filter(KnowledgeNode.node_type == t).order_by(KnowledgeNode.created_at.desc()).limit(per_type_limit).all()
            
        roots = roots[:roots_budget]
        root_ids = [node.node_id for node in roots] or [""]
        
        # Fetch adjacent edges
        adjacent = db.query(KnowledgeEdge).filter(or_(KnowledgeEdge.source_id.in_(root_ids), KnowledgeEdge.target_id.in_(root_ids))).limit(neighbors_budget * 4).all()
        
        neighbor_ids = [edge.target_id if edge.source_id in root_ids else edge.source_id for edge in adjacent]
        # De-duplicate neighbors
        neighbor_ids = list(set(neighbor_ids) - set(root_ids))
        
        neighbors = db.query(KnowledgeNode).filter(KnowledgeNode.node_id.in_(neighbor_ids)).order_by(KnowledgeNode.created_at.desc()).limit(neighbors_budget).all() if neighbor_ids else []
        
        nodes = roots + neighbors
    else:
        nodes = query.order_by(KnowledgeNode.created_at.desc()).limit(limit).all() if limit else query.all()
    ids = [node.node_id for node in nodes]
    edges = db.query(KnowledgeEdge).filter(KnowledgeEdge.source_id.in_(ids), KnowledgeEdge.target_id.in_(ids)).all() if ids else []
    
    warning_msg = None
    if ids and not edges:
        import logging
        warning_msg = "Knowledge Graph contains 0 relationships. Please verify that the ingestion and sync pipelines have executed correctly."
        logging.warning(warning_msg)

    result = graph_engine.serialize(nodes, edges)
    result["total_nodes"] = db.query(KnowledgeNode).count()
    result["total_relationships"] = db.query(KnowledgeEdge).count()
    result["partial"] = limit is not None
    if warning_msg:
        result["warning"] = warning_msg
    return result


@router.get("/neighbors/{node_id}")
def get_neighbors(node_id: str, db: Session = Depends(get_db), limit: int = Query(100, ge=1, le=500)):
    """Fetch an expandable local subgraph without transferring the entire graph."""
    return graph_engine.neighbors(db, node_id, limit)


@router.get("/stats")
def graph_stats(db: Session = Depends(get_db)):
    nodes = db.query(KnowledgeNode).all()
    return {
        "total_nodes": len(nodes),
        "total_relationships": db.query(KnowledgeEdge).count(),
        "by_type": dict(Counter((node.node_type or "unknown").lower() for node in nodes)),
    }
