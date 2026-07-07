import json
import os
import re
from datetime import datetime
from sqlalchemy.orm import Session
from models.domain import Document, DocumentPage, KnowledgeNode, KnowledgeEdge, PageIndex
from database import SessionLocal
from services.page_index_service import (
    extract_equipment_ids,
    page_index_service,
    split_page_into_smart_chunks,
)
from services.cache_service import cache_service
from dotenv import load_dotenv
import traceback

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Optional imports handled carefully for the demo
try:
    from llama_parse import LlamaParse
except ImportError:
    LlamaParse = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import fitz
except ImportError:
    fitz = None

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None

try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from langchain_chroma import Chroma
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document as LangchainDocument
    LANGCHAIN_AVAILABLE = True
except ImportError:
    GoogleGenerativeAIEmbeddings = None
    Chroma = None
    RecursiveCharacterTextSplitter = None
    LangchainDocument = None
    LANGCHAIN_AVAILABLE = False
    print("[ingestion] LangChain/Chroma not fully installed — vector features disabled.")

def get_chroma_vectorstore():
    if not LANGCHAIN_AVAILABLE:
        raise RuntimeError("LangChain/Chroma dependencies not installed.")
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set — cannot create embeddings.")

    embedding_model = os.environ.get("GOOGLE_EMBEDDING_MODEL", "gemini-embedding-001")
    embedding_kwargs = {}
    embedding_dim = os.environ.get("GOOGLE_EMBEDDING_DIM")
    if embedding_dim:
        try:
            embedding_kwargs["output_dimensionality"] = int(embedding_dim)
        except ValueError:
            print(f"[ingestion] Invalid GOOGLE_EMBEDDING_DIM: {embedding_dim}")

    if embedding_kwargs:
        embeddings = GoogleGenerativeAIEmbeddings(model=embedding_model, **embedding_kwargs)
    else:
        embeddings = GoogleGenerativeAIEmbeddings(model=embedding_model)

    persist_dir = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
    return Chroma(persist_directory=persist_dir, embedding_function=embeddings, collection_name="industrial_docs")

