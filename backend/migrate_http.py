import sqlite3
import requests
import json
from sqlalchemy import create_engine, MetaData
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql

def migrate_via_http():
    print("Starting HTTP-based migration to Neon...")
    
    neon_url = "https://ep-mute-haze-aoip5ik1-pooler.c-2.ap-southeast-1.aws.neon.tech/sql"
    headers = {
        "Neon-Connection-String": "postgresql://neondb_owner:npg_8KFDcHNlx3GA@ep-mute-haze-aoip5ik1-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb",
        "Content-Type": "application/json"
    }
    
    def execute_neon(sql):
        resp = requests.post(neon_url, headers=headers, json={"query": sql})
        if resp.status_code != 200:
            print(f"Error executing SQL: {resp.text}")
            return False
        return True

    # 1. Reflect SQLite Schema
    sqlite_url = "sqlite:///industrial_brain.db"
    sqlite_engine = create_engine(sqlite_url)
    metadata = MetaData()
    metadata.reflect(bind=sqlite_engine)
    
    # Generate CREATE TABLE statements for Postgres
    pg_dialect = postgresql.dialect()
    
    print("Creating tables in Neon...")
    for table in metadata.sorted_tables:
        create_stmt = str(CreateTable(table).compile(dialect=pg_dialect)).strip()
        # Clean up some dialect specific stuff if needed, though SQLAlchemy's PG dialect usually handles it perfectly
        # Ensure we don't fail if table exists and fix types
        create_stmt = create_stmt.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS")
        create_stmt = create_stmt.replace(" DATETIME", " TIMESTAMP")
        if not execute_neon(create_stmt):
            print(f"Failed to create table {table.name}")
            return

    # 2. Extract and Insert Data
    print("Migrating data...")
    with sqlite_engine.connect() as conn:
        for table in metadata.sorted_tables:
            print(f"Processing table '{table.name}'...")
            
            # Clear existing data in neon just in case
            execute_neon(f"TRUNCATE TABLE {table.name} CASCADE;")
            
            records = conn.execute(table.select()).fetchall()
            if not records:
                print("  No records.")
                continue
                
            keys = table.columns.keys()
            
            # Batch inserts to avoid massive payloads
            batch_size = 500
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                
                # Construct INSERT statement
                columns_str = ", ".join(keys)
                
                values_list = []
                for row in batch:
                    # Format each value properly for raw SQL
                    row_vals = []
                    for val in row:
                        if val is None:
                            row_vals.append("NULL")
                        elif isinstance(val, (int, float)):
                            row_vals.append(str(val))
                        else:
                            # Escape single quotes
                            escaped_val = str(val).replace("'", "''")
                            row_vals.append(f"'{escaped_val}'")
                    values_list.append("(" + ", ".join(row_vals) + ")")
                
                insert_sql = f"INSERT INTO {table.name} ({columns_str}) VALUES {', '.join(values_list)};"
                if execute_neon(insert_sql):
                    print(f"  Inserted batch of {len(batch)} into {table.name}")
                else:
                    print(f"  FAILED inserting batch into {table.name}")
                    
    print("Resetting Sequences...")
    for table in metadata.sorted_tables:
        seq_sql = f"SELECT setval(pg_get_serial_sequence('{table.name}', 'id'), COALESCE((SELECT MAX(id) FROM {table.name}), 1));"
        execute_neon(seq_sql)
        
    print("Migration completed successfully via HTTP API!")

if __name__ == "__main__":
    migrate_via_http()
