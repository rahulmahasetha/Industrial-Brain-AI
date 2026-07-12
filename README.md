# FreshFlow Beverages Knowledge Intelligence

**AI-powered Industrial Knowledge Intelligence Platform for beverage manufacturing and bottling.**

## Overview

FreshFlow Beverages Knowledge Intelligence is a unified AI platform that ingests plant documents, extracts knowledge, builds relationships between assets and documents, and provides intelligent assistance for operations, maintenance, troubleshooting, food safety, quality, and compliance.

## Core Capabilities

This platform is engineered to solve complex industrial knowledge challenges through advanced AI, GraphRAG, and Agentic workflows:

1. **Enterprise Dashboard**: Real-time insights into System Metrics, AI Brain Score, Confidence Levels, and system-wide knowledge health.
2. **AI Copilot (GraphRAG)**: Context-aware AI assistant capable of answering complex queries regarding equipment failure, SOPs, and compliance. Supports generating **audit-ready Enterprise PDF reports** directly from chat.
3. **Forensic Root Cause Analysis (RCA)**: Multi-agent AI engine that investigates failures (e.g. "Bottle Filling Machine Stopped") by synthesizing evidence from manuals, incident logs, and sensor telemetry. Predicts primary causes and generates actionable recommendations.
4. **Industrial Knowledge Graph**: Visualizes and traverses complex relationships between physical assets, compliance standards, and historical incidents.
5. **Intelligent Ingestion Pipeline**: Parses PDFs, scanned forms, spreadsheets, and expert notes into structured vector embeddings and relational graph nodes.

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
        PARSE[LlamaParse / OCR]
        CHUNK[Smart Chunking]
        META[Entity Extraction]
    end

    subgraph Storage & Retrieval
        SQLITE[(SQLite Relational DB)]
        CHROMA[(Chroma Vector DB)]
        KG[(Knowledge Graph)]
    end

    subgraph AI Agent Workflows
        RAG[GraphRAG Copilot]
        RCA[Forensic RCA Agent]
        COMP[Compliance Agent]
    end

    Data Sources --> PARSE
    PARSE --> CHUNK
    CHUNK --> META
    META --> SQLITE
    META --> CHROMA
    META --> KG

    SQLITE <--> AI Agent Workflows
    CHROMA <--> AI Agent Workflows
    KG <--> AI Agent Workflows
```

## Tech Stack

- **Frontend**: React, TypeScript, Vite, Tailwind CSS v4, Shadcn UI, Recharts, React Flow
- **Backend**: FastAPI, Python, SQLAlchemy
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **AI Stack**: LangChain, ChromaDB, LlamaParse

## Setup & Installation

### Using Docker Compose (Recommended)

1. Ensure Docker and Docker Compose are installed.
2. Run the application stack:
   ```bash
   docker-compose up --build
   ```
3. Access the Frontend UI at `http://localhost:3000`
4. Access the Backend API Docs at `http://localhost:8000/docs`

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
