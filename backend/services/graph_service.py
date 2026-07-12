"""Database-backed, incremental knowledge-graph projection.

KnowledgeNode and KnowledgeEdge remain the graph store.  ``weight`` is used as
relationship confidence so this projection does not require a schema change.
"""
import json
import re
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from models.domain import Asset, ComplianceRecord, Document, ExpertKnowledge, Incident, KnowledgeEdge, KnowledgeNode, PageIndex


def _safe_json(value: str) -> Dict[str, Any]:
    try:
        return json.loads(value or "{}")
    except (TypeError, ValueError):
        return {}


def _slug(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")


def _tokens(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(v).strip() for v in value if str(v).strip()]
    return [v.strip() for v in re.split(r"[,;|]", str(value)) if v.strip()]


def _asset_key(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


class KnowledgeGraphEngine:
    """Projects real domain records into graph rows without rebuilding the graph."""

    def get_subgraph_for_asset(self, asset_tag: str, db: Optional[Session] = None) -> Dict[str, Any]:
        if not db:
            return {"nodes": [], "edges": []}
        asset = db.query(Asset).filter(Asset.tag == asset_tag).first()
        if not asset:
            return {"nodes": [], "edges": []}
        return self.neighbors(db, f"asset:{asset.id}", limit=100)

    def neighbors(self, db: Session, node_id: str, limit: int = 100) -> Dict[str, Any]:
        edges = db.query(KnowledgeEdge).filter(
            (KnowledgeEdge.source_id == node_id) | (KnowledgeEdge.target_id == node_id)
        ).limit(limit).all()
        ids = {node_id}
        for edge in edges:
            ids.update((edge.source_id, edge.target_id))
        nodes = db.query(KnowledgeNode).filter(KnowledgeNode.node_id.in_(ids)).all() if ids else []
        return self.serialize(nodes, edges)

    @staticmethod
    def serialize(nodes: Iterable[KnowledgeNode], edges: Iterable[KnowledgeEdge]) -> Dict[str, Any]:
        return {
            "nodes": [{"id": node.node_id, "label": node.label, "type": node.node_type,
                       "metadata": _safe_json(node.extra_data)} for node in nodes],
            "edges": [{"source": edge.source_id, "target": edge.target_id,
                       "label": edge.relationship, "weight": edge.weight} for edge in edges],
        }

    def sync_knowledge_graph(self, db: Session, document_id: Optional[int] = None) -> None:
        """Upsert only the changed document projection (or all sources when requested).
        """
        import os
        import csv

        assets = db.query(Asset).all()
        assets_by_tag = {_asset_key(a.tag): a for a in assets if _asset_key(a.tag)}

        def asset_id(raw: Any) -> Optional[str]:
            asset = assets_by_tag.get(_asset_key(raw))
            if not asset:
                return None
            return f"asset:{asset.tag}"

        node_cache: Dict[str, KnowledgeNode] = {}
        edge_cache: Set[Tuple[str, str, str]] = set()

        def node(node_id: str, label: str, node_type: str, metadata: Dict[str, Any], owner: str) -> None:
            ntype = str(node_type or "other").lower().strip()
            current = node_cache.get(node_id) or db.query(KnowledgeNode).filter_by(node_id=node_id).first()
            payload = {**metadata, "graph_managed": True, "owner": owner}
            if current:
                current.label = label or node_id
                current.node_type = ntype
                current.extra_data = json.dumps(payload, default=str)
            else:
                current = KnowledgeNode(
                    node_id=node_id,
                    label=label or node_id,
                    node_type=ntype,
                    extra_data=json.dumps(payload, default=str)
                )
                db.add(current)
            node_cache[node_id] = current

        def edge(source: str, target: str, relationship: str, confidence: float, owner: str) -> None:
            if not source or not target or source == target:
                return
            edge_key = (source, target, relationship)
            if edge_key in edge_cache:
                return
            edge_cache.add(edge_key)
            current = db.query(KnowledgeEdge).filter_by(source_id=source, target_id=target, relationship=relationship).first()
            if current:
                current.weight = max(float(current.weight or 0), confidence)
            else:
                db.add(KnowledgeEdge(source_id=source, target_id=target, relationship=relationship, weight=confidence))

        # Perform cleanup or truncation
        if document_id is None:
            # Clean rebuild: delete all existing KnowledgeNode and KnowledgeEdge records
            # to prevent stale legacy duplicates (like maintenancelog vs maintenance)
            db.query(KnowledgeEdge).delete(synchronize_session=False)
            db.query(KnowledgeNode).delete(synchronize_session=False)
            db.flush()
        else:
            # Incremental doc upload: delete previous nodes/edges owned by this document
            self._remove_document_projection(db, document_id)

        # 1. Assets Sync
        for asset in assets:
            node(
                f"asset:{asset.tag}",
                asset.name or asset.tag,
                "asset",
                {
                    "asset_id": asset.id,
                    "equipment_id": asset.tag,
                    "status": asset.status,
                    "health_score": asset.health_score,
                    "location": asset.location,
                    "asset_type": asset.type,
                },
                f"asset:{asset.tag}"
            )

        # 2. Documents Sync (Manuals, SOPs, Pages, Records)
        documents_query = db.query(Document)
        documents = documents_query.filter(Document.id == document_id).all() if document_id else documents_query.all()
        
        # Build mapping of incident references
        incidents_by_reference: Dict[str, Incident] = {}
        for incident in db.query(Incident).all():
            incidents_by_reference[_slug(incident.id)] = incident
            for reference in re.findall(r"\bINC[-_ ]?\d+\b", incident.title or "", re.I):
                incidents_by_reference[_slug(reference)] = incident

        for doc in documents:
            doc_node = f"document:{doc.id}"
            metadata = _safe_json(doc.metadata_json)
            # Standardize document types (Manual -> manual, SOP -> sop, else -> document)
            doc_type = str(doc.type or "document").lower().strip()
            if "manual" in doc_type:
                doc_type = "manual"
            elif "sop" in doc_type:
                doc_type = "sop"
            else:
                doc_type = "document"
                
            node(
                doc_node,
                doc.title or f"Document {doc.id}",
                doc_type,
                {
                    "document_id": doc.id,
                    "document_type": doc.type,
                    "status": doc.status,
                    "equipment_tags": doc.equipment_tags,
                    "source_documents": [doc.title],
                    **metadata
                },
                f"document:{doc.id}"
            )
            
            # Asset ↔ Document using equipment_tags, metadata tags
            for tag in _tokens(doc.equipment_tags) + _tokens(metadata.get("equipment_id")) + _tokens(metadata.get("asset_id")):
                target = asset_id(tag)
                if target:
                    edge(target, doc_node, "references", 1.0, f"document:{doc.id}")

            # Technician link
            technician = metadata.get("technician") or metadata.get("technician_id") or metadata.get("Technician")
            if technician:
                tech_node = f"person:{_slug(technician)}"
                node(tech_node, str(technician), "person", {"name": technician}, f"person:{_slug(technician)}")
                edge(tech_node, doc_node, "maintained_by", 0.9, f"document:{doc.id}")
                
            # Incident links
            for incident_ref in _tokens(metadata.get("incident_id")) + _tokens(metadata.get("Incident_ID")):
                inc = incidents_by_reference.get(_slug(incident_ref))
                if inc:
                    edge(f"incident:{inc.id}", doc_node, "references", 1.0, f"document:{doc.id}")
                    
            # Document ↔ Document References parsing
            ref_docs = metadata.get("references") or metadata.get("referenced_documents")
            if ref_docs:
                for ref in _tokens(ref_docs):
                    ref_doc = db.query(Document).filter(Document.title.ilike(f"%{ref}%")).first()
                    if ref_doc:
                        edge(doc_node, f"document:{ref_doc.id}", "references", 0.9, f"document:{doc.id}")

            # Pages sync
            pages = db.query(PageIndex).filter(PageIndex.document_id == doc.id).all()
            for page in pages:
                page_node = f"page_index:{page.id}"
                page_type = self._page_type(page, doc)
                node(
                    page_node,
                    f"{doc.title} · p.{page.page_number}",
                    "page_index",
                    {
                        "page_index_id": page.id,
                        "document_id": doc.id,
                        "page_number": page.page_number,
                        "section_title": page.section_title,
                        "source_type": page.source_type,
                        "source_documents": [doc.title],
                    },
                    f"document:{doc.id}"
                )
                edge(doc_node, page_node, "covers", 1.0, f"document:{doc.id}")
                
                # Page links to assets
                for tag in _tokens(page.equipment_ids):
                    target = asset_id(tag)
                    if target:
                        edge(target, page_node, "references", 0.8, f"document:{doc.id}")

                if page_type:
                    record_id = self._record_id(page_type, page)
                    if record_id:
                        ptype = page_type.lower()
                        # Normalize page_type name mapping to match filters list
                        if "maintenance" in ptype:
                            ptype = "maintenance"
                        node(
                            record_id,
                            self._record_label(page_type, page),
                            ptype,
                            {
                                "page_index_id": page.id,
                                "document_id": doc.id,
                                "source_documents": [doc.title],
                                "source_type": page.source_type,
                            },
                            f"document:{doc.id}"
                        )
                        edge(record_id, page_node, "reported_in", 1.0, f"document:{doc.id}")
                        for tag in _tokens(page.equipment_ids):
                            target = asset_id(tag)
                            if target:
                                rel = self._asset_relationship(page_type)
                                edge(target, record_id, rel, 0.85, f"document:{doc.id}")

        # 3. Incidents Sync
        if document_id is None:
            for incident in db.query(Incident).all():
                inc = f"incident:{incident.id}"
                node(
                    inc,
                    incident.title or f"Incident {incident.id}",
                    "incident",
                    {
                        "incident_id": incident.id,
                        "severity": incident.severity,
                        "status": incident.status,
                        "root_cause": incident.root_cause,
                        "corrective_action": incident.corrective_action,
                        "source_documents": [],
                    },
                    f"incident:{incident.id}"
                )
                
                # Incident ↔ Asset
                target = asset_id(incident.asset_tag)
                if target:
                    edge(target, inc, "caused_by", 1.0, f"incident:{incident.id}")
                    
                # Incident ↔ Person (reported_by, assigned_to)
                for name, relation in ((incident.reported_by, "reported_by"), (incident.assigned_to, "assigned_to")):
                    if name:
                        person = f"person:{_slug(name)}"
                        node(person, name, "person", {"name": name}, f"person:{_slug(name)}")
                        edge(person, inc, relation, 1.0, f"incident:{incident.id}")
                        
                # Incident ↔ RCA (linking to root cause page index or text node if available)
                if incident.root_cause:
                    rca_node = f"rca:{incident.id}"
                    node(
                        rca_node,
                        f"RCA: {incident.root_cause[:45]}...",
                        "rca",
                        {"incident_id": incident.id, "root_cause": incident.root_cause},
                        f"incident:{incident.id}"
                    )
                    edge(inc, rca_node, "caused_by", 1.0, f"incident:{incident.id}")
                    if target:
                        edge(target, rca_node, "related_to", 0.9, f"incident:{incident.id}")

            # 4. Compliance Sync
            for record in db.query(ComplianceRecord).all():
                rid = f"compliance:{record.id}"
                node(
                    rid,
                    record.standard or f"Compliance {record.id}",
                    "compliance",
                    {
                        "compliance_id": record.id,
                        "status": record.status,
                        "risk_level": record.risk_level,
                        "standard": record.standard,
                        "section": record.section,
                    },
                    rid
                )
                target = asset_id(record.asset_tag)
                if target:
                    edge(target, rid, "monitored_by", 1.0, rid)

            # 5. Expert Knowledge Sync
            for insight in db.query(ExpertKnowledge).all():
                rid = f"expert:{insight.id}"
                node(
                    rid,
                    insight.condition or f"Expert insight {insight.id}",
                    "expert",
                    {
                        "expert_id": insight.id,
                        "action": insight.action,
                        "confidence": insight.confidence,
                        "source_expert": insight.source_expert,
                    },
                    rid
                )
                target = asset_id(insight.target_asset)
                if target:
                    edge(rid, target, "expert_insight_for", insight.confidence or 0.7, rid)
                if insight.source_expert:
                    person = f"person:{_slug(insight.source_expert)}"
                    node(person, insight.source_expert, "person", {"name": insight.source_expert}, f"person:{_slug(insight.source_expert)}")
                    edge(person, rid, "reported_by", 0.9, rid)

            # 6. Sensors Sync (Read from CSV)
            project_root = "/Users/rahulmahaseth/Desktop/Industrial Brain AI"
            sensor_file = os.path.join(project_root, "IndustrialBrain", "sensor_data", "sensor_readings.csv")
            if os.path.exists(sensor_file):
                with open(sensor_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        asset_tag = row.get("Asset_ID")
                        sensor_name = row.get("Sensor_Name")
                        sensor_id = f"sensor:{asset_tag}_{_slug(sensor_name)}"
                        target = asset_id(asset_tag)
                        if target and sensor_name:
                            node(
                                sensor_id,
                                f"{sensor_name} ({asset_tag})",
                                "sensor",
                                {
                                    "sensor_name": sensor_name,
                                    "asset_tag": asset_tag,
                                    "value": row.get("Value"),
                                    "status": row.get("Status")
                                },
                                f"asset:{asset_tag}"
                            )
                            edge(sensor_id, target, "connected_to", 1.0, f"asset:{asset_tag}")

        db.flush()
        if document_id is None:
            self._remove_orphaned_managed_nodes(db)
        db.commit()

    @staticmethod
    def _page_type(page: PageIndex, doc: Document) -> str:
        source = f"{page.source_type} {doc.type}".lower()
        for name, terms in {
            "maintenance": ("maintenance", "log"),
            "inspection": ("inspection",),
            "qa": ("quality", "qa"),
            "rca": ("rca", "root cause"),
            "sop": ("sop",),
            "manual": ("manual",),
            "compliance": ("compliance", "audit", "certificate")
        }.items():
            if any(term in source for term in terms): return name
        return ""

    @staticmethod
    def _record_id(kind: str, page: PageIndex) -> Optional[str]:
        value = {"maintenance": page.log_id, "inspection": page.inspection_id, "sop": page.sop_id}.get(kind) or str(page.id)
        return f"{kind}:{_slug(value)}" if value else None

    @staticmethod
    def _record_label(kind: str, page: PageIndex) -> str:
        value = {"maintenance": page.log_id, "inspection": page.inspection_id, "sop": page.sop_id}.get(kind)
        return f"{kind.upper()} {value or page.id}"

    @staticmethod
    def _asset_relationship(kind: str) -> str:
        return {
            "maintenance": "maintained_by",
            "inspection": "inspected_by",
            "qa": "monitored_by",
            "rca": "related_to",
            "sop": "references",
            "manual": "references",
            "compliance": "monitored_by"
        }.get(kind, "related_to")

    @staticmethod
    def _link_page_identifiers(node, edge, page: PageIndex, page_node: str, doc: Document, asset_id, incidents_by_reference: Dict[str, Incident]) -> None:
        # Exact external IDs create only relationships to corresponding real records.
        if page.incident_id:
            incident = incidents_by_reference.get(_slug(page.incident_id))
            if incident:
                node(f"incident:{incident.id}", incident.title or f"Incident {incident.id}", "incident", {"incident_id": incident.id, "severity": incident.severity, "status": incident.status}, f"incident:{incident.id}")
                edge(f"incident:{incident.id}", page_node, "reported_in", 1.0, f"document:{doc.id}")
        if page.sop_id:
            sop = f"sop:{_slug(page.sop_id)}"
            node(sop, f"SOP {page.sop_id}", "sop", {"sop_id": page.sop_id, "source_documents": [doc.title]}, f"document:{doc.id}")
            edge(sop, page_node, "references", 1.0, f"document:{doc.id}")

    @staticmethod
    def _remove_document_projection(db: Session, document_id: int) -> None:
        prefix_ids = [f"document:{document_id}"] + [n.node_id for n in db.query(KnowledgeNode).all()
            if _safe_json(n.extra_data).get("owner") == f"document:{document_id}"]
        if prefix_ids:
            db.query(KnowledgeEdge).filter((KnowledgeEdge.source_id.in_(prefix_ids)) | (KnowledgeEdge.target_id.in_(prefix_ids))).delete(synchronize_session=False)
            db.query(KnowledgeNode).filter(KnowledgeNode.node_id.in_(prefix_ids)).delete(synchronize_session=False)

    @staticmethod
    def _remove_orphaned_managed_nodes(db: Session) -> None:
        node_ids = {n.node_id for n in db.query(KnowledgeNode).all()}
        referenced = {x for edge in db.query(KnowledgeEdge).all() for x in (edge.source_id, edge.target_id)}
        for node in db.query(KnowledgeNode).all():
            meta = _safe_json(node.extra_data)
            if meta.get("graph_managed") and node.node_id not in referenced and node.node_type not in {"asset", "document", "incident", "compliance", "expert"}:
                db.delete(node)


graph_engine = KnowledgeGraphEngine()
