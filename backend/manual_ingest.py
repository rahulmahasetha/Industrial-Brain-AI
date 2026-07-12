import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import domain as m
from services.page_index_service import page_index_service
from services.chunking_service import chunking_service
from services.ingestion import get_chroma_vectorstore
import PyPDF2
from langchain_core.documents import Document as LangchainDocument
import json

db = SessionLocal()
file_path = "../IndustrialBrain/manuals/Manual_CP102.pdf"
filename = "Manual_CP102.pdf"

# Clean up first
docs = db.query(m.Document).filter(m.Document.title == filename).all()
for doc in docs:
    db.query(m.PageIndex).filter(m.PageIndex.document_id == doc.id).delete()
    db.delete(doc)
db.commit()

db_doc = m.Document(title=filename, type="Manual", size="30 KB", status="processed", equipment_tags="CP102")
db.add(db_doc)
db.commit()
db.refresh(db_doc)

reader = PyPDF2.PdfReader(file_path)
pages_data = []
for p_num, page in enumerate(reader.pages, start=1):
    extracted = page.extract_text()
    if extracted:
        page_index = page_index_service.build_page_record(db=db, doc=db_doc, page_number=p_num, text=extracted)
        pages_data.append({"page_number": p_num, "text": extracted, "page_index_id": page_index.id})

full_text_sample = "\n\n".join(p["text"] for p in pages_data[:10])
extracted_metadata = chunking_service.extract_metadata(full_text_sample, filename)
extracted_metadata["document_id"] = db_doc.id
extracted_metadata["source_file"] = filename
db_doc.type = extracted_metadata.get("document_type", "Manual")

semantic_chunks, toc_data = chunking_service.create_semantic_chunks(pages_data, extracted_metadata)

existing_meta = extracted_metadata.copy()
if "toc" in toc_data:
    existing_meta["toc"] = toc_data["toc"]
db_doc.metadata_json = json.dumps(existing_meta)
db.commit()

langchain_docs = []
for chunk in semantic_chunks:
    langchain_docs.append(LangchainDocument(page_content=chunk["text"], metadata={
        "source": filename, 
        "type": db_doc.type, 
        "document_id": db_doc.id, 
        "equipment": "CP102", 
        "section_name": chunk.get("section_name", ""), 
        "section_number": chunk.get("section_number", ""), 
        "page_start": chunk.get("page_start", 1), 
        "page_end": chunk.get("page_end", 1)
    }))

vectorstore = get_chroma_vectorstore()
vectorstore.add_documents(langchain_docs)
print("Done inserting Manual_CP102.pdf")

