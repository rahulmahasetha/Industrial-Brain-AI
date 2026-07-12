"""
Generate global Metadata catalog (JSON) indexing all generated files.
"""
import os
import json
from dataset_gen.config import BASE_DIR

def generate_metadata():
    print("\n--- Generating Global Metadata Catalog ---")
    
    metadata = {
        "company": "FreshFlow Beverages Pvt. Ltd.",
        "plant": "Pune Production Facility",
        "datasets": {}
    }
    
    for root, dirs, files in os.walk(BASE_DIR):
        if root == BASE_DIR: continue # skip root
        folder = os.path.basename(root)
        metadata["datasets"][folder] = {
            "count": len(files),
            "files": files[:10] + (["..."] if len(files) > 10 else [])
        }
        
    out_path = os.path.join(BASE_DIR, "metadata_catalog.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"  Metadata catalog saved to: {out_path}")

if __name__ == "__main__":
    generate_metadata()
