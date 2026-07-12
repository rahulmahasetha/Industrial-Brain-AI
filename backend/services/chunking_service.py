import os
import re
import json
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field

try:
    from langchain_groq import ChatGroq
except ImportError:
    ChatGroq = None


class DocumentMetadata(BaseModel):
    document_type: str = Field(description="Document type (e.g. Equipment Manual, SOP, Incident Report, RCA Report, Inspection Report, QA Report, Compliance Certificate, Training Manual, Maintenance Log, Sensor Readings, Shift Log, Others)")
    equipment_id: str = Field(default="", description="Equipment tag or ID if available (e.g., AC101, FM101)")
    equipment_name: str = Field(default="", description="Name of the equipment if available (e.g., Air Compressor)")
    manufacturer: str = Field(default="", description="Manufacturer if available")
    department: str = Field(default="", description="Department if available")
    revision: str = Field(default="", description="Revision version if available")
    issue_date: str = Field(default="", description="Issue date if available")


class ChunkingService:
    def __init__(self):
        self.llm = None
        if ChatGroq:
            api_key = os.environ.get("GROQ_API_KEY")
            if api_key:
                self.llm = ChatGroq(
                    api_key=api_key,
                    model="llama-3.1-8b-instant",
                    temperature=0.0
                )

    def extract_metadata(self, text: str, filename: str) -> Dict[str, Any]:
        """Extract document metadata using Gemini with rule-based fallback prioritization."""
        guessed_type = self._guess_type_from_filename(filename)
        
        metadata = {"document_type": guessed_type}
        
        if not self.llm:
            return metadata

        # Use the first 8000 characters to deduce metadata
        sample_text = text[:8000]
        prompt = f"""
        Extract metadata from the following document (Filename: {filename}).
        Determine the most appropriate 'document_type' from the following list:
        - Equipment Manual
        - SOP
        - Incident Report
        - RCA Report
        - Inspection Report
        - QA Report
        - Compliance Certificate
        - Training Manual
        - Maintenance Log
        - Sensor Readings
        - Shift Log
        - Others
        
        Document Text Snippet:
        {sample_text}
        """
        
        try:
            llm_with_tools = self.llm.with_structured_output(DocumentMetadata)
            result = llm_with_tools.invoke(prompt)
            ai_data = result.model_dump()
            
            # Rule-based priority: if rule-based got something specific, keep it over AI fallback
            if guessed_type != "Others" and guessed_type != ai_data.get("document_type"):
                ai_data["document_type"] = guessed_type
                
            return ai_data
        except Exception as e:
            print(f"[ChunkingService] Error extracting metadata: {e}")
            return metadata

    def _guess_type_from_filename(self, filename: str) -> str:
        filename_lower = filename.lower()
        if "manual" in filename_lower: return "Equipment Manual"
        if "sop" in filename_lower: return "SOP"
        if "inc" in filename_lower: return "Incident Report"
        if "rca" in filename_lower: return "RCA Report"
        if "insp" in filename_lower: return "Inspection Report"
        if "qa" in filename_lower: return "QA Report"
        if "comp" in filename_lower: return "Compliance Certificate"
        if "log" in filename_lower or "maint" in filename_lower: return "Maintenance Log"
        return "Others"

    def create_semantic_chunks(self, pages: List[Dict[str, Any]], metadata: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Create intelligent, section-based semantic chunks.
        Returns:
            chunks: List of dictionaries representing chunk data.
            toc_mapping: A TOC dictionary for manuals mapping section names to start/end pages.
        """
        doc_type = metadata.get("document_type", "Others")
        
        # CSV/Row-based handling
        if doc_type in ["Maintenance Log", "Sensor Readings", "Shift Log"] or any(p.get("source_type") == "CSV_ROW" for p in pages):
            chunks = []
            for page in pages:
                # Each page is already one row/record
                chunk = {
                    "id": f"chunk_{page['page_number']}",
                    "text": page["text"],
                    "page_start": page["page_number"],
                    "page_end": page["page_number"],
                    "section_name": "Record",
                    "section_number": str(page["page_number"]),
                    **metadata
                }
                chunks.append(chunk)
            return chunks, {}

        # Markdown/Text semantic chunking for documents
        full_text = ""
        page_offsets = [] # Track character offsets for each page to map text back to page numbers
        current_offset = 0
        
        for p in sorted(pages, key=lambda x: x["page_number"]):
            page_text = p.get("text", "") + "\n\n"
            page_offsets.append({
                "page": p["page_number"],
                "start": current_offset,
                "end": current_offset + len(page_text)
            })
            full_text += page_text
            current_offset += len(page_text)

        # Split by Markdown Headers or Numbered Sections
        # Matches: # Header OR 1. Introduction OR 1.1 Overview
        header_pattern = re.compile(r'^(?:(#{1,6})\s+(.+)|((?:\d+\.)+\d*\.?)\s+([A-Z].{2,80}))\s*$', re.MULTILINE)
        
        sections = []
        last_pos = 0
        current_section_name = "Introduction"
        current_section_number = "0"
        
        for match in header_pattern.finditer(full_text):
            start_pos = match.start()
            
            if start_pos > last_pos:
                section_text = full_text[last_pos:start_pos].strip()
                if section_text:
                    sections.append({
                        "name": current_section_name,
                        "number": current_section_number,
                        "start_pos": last_pos,
                        "end_pos": start_pos,
                        "text": section_text
                    })
            
            last_pos = start_pos
            if match.group(1): # Markdown header
                header_level = len(match.group(1))
                header_text = match.group(2).strip()
                # Check if it starts with a number
                num_match = re.match(r'^([\d\.]+)\s*(.*)', header_text)
                if num_match:
                    current_section_number = num_match.group(1).rstrip('.')
                    current_section_name = num_match.group(2).strip()
                else:
                    current_section_number = str(len(sections) + 1)
                    current_section_name = header_text
            else: # Numbered section
                current_section_number = match.group(3).rstrip('.')
                current_section_name = match.group(4).strip()

        # Add the last section
        if last_pos < len(full_text):
            section_text = full_text[last_pos:].strip()
            if section_text:
                sections.append({
                    "name": current_section_name,
                    "number": current_section_number,
                    "start_pos": last_pos,
                    "end_pos": len(full_text),
                    "text": section_text
                })

        # Process sections into chunks
        chunks = []
        toc_mapping = {}
        
        def get_page_for_offset(offset: int) -> int:
            for p in page_offsets:
                if p["start"] <= offset < p["end"]:
                    return p["page"]
            return page_offsets[-1]["page"] if page_offsets else 1

        import hashlib
        doc_id = metadata.get("document_id", "unknown")
        
        prev_chunk_id = None
        
        for idx, sec in enumerate(sections):
            page_start = get_page_for_offset(sec["start_pos"])
            page_end = get_page_for_offset(sec["end_pos"])
            
            sub_chunks = self._split_section_text(sec["text"], max_size=1500)
            
            for sub_idx, sub_text in enumerate(sub_chunks):
                if not sub_text.strip():
                    continue
                    
                # Create a deterministic hash for incremental indexing
                content_hash = hashlib.md5(sub_text.encode('utf-8')).hexdigest()
                chunk_id = f"doc_{doc_id}_sec_{sec['number']}_{idx}_{sub_idx}"
                
                chunk = {
                    "id": chunk_id,
                    "text": sub_text,
                    "page_start": page_start,
                    "page_end": page_end,
                    "section_name": sec["name"][:100],
                    "section_number": sec["number"],
                    "content_hash": content_hash,
                    "prev_chunk_id": prev_chunk_id,
                    "next_chunk_id": None, # Will set on next iteration
                    **metadata
                }
                
                if chunks:
                    chunks[-1]["next_chunk_id"] = chunk_id
                    
                chunks.append(chunk)
                prev_chunk_id = chunk_id
                
            # Build TOC mapping
            if doc_type in ["Equipment Manual", "SOP"]:
                sec_key = sec["name"][:100]
                if sec_key and sec_key not in toc_mapping:
                    toc_mapping[sec_key] = {
                        "page_start": page_start,
                        "page_end": page_end
                    }

        # Final Validation pass (no empty chunks, no duplicates)
        validated_chunks = []
        seen_ids = set()
        for c in chunks:
            if not c["text"].strip() or c["id"] in seen_ids:
                continue
            seen_ids.add(c["id"])
            validated_chunks.append(c)

        return validated_chunks, {"toc": toc_mapping}

    def _split_section_text(self, text: str, max_size: int = 1500) -> List[str]:
        """Split section into smaller chunks if necessary, without breaking tables, lists, or warnings."""
        if len(text) <= max_size:
            return [text]
            
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_len = 0
        in_table = False
        in_list = False
        in_warning = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # Table detection
            if '|' in line and '-|-' not in line and not in_table:
                in_table = True
            elif not line_stripped and in_table:
                in_table = False
                
            # List detection
            if re.match(r'^(\*|-|\d+\.)\s', line_stripped):
                in_list = True
            elif not line_stripped and in_list:
                in_list = False
                
            # Warning/Note detection
            if re.match(r'^(\*\*warning\*\*|\*\*note\*\*|warning:|note:)', line_stripped, re.IGNORECASE):
                in_warning = True
            elif not line_stripped and in_warning:
                in_warning = False
                
            current_chunk.append(line)
            current_len += len(line) + 1
            
            can_split = not (in_table or in_list or in_warning) and not line_stripped
            
            if current_len > max_size and can_split:
                chunks.append('\n'.join(current_chunk).strip())
                current_chunk = []
                current_len = 0
                
        if current_chunk:
            chunks.append('\n'.join(current_chunk).strip())
            
        return [c for c in chunks if c.strip()]

chunking_service = ChunkingService()
