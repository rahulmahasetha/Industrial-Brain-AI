import os
import sys
import requests
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

def migrate_to_render_http(render_url: str):
    print(f"Starting HTTP migration to: {render_url}")
    
    # Setup local SQLite engine
    sqlite_url = "sqlite:///industrial_brain.db"
    if not os.path.exists("industrial_brain.db"):
        print("Error: industrial_brain.db not found!")
        sys.exit(1)
        
    sqlite_engine = create_engine(sqlite_url)
    metadata = MetaData()
    metadata.reflect(bind=sqlite_engine)
    
    tables = metadata.sorted_tables
    
    # 1. Clear existing Postgres data
    for table in reversed(tables):
        print(f"Clearing table '{table.name}' in Postgres via HTTP...")
        url = f"{render_url}/api/internal/truncate-table?table_name={table.name}"
        resp = requests.post(url)
        if resp.status_code != 200 or resp.json().get("status") != "success":
            print(f"  Warning: Failed to truncate {table.name}: {resp.text}")

    # 2. Copy data
    with sqlite_engine.connect() as sqlite_conn:
        for table in tables:
            print(f"Copying table '{table.name}'...")
            records = sqlite_conn.execute(table.select()).fetchall()
            
            if not records:
                print("  No records to copy.")
                continue
                
            keys = table.columns.keys()
            batch_size = 500
            total_inserted = 0
            
            for i in range(0, len(records), batch_size):
                batch_records = records[i:i+batch_size]
                # Convert records to dicts (handling memory objects if any)
                batch = []
                for row in batch_records:
                    row_dict = {}
                    for key, val in zip(keys, row):
                        # Convert types to JSON serializable formats
                        if hasattr(val, 'isoformat'):
                            row_dict[key] = val.isoformat()
                        else:
                            row_dict[key] = val
                    batch.append(row_dict)
                
                payload = {
                    "table_name": table.name,
                    "records": batch
                }
                
                url = f"{render_url}/api/internal/migrate-batch"
                resp = requests.post(url, json=payload)
                
                if resp.status_code == 200 and resp.json().get("status") == "success":
                    inserted = resp.json().get("inserted", 0)
                    total_inserted += inserted
                    print(f"  Inserted batch of {inserted} rows...")
                else:
                    print(f"  Error inserting batch: {resp.status_code} - {resp.text}")
                    sys.exit(1)
                    
            print(f"  Total inserted for '{table.name}': {total_inserted}")
            
    # 3. Reset Sequences
    print("Resetting PostgreSQL sequences via HTTP...")
    url = f"{render_url}/api/internal/reset-sequences"
    resp = requests.post(url)
    if resp.status_code == 200 and resp.json().get("status") == "success":
        print("Sequences reset successfully:")
        for r in resp.json().get("results", []):
            print(f"  {r}")
    else:
        print(f"Warning: Failed to reset sequences: {resp.text}")
        
    print("Migration completed successfully via custom Render API!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 migrate_to_render_http.py <RENDER_WEB_SERVICE_URL>")
        print("Example: python3 migrate_to_render_http.py https://industrial-brain-api.onrender.com")
        sys.exit(1)
        
    base_url = sys.argv[1].rstrip("/")
    migrate_to_render_http(base_url)
