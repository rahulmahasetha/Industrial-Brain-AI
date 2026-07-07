import os
from typing import Dict, Any

class DocumentProcessor:
    def __init__(self):
        self.supported_formats = [".pdf", ".docx", ".xlsx", ".txt"]

    async def process_document(self, file_path: str, filename: str) -> Dict[str, Any]:
        """
        Simulates parsing a document using LlamaParse and extracting metadata.
        """
        _, ext = os.path.splitext(filename)
        if ext.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported format {ext}")
            
        print(f"Processing {filename} via LlamaParse (Mock)...")
        
        # Simulate extracted metadata
        metadata = {
            "title": filename,
            "type": "Manual" if "manual" in filename.lower() else "Document",
            "page_count": 42,
            "extracted_entities": ["FM101", "AC101", "Bottle Count", "Sanitization"]
        }
        
        # Return mocked chunks
        return {
            "status": "success",
            "metadata": metadata,
            "chunks": [
                {"content": "Section 1: Startup SOP for Bottle Filling Machine FM101...", "page": 1},
                {"content": "Warning: Investigate conveyor vibration above 6 mm/s before replacing bearings...", "page": 24}
            ]
        }

document_processor = DocumentProcessor()
