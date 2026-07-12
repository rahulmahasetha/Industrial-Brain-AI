import os
import json
import csv
import glob
import re
from datetime import datetime
import sys
from dotenv import load_dotenv

load_dotenv()

# Ensure backend root is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Ensure project root is in sys.path so we can import dataset_gen
project_root = os.path.dirname(backend_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from database import engine, Base, SessionLocal
import models.domain as m

# For Vector Store
from services.ingestion import get_chroma_vectorstore
from services.page_index_service import PageIndexService, split_page_into_smart_chunks
from services.chunking_service import chunking_service
from langchain_core.documents import Document as LangchainDocument
import PyPDF2
import time

page_index_service = PageIndexService()

def add_docs_with_retry(vectorstore, docs, batch_size=20):
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i+batch_size]
        success = False
        retries = 1
        while not success and retries > 0:
            try:
                vectorstore.add_documents(documents=batch)
                success = True
                print(f"  Added batch of {len(batch)} documents.")
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"  Rate limit hit. Retrying in 2s... ({retries} retries left)")
                    time.sleep(2)
                    retries -= 1
                else:
                    print(f"  Error adding documents: {e}")
                    break
        if not success:
            print(f"  Skipping batch after failed retries.")
            
BASE_DIR = os.path.join(project_root, "IndustrialBrain")

