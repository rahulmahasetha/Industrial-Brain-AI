from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from models.domain import KnowledgeNode, KnowledgeEdge


class KnowledgeGraphEngine:
    def __init__(self):
        self.graph_ready = True

    def add_relationship(self, source_id: str, target_id: str, rel_type: str):
        print(f"Graph: Added {rel_type} from {source_id} to {target_id}")

    def get_subgraph_for_asset(self, asset_tag: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """Query the knowledge graph (backed by the DB in this demo) for an asset's connected nodes."""
        asset_key = f"eq_{asset_tag}"
        graph_keys = [asset_key, asset_tag]
        if not db:
            return {
                "nodes": [{"id": asset_key, "label": asset_tag, "type": "asset"}],
                "edges": []
            }

        edges = db.query(KnowledgeEdge).filter(
            (KnowledgeEdge.source_id.in_(graph_keys)) | (KnowledgeEdge.target_id.in_(graph_keys))
        ).all()

        nodes: List[Dict[str, Any]] = [{"id": asset_key, "label": asset_tag, "type": "asset"}]
        graph_edges: List[Dict[str, Any]] = []
        seen_nodes = {asset_key}

        for edge in edges:
            other_id = edge.target_id if edge.source_id in graph_keys else edge.source_id
            node = db.query(KnowledgeNode).filter(KnowledgeNode.node_id == other_id).first()
            if node and node.node_id not in seen_nodes:
                nodes.append({
                    "id": node.node_id,
                    "label": node.label,
                    "type": node.node_type or "document"
                })
                seen_nodes.add(node.node_id)
            elif other_id not in seen_nodes:
                nodes.append({
                    "id": other_id,
                    "label": other_id,
                    "type": "document" if str(other_id).lower().endswith(".pdf") else "related"
                })
                seen_nodes.add(other_id)
            graph_edges.append({
                "source": edge.source_id,
                "target": other_id,
                "label": edge.relationship or "related_to"
            })

        return {"nodes": nodes, "edges": graph_edges}


graph_engine = KnowledgeGraphEngine()
