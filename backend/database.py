from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "industrial_brain.db")

# Default to SQLite if DATABASE_URL is missing
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 30})
else:
    # PostgreSQL connection (no check_same_thread needed)
    engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_runtime_schema():
    inspector = inspect(engine)
    if "page_index" not in inspector.get_table_names():
        return

    page_index_columns = {column["name"] for column in inspector.get_columns("page_index")}
    if "procedure_type" not in page_index_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE page_index ADD COLUMN procedure_type VARCHAR DEFAULT 'GENERAL'"))

    document_columns = {column["name"] for column in inspector.get_columns("documents")} if "documents" in inspector.get_table_names() else set()
    if "metadata_json" not in document_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE documents ADD COLUMN metadata_json TEXT DEFAULT '{}'"))

    if "file_key" not in document_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE documents ADD COLUMN file_key VARCHAR DEFAULT ''"))
            
    if "storage_provider" not in document_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE documents ADD COLUMN storage_provider VARCHAR DEFAULT 'local'"))