def ingest_data():
    print("Recreating SQLite database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        vectorstore = get_chroma_vectorstore()
    except Exception as e:
        print(f"Failed to initialize ChromaDB: {e}")
        vectorstore = None

    try:
        # 1. Ingest Assets from config
        print("Ingesting assets...")
        from dataset_gen.config import ALL_EQUIPMENT
        
        asset_map = {}
        for item in ALL_EQUIPMENT:
            db_asset = m.Asset(
                tag=item['id'],
                name=item['name'],
                type=item['type'],
                location=item['location'],
                health_score=100.0,
                status="operational"
            )
            db.add(db_asset)
            asset_map[item['id']] = db_asset
        
        db.commit()

        # 2. Ingest Sensor Snapshots
        print("Ingesting sensor snapshots...")
        sensor_file = os.path.join(BASE_DIR, "sensor_data", "sensor_readings.csv")
        
        latest_readings = {}
        if os.path.exists(sensor_file):
            with open(sensor_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    latest_readings.setdefault(row["Asset_ID"], {})[row["Sensor_Name"]] = row

            for eq_id, reading in latest_readings.items():
                if eq_id in asset_map:
                    asset = asset_map[eq_id]
                    def val(name, default=0.0):
                        try:
                            return float(reading.get(name, {}).get("Value", default))
                        except (TypeError, ValueError):
                            return default
                    asset.temperature = val("Machine Temperature", 32.0)
                    asset.vibration = val("Machine Vibration", 2.1)
                    asset.power_draw = val("Power Consumption", 15.0)
                    if asset.vibration > 6 or asset.temperature > 75:
                        asset.status = "warning"
                        asset.health_score = 68.0
                    else:
                        asset.health_score = 88.0
            
            db.commit()

        # 3. Ingest Maintenance Logs into Incidents
        print("Ingesting maintenance logs...")
        maint_file = os.path.join(BASE_DIR, "maintenance_logs", "maintenance_logs.csv")
        if os.path.exists(maint_file):
            with open(maint_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    db_incident = m.Incident(
                        title=row.get("Issue_Description", "Issue"),
                        description=row.get("Remarks", ""),
                        asset_tag=row.get("Asset_ID", ""),
                        severity=row.get("Severity", "low").lower(),
                        status="resolved" if row.get("Status") == "Closed" else "open",
                        root_cause=row.get("Root_Cause", ""),
                        corrective_action=row.get("Corrective_Action", ""),
                        reported_by=row.get("Technician_Name", ""),
                        assigned_to=row.get("Technician_Name", ""),
                        created_at=datetime.strptime(row["Date"], "%Y-%m-%d") if row.get("Date") else datetime.utcnow()
                    )
                    db.add(db_incident)
                    
                    if row.get("Asset_ID") in asset_map:
                        asset_map[row["Asset_ID"]].last_maintenance = row["Date"]
            db.commit()

        # 4. Ingest Expert Notes (SQLite + ChromaDB)
        print("Ingesting expert notes (SQLite & ChromaDB)...")
        expert_dir = os.path.join(BASE_DIR, "expert_notes")
        expert_files = glob.glob(os.path.join(expert_dir, "*.md"))
        langchain_docs = []
        
        for file_path in expert_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Basic parsing of the MD
            author = ""
            asset = ""
            observation = content
            
            for line in content.split("\n"):
                if line.startswith("**Author:**"): author = line.replace("**Author:**", "").strip()
                elif line.startswith("**Related Asset:**"): asset = line.replace("**Related Asset:**", "").strip().split()[0]
                
            db_exp = m.ExpertKnowledge(
                condition=observation[:250] + "...",
                action="Refer to expert note",
                target_asset=asset,
                confidence=0.9,
                source_expert=author,
                validated=True
            )
            db.add(db_exp)
            
            # Add to Langchain Docs for RAG
            langchain_docs.append(LangchainDocument(
                page_content=content,
                metadata={"source": os.path.basename(file_path), "type": "ExpertNote", "asset": asset}
            ))
            
        db.commit()
        
        # Insert Expert notes into Chroma
        if vectorstore and langchain_docs:
            print(f"Adding {len(langchain_docs)} expert notes to ChromaDB in batches...")
            add_docs_with_retry(vectorstore, langchain_docs)
            langchain_docs = [] # Clear memory

        def get_or_create_node(node_id, label, node_type, extra_data="{}"):
            node = db.query(m.KnowledgeNode).filter(m.KnowledgeNode.node_id == node_id).first()
            if not node:
                node = m.KnowledgeNode(node_id=node_id, label=label, node_type=node_type, extra_data=extra_data)
                db.add(node)
                db.flush()
            return node

        # 5. Ingest Knowledge Graph
        print("Ingesting knowledge graph relationships...")
        kg_file = os.path.join(BASE_DIR, "knowledge_graph", "graph_relationships.json")
        if os.path.exists(kg_file):
            with open(kg_file, 'r', encoding='utf-8') as f:
                kg_data = json.load(f)
                
            for node in kg_data.get("nodes", []):
                get_or_create_node(
                    node_id=node["id"],
                    label=node.get("name") or node["id"],
                    node_type=node.get("label", "other").lower()
                )
                
            for edge in kg_data.get("edges", []):
                db_edge = m.KnowledgeEdge(
                    source_id=edge["source"],
                    target_id=edge["target"],
                    relationship=edge["type"]
                )
                db.add(db_edge)
                
            db.commit()

        # 5b. Link Incidents into Knowledge Graph
        print("Linking incidents to knowledge graph...")
        all_incidents = db.query(m.Incident).all()
        for inc in all_incidents:
            inc_node_id = f"inc_{inc.id}"
            get_or_create_node(
                node_id=inc_node_id,
                label=inc.title or f"Incident #{inc.id}",
                node_type="incident",
                extra_data=json.dumps({"severity": inc.severity, "status": inc.status}),
            )
            # Link incident -> asset
            if inc.asset_tag:
                db.merge(m.KnowledgeEdge(
                    source_id=inc_node_id,
                    target_id=f"eq_{inc.asset_tag}",
                    relationship="occurred_on",
                ))
                # Ensure the equipment node exists
                get_or_create_node(
                    node_id=f"eq_{inc.asset_tag}",
                    label=inc.asset_tag,
                    node_type="asset",
                )
            if inc.root_cause:
                rc_node_id = f"rc_{inc.id}"
                get_or_create_node(
                    node_id=rc_node_id,
                    label=inc.root_cause[:100],
                    node_type="root_cause",
                )
                db.merge(m.KnowledgeEdge(
                    source_id=inc_node_id,
                    target_id=rc_node_id,
                    relationship="caused_by",
                ))
        db.commit()

        # 5c. Link Compliance Records into Knowledge Graph
        print("Linking compliance records to knowledge graph...")
        all_compliance = db.query(m.ComplianceRecord).all()
        for cr in all_compliance:
            cr_node_id = f"comp_{cr.id}"
            get_or_create_node(
                node_id=cr_node_id,
                label=f"{cr.standard} {cr.section}".strip(),
                node_type="compliance",
                extra_data=json.dumps({"status": cr.status, "risk_level": cr.risk_level}),
            )
            # Link to standard node
            std_node_id = f"std_{cr.standard.replace(' ', '_')}" if cr.standard else None
            if std_node_id:
                get_or_create_node(
                    node_id=std_node_id,
                    label=cr.standard,
                    node_type="standard"
                )
                db.merge(m.KnowledgeEdge(
                    source_id=cr_node_id,
                    target_id=std_node_id,
                    relationship="governed_by",
                ))
            # Link to asset if applicable
            if cr.asset_tag:
                db.merge(m.KnowledgeEdge(
                    source_id=cr_node_id,
                    target_id=f"eq_{cr.asset_tag}",
                    relationship="applies_to",
                ))
        db.commit()

        # 6. Ingest Documents (SQLite + ChromaDB RAG)
        print("Ingesting documents (SQLite & ChromaDB)...")
        pdf_files = glob.glob(os.path.join(BASE_DIR, "**", "*.pdf"), recursive=True)
        csv_files = glob.glob(os.path.join(BASE_DIR, "**", "*.csv"), recursive=True)
        all_files = pdf_files + csv_files
        
        doc_count = 0
        page_count = 0
        chunk_count = 0
        failed_docs = []
        skipped_docs = []
        
        seen_documents = set() # To skip duplicates by filename
        
        for file_path in all_files:
            filename = os.path.basename(file_path)
            
            if filename in seen_documents:
                skipped_docs.append(filename)
                continue
                
            seen_documents.add(filename)
            size_bytes = os.path.getsize(file_path)
            size_str = f"{size_bytes / 1024 / 1024:.1f} MB" if size_bytes > 1024*1024 else f"{size_bytes / 1024:.1f} KB"
            
            equip_tags = ",".join(re.findall(r'\b[A-Z]{1,3}\d{3}\b', filename))
            
            doc_type = "Document"
            if "Manual" in filename: doc_type = "Manual"
            elif "SOP" in filename: doc_type = "SOP"
            elif "INC" in filename: doc_type = "Incident"
            elif "INSP" in filename: doc_type = "Inspection"
            elif "RCA" in filename: doc_type = "RCA"
            elif "COMP" in filename: doc_type = "Compliance"
            
            try:
                db_doc = m.Document(
                    title=filename,
                    type=doc_type,
                    size=size_str,
                    status="processed", 
                    equipment_tags=equip_tags
                )
                db.add(db_doc)
                db.flush() # Flush to get ID, but don't commit yet to allow atomic rollback
                langchain_docs = []
                pages_data = []
                total_extracted_pages = 0
                
                if file_path.lower().endswith('.pdf'):
                    reader = PyPDF2.PdfReader(file_path)
                    total_pages = len(reader.pages)
                    count = min(total_pages, 100)
                    for p_num in range(1, count + 1):
                        page = reader.pages[p_num - 1]
                        extracted = page.extract_text()
                        if extracted and extracted.strip():
                            # Add to SQLite PageIndex via service
                            page_index = page_index_service.build_page_record(
                                db=db, 
                                doc=db_doc, 
                                page_number=p_num, 
                                text=extracted
                            )
                            page_count += 1
                            pages_data.append({"page_number": p_num, "text": extracted, "page_index_id": page_index.id})
                    total_extracted_pages = len(reader.pages)
                elif file_path.lower().endswith('.csv'):
                    import pandas as pd
                    import numpy as np
                    df = pd.read_csv(file_path)
                    df = df.replace({np.nan: None})
                    total_pages = len(df)
                    count = min(total_pages, 100)
                    for i in range(count):
                        row = df.iloc[i]
                        row_dict = row.to_dict()
                        text = "\n".join([f"**{k}**: {v}" for k, v in row_dict.items() if v is not None])
                        
                        log_id = str(row_dict.get('Log_ID', '')) or ''
                        incident_id = str(row_dict.get('Related_Incident_ID', '')) or str(row_dict.get('Incident_ID', '')) or ''
                        inspection_id = str(row_dict.get('Inspection_ID', '')) or ''
                        sop_id = str(row_dict.get('SOP_Reference', '')) or ''
                        
                        page_index = page_index_service.build_page_record(
                            db=db, 
                            doc=db_doc, 
                            page_number=i + 1, 
                            text=text,
                            log_id=log_id,
                            incident_id=incident_id,
                            inspection_id=inspection_id,
                            sop_id=sop_id,
                            source_type="CSV_ROW"
                        )
                        page_count += 1
                        pages_data.append({"page_number": i + 1, "text": text, "page_index_id": page_index.id})
                    total_extracted_pages = len(df)
                        
                # Extract metadata
                full_text_sample = "\n\n".join(p["text"] for p in pages_data[:10])
                extracted_metadata = chunking_service.extract_metadata(full_text_sample, filename)
                
                extracted_metadata["document_id"] = db_doc.id
                extracted_metadata["source_file"] = filename
                
                if extracted_metadata.get("document_type") and extracted_metadata["document_type"] != "Others":
                    db_doc.type = extracted_metadata["document_type"]
                
                # Semantic chunking
                semantic_chunks, toc_data = chunking_service.create_semantic_chunks(pages_data, extracted_metadata)
                
                # Merge into metadata_json
                existing_meta = {}
                if db_doc.metadata_json:
                    try:
                        existing_meta = json.loads(db_doc.metadata_json)
                    except:
                        pass
                existing_meta.update(extracted_metadata)
                if "toc" in toc_data:
                    existing_meta["toc"] = toc_data["toc"]
                db_doc.metadata_json = json.dumps(existing_meta)
                
                for chunk in semantic_chunks:
                    langchain_docs.append(LangchainDocument(
                        page_content=chunk["text"],
                        metadata={
                            "source": filename, 
                            "type": chunk.get("document_type", db_doc.type),
                            "document_id": db_doc.id,
                            "equipment": equip_tags,
                            "equipment_id": chunk.get("equipment_id", ""),
                            "equipment_name": chunk.get("equipment_name", ""),
                            "department": chunk.get("department", ""),
                            "revision": chunk.get("revision", ""),
                            "page_start": chunk.get("page_start", 1),
                            "page_end": chunk.get("page_end", 1),
                            "section_name": chunk.get("section_name", ""),
                            "section_number": chunk.get("section_number", ""),
                            "chunk_id": chunk["id"],
                            "content_hash": chunk.get("content_hash", ""),
                            "prev_chunk_id": chunk.get("prev_chunk_id", ""),
                            "next_chunk_id": chunk.get("next_chunk_id", ""),
                            "source_file": chunk.get("source_file", filename)
                        }
                    ))
                    chunk_count += 1
                
                if vectorstore and langchain_docs:
                    db.commit() # Release SQLite locks BEFORE slow API calls!
                    add_docs_with_retry(vectorstore, langchain_docs, batch_size=20)
                    
                db_doc.page_count = total_extracted_pages
                doc_count += 1
                db.commit() # Commit after each document to persist immediately
            except Exception as e:
                print(f"Error reading {filename}: {e}")
                failed_docs.append(filename)
                db.rollback()
                # Optionally, we could add a failed document record here if needed,
                # but it's safer to just let it rollback completely to avoid corrupted state.
        db.commit()
        
        # End Summary
        print("\n========================================")
        print("BULK INGESTION COMPLETE")
        print("========================================")
        print(f"Total Documents Ingested: {doc_count}")
        print(f"Total Pages Indexed: {page_count}")
        print(f"Total Chunks Created (VectorDB): {chunk_count}")
        if skipped_docs:
            print(f"Skipped Duplicates ({len(skipped_docs)}): {', '.join(skipped_docs[:5])}...")
        if failed_docs:
            print(f"Failed Documents ({len(failed_docs)}): {', '.join(failed_docs[:5])}...")
        print("========================================\n")

    except Exception as e:
        print(f"Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    ingest_data()
