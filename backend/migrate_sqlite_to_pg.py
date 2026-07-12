import os
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker

def migrate():
    print("Starting migration from SQLite to PostgreSQL...")
    
    # 1. Setup Engines
    sqlite_url = "sqlite:///industrial_brain.db"
    sqlite_engine = create_engine(sqlite_url)
    
    pg_url = "postgresql://neondb_owner:npg_8KFDcHNlx3GA@ep-mute-haze-aoip5ik1-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
    pg_engine = create_engine(pg_url)
    
    # 2. Reflect SQLite schema
    metadata = MetaData()
    metadata.reflect(bind=sqlite_engine)
    
    # 3. Create tables in Postgres (if missing)
    metadata.create_all(bind=pg_engine)
    
    tables = metadata.sorted_tables
    
    # 4. Clear existing Postgres data
    with pg_engine.begin() as pg_conn:
        for table in reversed(tables):
            print(f"Clearing table '{table.name}' in Postgres...")
            pg_conn.execute(table.delete())
            
    # 5. Copy data
    with sqlite_engine.connect() as sqlite_conn:
        for table in tables:
            print(f"Copying table '{table.name}'...")
            records = sqlite_conn.execute(table.select()).fetchall()
            
            if not records:
                print("  No records to copy.")
                continue
                
            keys = table.columns.keys()
            
            # Use chunks of 1000 for insertion
            batch_size = 1000
            total_inserted = 0
            
            with pg_engine.begin() as pg_conn:
                for i in range(0, len(records), batch_size):
                    batch_records = records[i:i+batch_size]
                    # Convert to list of dicts
                    batch = [dict(zip(keys, row)) for row in batch_records]
                    pg_conn.execute(table.insert(), batch)
                    total_inserted += len(batch)
                    
            print(f"  Inserted {total_inserted} rows.")
            
    # 6. Reset Primary Key Sequences (for PostgreSQL serial auto-increment compatibility)
    print("Resetting PostgreSQL sequences...")
    with pg_engine.begin() as pg_conn:
        for table in tables:
            try:
                result = pg_conn.execute(text(f"SELECT MAX(id) FROM {table.name}"))
                max_id = result.scalar()
                if max_id is not None:
                    seq_query = f"SELECT setval(pg_get_serial_sequence('{table.name}', 'id'), :max_id)"
                    pg_conn.execute(text(seq_query), {"max_id": max_id})
                    print(f"  Reset sequence for '{table.name}' to max ID {max_id}")
            except Exception as e:
                # Ignore if driver doesn't support pg_get_serial_sequence
                pass
            
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()