def process_document_pipeline(document_id: int, file_path: str):
    """
    Background task to process the uploaded document.
    """
    db = SessionLocal()
    doc = db.query(Document).filter(Document.id == document_id).first()
    
    if not doc:
        db.close()
        return

    try:
        print(f"Starting processing for document {doc.title}")
        db.query(PageIndex).filter(PageIndex.document_id == doc.id).delete()
        db.query(DocumentPage).filter(DocumentPage.document_id == doc.id).delete()
        
        # 1. Document Parsing (LlamaParse)
        pages = []
        if LlamaParse:
            try:
                parser = LlamaParse(
                    result_type="markdown",  # Getting markdown is great for structure
                    verbose=True
                )
                parsed_docs = parser.load_data(file_path)
                for d in parsed_docs:
                    page_num = d.metadata.get("page_label", 1) if hasattr(d, 'metadata') else 1
                    pages.append({
                        "page_number": int(page_num) if str(page_num).isdigit() else 1,
                        "text": d.text
                    })
            except Exception as e:
                print(f"[ingestion] Document parser unavailable for {doc.title}: {e}")

        if not pages:
            if fitz and pytesseract and Image and file_path.lower().endswith('.pdf'):
                try:
                    raw_text = []
                    doc_pdf = fitz.open(file_path)
                    for page_num in range(len(doc_pdf)):
                        pix = doc_pdf[page_num].get_pixmap()
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        raw_text.append(pytesseract.image_to_string(img))
                    pages = [{"page_number": i + 1, "text": text} for i, text in enumerate(raw_text) if text.strip()]
                except Exception as e:
                    print(f"[ingestion] OCR failed for {doc.title}: {e}")
            if not pages and PyPDF2 and file_path.lower().endswith('.pdf'):
                try:
                    reader = PyPDF2.PdfReader(file_path)
                    pdf_text = []
                    for i, page in enumerate(reader.pages):
                        pdf_text.append(page.extract_text() or "")
                    pages = [{"page_number": i + 1, "text": text} for i, text in enumerate(pdf_text) if text.strip()]
                except Exception as e:
                    print(f"[ingestion] PDF text extraction failed for {doc.title}: {e}")
            if not pages and (file_path.lower().endswith('.csv') or file_path.lower().endswith('.xlsx') or file_path.lower().endswith('.xls')):
                try:
                    import pandas as pd
                    if file_path.lower().endswith('.csv'):
                        df = pd.read_csv(file_path)
                    else:
                        df = pd.read_excel(file_path)
                    # Convert to markdown or string format for the pages
                    text = df.to_markdown(index=False)
                    pages = [{"page_number": 1, "text": text}]
                except Exception as e:
                    print(f"[ingestion] Spreadsheet text extraction failed for {doc.title}: {e}")
            if not pages:
                raw_text = f"Document metadata captured for {doc.title}. Detailed page text is not available yet."
                pages = [{"page_number": 1, "text": raw_text}]

        doc.page_count = len(pages)
        
        all_equipment = set()
        
        langchain_docs = []
        
        # 2. Page Indexing & Metadata Extraction
        for page in pages:
            text = page["text"]
            
            # Extract Headings (Markdown headers)
            headings = re.findall(r'^#+\s+(.*)$', text, re.MULTILINE)
            section_name = headings[0] if headings else ""
            
            # Extract Tables (Markdown tables)
            has_table = "|" in text and "-|-" in text
            
            # Extract Images (Markdown image links)
            has_image = "![" in text
            
            # Extract Equipment IDs
            equip_ids = extract_equipment_ids(text)
            all_equipment.update(equip_ids)
            
            # Keywords (Dummy logic for now: longest words)
            words = [w for w in re.findall(r'\b\w+\b', text) if len(w) > 6]
            keywords = list(set(words))[:5]
            
            # Save legacy page row for existing callers.
            db_page = DocumentPage(
                document_id=doc.id,
                page_number=page["page_number"],
                section_name=section_name,
                headings=",".join(headings),
                tables="Yes" if has_table else "No",
                images="Yes" if has_image else "No",
                equipment_ids=",".join(equip_ids),
                keywords=",".join(keywords),
                content=text
            )
            db.add(db_page)

            page_index = page_index_service.build_page_record(db, doc, page["page_number"], text)
            
            if LANGCHAIN_AVAILABLE:
                for chunk in split_page_into_smart_chunks(text, page_index.id):
                    langchain_docs.append(
                        LangchainDocument(
                            page_content=chunk["text"],
                            metadata={
                                "document_id": doc.id,
                                "document_name": doc.title,
                                "title": doc.title,
                                "page_index_id": page_index.id,
                                "page_number": page["page_number"],
                                "section_title": page_index.section_title,
                                "section_name": page_index.section_title,
                                "equipment": ",".join(equip_ids),
                                "keywords": page_index.keywords,
                                "chunk_id": chunk["id"],
                                "procedure_type": page_index.procedure_type,
                            }
                        )
                    )

            page_node_id = f"page_{page_index.id}"
            db.merge(KnowledgeNode(
                node_id=page_node_id,
                label=f"{doc.title} p.{page_index.page_number}",
                node_type="page",
                extra_data=f'{{"document_id": {doc.id}, "page_index_id": {page_index.id}}}',
            ))
            existing_page = db.query(KnowledgeEdge).filter_by(source_id=f"doc_{doc.id}", target_id=page_node_id, relationship="has_page").first()
            if not existing_page:
                db.add(KnowledgeEdge(
                    source_id=f"doc_{doc.id}",
                    target_id=page_node_id,
                    relationship="has_page",
                ))
                
            for eq_id in equip_ids:
                existing_mentions = db.query(KnowledgeEdge).filter_by(source_id=page_node_id, target_id=f"eq_{eq_id}", relationship="mentions").first()
                if not existing_mentions:
                    db.add(KnowledgeEdge(
                        source_id=page_node_id,
                        target_id=f"eq_{eq_id}",
                        relationship="mentions",
                    ))
            
        doc.equipment_tags = ",".join(list(all_equipment))

        # 3. Smart Chunking & Embeddings
        # Pages are the primary retrieval unit; chunks are semantic signals.
        if langchain_docs:
            try:
                vectorstore = get_chroma_vectorstore()
                vectorstore.add_documents(documents=langchain_docs)
            except Exception as e:
                print(f"[ingestion] Vector indexing unavailable for {doc.title}: {e}")
        
        # 4. Knowledge Graph (Neo4j / in-memory NetworkX simulation in DB)
        # Add document node
        doc_node_id = f"doc_{doc.id}"
        db_doc_node = KnowledgeNode(node_id=doc_node_id, label=doc.title, node_type="document")
        db.merge(db_doc_node)
        
        # Link document to equipment
        for eq_id in all_equipment:
            # Ensure equipment node exists
            db_eq_node = KnowledgeNode(node_id=f"eq_{eq_id}", label=eq_id, node_type="asset")
            db.merge(db_eq_node)
            
            existing_ref = db.query(KnowledgeEdge).filter_by(source_id=doc_node_id, target_id=f"eq_{eq_id}", relationship="references").first()
            if not existing_ref:
                db_edge = KnowledgeEdge(
                    source_id=doc_node_id,
                    target_id=f"eq_{eq_id}",
                    relationship="references"
                )
                db.add(db_edge)

        # 6. Finalize Status
        doc.status = "processed"
        db.commit()
        
        # Invalidate related caches
        cache_service.delete_prefix("chroma:")
        cache_service.delete_prefix("kg:")
        cache_service.delete_prefix("chat:llm_response:")
        
        print(f"Successfully processed document {doc.title}")

    except Exception as e:
        print(f"Error processing document {doc.id}: {e}")
        traceback.print_exc()
        doc.status = "failed"
        db.commit()
    finally:
        db.close()
