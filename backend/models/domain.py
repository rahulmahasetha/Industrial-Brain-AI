from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from datetime import datetime
from database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    type = Column(String)          # Manual, SOP, Incident, Inspection, Compliance, Drawing
    size = Column(String)
    status = Column(String, default="processing")   # processing, processed, failed
    equipment_tags = Column(String, default="")      # comma-separated tags like FM101,AC101
    page_count = Column(Integer, default=0)
    uploaded_by = Column(String, default="System")
    file_key = Column(String, default="")
    storage_provider = Column(String, default="local")
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    tag = Column(String, unique=True, index=True)    # FM101, AC101, UPS101, etc.
    name = Column(String)
    type = Column(String)                             # Filler, Washer, Compressor, Chiller, Conveyor
    location = Column(String, default="")
    health_score = Column(Float, default=100.0)
    status = Column(String, default="operational")    # operational, warning, critical, shutdown
    temperature = Column(Float, default=0.0)
    vibration = Column(Float, default=0.0)
    power_draw = Column(Float, default=0.0)
    lube_oil_level = Column(String, default="Normal")
    last_maintenance = Column(String, default="")
    next_maintenance = Column(String, default="")
    mtbf_hours = Column(Integer, default=0)           # Mean Time Between Failures
    created_at = Column(DateTime, default=datetime.utcnow)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text, default="")
    asset_tag = Column(String, default="")
    severity = Column(String, default="low")          # low, medium, high, critical
    status = Column(String, default="open")           # open, investigating, resolved, closed
    root_cause = Column(Text, default="")
    corrective_action = Column(Text, default="")
    reported_by = Column(String, default="")
    assigned_to = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class ComplianceRecord(Base):
    __tablename__ = "compliance_records"

    id = Column(Integer, primary_key=True, index=True)
    standard = Column(String)                          # ISO 22000, ISO 9001, FSSAI
    section = Column(String, default="")
    requirement = Column(Text)
    status = Column(String, default="compliant")       # compliant, non_compliant, gap, overdue
    risk_level = Column(String, default="low")         # low, medium, high, critical
    asset_tag = Column(String, default="")
    due_date = Column(String, default="")
    last_audit = Column(String, default="")
    notes = Column(Text, default="")
    evidence_data = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)


class ExpertKnowledge(Base):
    __tablename__ = "expert_knowledge"

    id = Column(Integer, primary_key=True, index=True)
    condition = Column(String)
    action = Column(String)
    target_asset = Column(String, default="")
    confidence = Column(Float, default=0.0)
    source_expert = Column(String, default="")
    validated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String)
    content = Column(Text)
    sources = Column(String, default="")    # comma-separated source refs
    confidence = Column(Integer, nullable=True)
    time = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, index=True, nullable=True)
    rating = Column(Integer, nullable=True)
    comment = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String, unique=True, index=True)
    label = Column(String)
    node_type = Column(String, index=True)   # asset, document, person, incident, procedure
    extra_data = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String, index=True)
    target_id = Column(String, index=True)
    relationship = Column(String, index=True)   # documented_in, maintained_by, caused_by, references
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, index=True) # Linked to Document.id
    page_number = Column(Integer)
    section_name = Column(String, default="")
    headings = Column(Text, default="")
    tables = Column(Text, default="")         # Extracted tables info
    images = Column(Text, default="")         # Extracted images info
    equipment_ids = Column(String, default="")
    keywords = Column(String, default="")
    content = Column(Text, default="")        # The actual text content
    created_at = Column(DateTime, default=datetime.utcnow)


class PageIndex(Base):
    __tablename__ = "page_index"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, index=True)
    document_name = Column(String, default="")
    page_number = Column(Integer, index=True)
    section_title = Column(String, default="")
    headings = Column(Text, default="")
    equipment_ids = Column(Text, default="")
    keywords = Column(Text, default="")
    summary = Column(Text, default="")
    extracted_text = Column(Text, default="")
    tables = Column(Text, default="")
    images = Column(Text, default="")
    chunk_ids = Column(Text, default="")
    embedding_id = Column(String, default="")
    procedure_type = Column(String, default="GENERAL")  # STARTUP, SHUTDOWN, MAINTENANCE, EMERGENCY, GENERAL
    indexing_status = Column(String, default="pending")
    log_id = Column(String, index=True, default="")
    incident_id = Column(String, index=True, default="")
    inspection_id = Column(String, index=True, default="")
    sop_id = Column(String, index=True, default="")
    source_type = Column(String, index=True, default="")  # e.g., 'MAINTENANCE_LOG', 'INCIDENT', 'MANUAL'
    created_at = Column(DateTime, default=datetime.utcnow)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(String, index=True)
    page_index_id = Column(Integer, index=True)
    document_id = Column(Integer, index=True)
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="Enterprise User")
    email = Column(String, default="user@enterprise.com")
    role = Column(String, default="Operations Manager")
    employee_id = Column(String, default="EMP-1001")
    photo_url = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
