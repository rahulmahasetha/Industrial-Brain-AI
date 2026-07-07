import sqlite3
import chromadb

conn = sqlite3.connect('industrial_brain.db')
c = conn.cursor()

c.execute("SELECT type, COUNT(*) FROM documents GROUP BY type")
doc_types = c.fetchall()

c.execute("SELECT status, COUNT(*) FROM documents GROUP BY status")
doc_status = c.fetchall()

c.execute("SELECT procedure_type, COUNT(*) FROM page_index GROUP BY procedure_type")
page_types = c.fetchall()

c.execute("SELECT COUNT(*) FROM page_index")
total_pages = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM knowledge_nodes")
kg_nodes = c.fetchone()[0]

print("=== Document Metrics ===")
for t, count in doc_types:
    print(f"  {t}: {count}")

print("\n=== Document Status ===")
for s, count in doc_status:
    print(f"  {s}: {count}")

print("\n=== Page Metrics ===")
print(f"Total pages indexed: {total_pages}")
for t, count in page_types:
    print(f"  {t}: {count}")
print(f"\nKnowledge Graph Nodes: {kg_nodes}")

try:
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection("industrial_docs")
    print(f"\n=== ChromaDB Metrics ===")
    print(f"Total vectors (chunks): {collection.count()}")
except Exception as e:
    print(f"ChromaDB Error: {e}")
