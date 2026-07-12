"""
Generate Knowledge Graph mappings (JSON) for FreshFlow Beverages.
Defines relationships: (Manual)-[COVERS]->(Asset), (Maintenance Log)-[LOGGED_ON]->(Asset)
"""
import os
import json
import csv
from dataset_gen.config import BASE_DIR, ALL_EQUIPMENT

def generate_knowledge_graph():
    print("\n--- Generating Knowledge Graph Mappings ---")
    os.makedirs(os.path.join(BASE_DIR, "knowledge_graph"), exist_ok=True)
    
    nodes = []
    edges = []
    
    # Asset Nodes
    for eq in ALL_EQUIPMENT:
        nodes.append({"id": eq["id"], "label": "Asset", "name": eq["name"], "dept": eq["dept"]})
        
        # Manual Edges
        manual_id = f"MAN-{eq['id']}-001"
        nodes.append({"id": manual_id, "label": "Manual", "name": f"Manual for {eq['name']}"})
        edges.append({"source": manual_id, "target": eq["id"], "type": "COVERS_EQUIPMENT"})

    # Parse Maintenance Logs to create edges
    ml_path = os.path.join(BASE_DIR, "maintenance_logs", "maintenance_logs.csv")
    if os.path.exists(ml_path):
        with open(ml_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ml_id = row["Log_ID"]
                asset = row["Asset_ID"]
                sop = row.get("SOP_Reference")
                nodes.append({"id": ml_id, "label": "MaintenanceLog"})
                edges.append({"source": ml_id, "target": asset, "type": "LOGGED_AGAINST_ASSET"})
                
                if sop:
                    if not any(n["id"] == sop for n in nodes):
                        nodes.append({"id": sop, "label": "SOP"})
                    edges.append({"source": ml_id, "target": sop, "type": "FOLLOWED_SOP"})

    graph = {
        "nodes": nodes,
        "edges": edges
    }
    
    out_path = os.path.join(BASE_DIR, "knowledge_graph", "graph_relationships.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)
        
    print(f"  Generated {len(nodes)} nodes and {len(edges)} edges at: {out_path}")

if __name__ == "__main__":
    generate_knowledge_graph()
