import sys
import os
sys.path.append(os.path.join(os.getcwd(), "backend"))

from database import engine, SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("Adding indices...")
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_kn_type ON knowledge_nodes (node_type);"))
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_ke_source ON knowledge_edges (source_id);"))
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_ke_target ON knowledge_edges (target_id);"))
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_ke_rel ON knowledge_edges (relationship);"))
    db.commit()
    print("Done!")
except Exception as e:
    print("Error:", e)
finally:
    db.close()
