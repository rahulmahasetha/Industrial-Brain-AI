# FreshFlow Beverages Knowledge Intelligence

**AI-powered Industrial Knowledge Intelligence Platform for beverage manufacturing and bottling.**

## Overview

FreshFlow Beverages Knowledge Intelligence is a unified AI platform that ingests plant documents, extracts knowledge, builds relationships between assets and documents, and provides intelligent assistance for operations, maintenance, troubleshooting, food safety, quality, and compliance.

## Architecture

The project is designed as a modern industrial knowledge platform with a scalable ingestion and retrieval pipeline.

- PDF Upload: Users upload documents and reports through the frontend.
- OCR: Extract text from scanned and image-based documents.
- Metadata Extraction: Extract document metadata, asset tags, and compliance attributes.
- Smart Chunking: Segment content into semantically coherent chunks for more accurate retrieval.
- Embeddings: Generate vector embeddings for document chunks.
- Hybrid Search: Perform retrieval using both vector similarity and BM25-style keyword search.
- Reranker: Reorder candidate passages for relevance and source quality.
- Prompt Builder: Assemble context, question, and instructions into LLM prompts.
- LLM: Generate answers using an LLM with grounded context.
- Source Citation: Return citations and supporting evidence for traceability.
- Conversation Memory: Maintain session-aware context and follow-up capabilities.
- Feedback & Analytics: Collect answer quality and usage data for continuous improvement.

## Features & Hackathon Modules

This platform maps directly to the **AI for Industrial Knowledge Intelligence** problem statement:

1. **Intelligent Ingestion Engine**: Parses PDFs, P&IDs, scanned forms, spreadsheets, and expert notes (`services/ingestion.py`, `services/page_index_service.py`).
2. **Industrial Knowledge Graph**: Builds relationships between assets, documents, incidents, and standards (`routers/knowledge_graph.py`).
3. **Intent-Based Retrieval & Copilot**: Context-aware RAG answering questions like "Why did CV101 fail?" with exact citations (`services/rag_service.py`).
4. **Automated Root Cause Analysis (RCA)**: Investigates anomalies using evidence from manuals and shift logs (`agents/rca_agent.py`).
5. **Lessons Learned & Failure Intelligence**: Analyzes historical incidents for cross-asset patterns (`services/lessons_learned_service.py`).
6. **Compliance Agent**: Audits documents against ISO/FSSAI standards (`agents/compliance_agent.py`).
7. **Predictive Maintenance**: Generates natural language advisories based on asset health and sensor data (`agents/predictive_maintenance.py`).

## Architecture

```mermaid
graph TD
    subgraph Data Sources
        PDF[PDF Manuals/SOPs]
        CSV[Spreadsheets/Incidents]
        TXT[Expert Notes]
        SENSORS[Sensor Telemetry]
    end

    subgraph Ingestion Pipeline
        PARSE[LlamaParse / OCR / Pandas]
        CHUNK[Smart Chunking]
        META[Entity Extraction]
    end

    subgraph Storage
        SQLITE[(SQLite Relational DB)]
        CHROMA[(Chroma Vector DB)]
        KG[(Knowledge Graph)]
    end

    subgraph AI Agents
        RAG[RAG Copilot]
        RCA[RCA Agent]
        COMP[Compliance Agent]
        PRED[Predictive Maint.]
        LL[Lessons Learned]
    end

    Data Sources --> PARSE
    PARSE --> CHUNK
    CHUNK --> META
    META --> SQLITE
    META --> CHROMA
    META --> KG

    SQLITE <--> AI Agents
    CHROMA <--> AI Agents
    KG <--> AI Agents
```

## Production Pipeline

The platform is designed to support a modern industrial AI ingestion and retrieval workflow:

- PDF Upload
- OCR
- Metadata Extraction
- Smart Chunking
- Embeddings
- Hybrid Search (Vector + BM25)
- Reranker
- Prompt Builder
- LLM
- Source Citation
- Conversation Memory
- Feedback & Analytics

## Tech Stack

- **Frontend**: React, TypeScript, Vite, Tailwind CSS v4, Shadcn UI, React Flow, Recharts
- **Backend**: FastAPI, Python, SQLAlchemy
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **AI Stack**: LangChain, LlamaParse, Gemini 2.5 Pro (Mocked in demo)

## Running the Application

### Using Docker Compose (Recommended)

1. Ensure Docker is installed and running.
2. Run the application:
   ```bash
   docker-compose up --build
   ```
3. Access the frontend at `http://localhost:3000`
4. Access the backend API docs at `http://localhost:8000/docs`

### Manual Setup

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
fastapi run main.py
```
