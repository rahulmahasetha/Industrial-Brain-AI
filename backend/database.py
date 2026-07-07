from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./industrial_brain.db"
# Use PostgreSQL in production:
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 30}
)
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
