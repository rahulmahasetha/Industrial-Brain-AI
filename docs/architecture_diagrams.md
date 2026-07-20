# Industrial Brain AI - Architecture Diagrams (Colored Edition)

This document outlines the core architecture, pipelines, and workflows of the Industrial Brain AI platform through visual, color-coded diagrams.

## 1. System Architecture
High-level overview of the interaction between the frontend, backend, databases, and AI services.

```mermaid
graph TD
    classDef user fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff;
    classDef frontend fill:#0ea5e9,stroke:#0369a1,stroke-width:2px,color:#fff;
    classDef backend fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff;
    classDef db fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff;
    classDef ai fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#fff;
    classDef bg fill:#64748b,stroke:#334155,stroke-width:2px,color:#fff;

    User([User]):::user --> |HTTPS| Frontend[Frontend React/Vite]:::frontend
    Frontend --> |REST/WebSockets| API[FastAPI Backend]:::backend
    API --> |SQL| DB[(PostgreSQL / Neon DB)]:::db
    API --> |Cache/Queue| Redis[(Redis)]:::db
    API --> |Vector Search| VectorDB[(Vector DB - Pinecone / Qdrant)]:::db
    API --> |LLM Inference| LLM[LLM Service / OpenAI]:::ai
    Redis --> Worker[Celery Worker]:::bg
    Worker --> |Background Tasks| API
```

## 2. RAG (Retrieval-Augmented Generation) Pipeline
Describes how unstructured data (SOPs, manuals) is ingested and how user queries retrieve context for the LLM.

```mermaid
flowchart TD
    classDef data fill:#f87171,stroke:#b91c1c,stroke-width:2px,color:#fff;
    classDef process fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff;
    classDef db fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff;
    classDef ai fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#fff;
    classDef user fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff;
    classDef guard fill:#eab308,stroke:#a16207,stroke-width:2px,color:#fff;

    %% Ingestion
    subgraph Ingestion ["Data Ingestion (Industrial Manuals, SOPs, RCA)"]
        direction LR
        Docs[Raw Documents]:::data --> Parse[Chunking & Parser]:::process
        Parse --> Meta[Metadata Extraction]:::ai
        Meta --> Embed[Embedding]:::ai
        
        Meta -.-> SQLDB[(SQL Metadata)]:::db
        Embed -.-> VectorDB[(Vector DB)]:::db
        Parse -.-> TextDB[(BM25 Index)]:::db
        Meta -.-> GraphDB[(Knowledge Graph)]:::db
    end

    %% Query Processing
    subgraph QueryProcessing ["Query Pre-Processing"]
        UserQuery([User Query]):::user --> Cache{Redis Cache}:::db
        Cache -->|Miss| Intent[Intent Classification]:::ai
        Intent --> SQLCheck{SQL-First?}:::process
        SQLCheck -->|Yes| SQLQuery[SQL Lookup]:::process
        SQLCheck -->|No| Rewrite[Query Rewriting]:::ai
        Rewrite --> Filter[Strict Metadata Filtering]:::process
    end

    %% Retrieval
    subgraph Retrieval ["Hybrid Retrieval Engine"]
        Filter --> VSearch[Vector Similarity]:::process
        Filter --> KSearch[Keyword / BM25]:::process
        Filter --> GSearch[Graph Traversal]:::process
        
        VSearch -.-> VectorDB
        KSearch -.-> TextDB
        GSearch -.-> GraphDB
        SQLQuery -.-> SQLDB
    end

    %% Post-Processing
    subgraph PostProcessing ["Post-Retrieval Optimization"]
        VectorDB & TextDB & GraphDB & SQLDB --> Merge[Merge Results]:::process
        Merge --> Rerank[Cross-Encoder Re-ranking]:::ai
        Rerank --> Compress[Context Compression]:::process
        Compress --> AntiContam[Contamination Prevention]:::process
    end

    %% Generation & Guardrails
    subgraph Generation ["Generation & Guardrails"]
        AntiContam --> Prompt[Prompt: Evidence-Only]:::process
        Prompt --> LLM[Large Language Model]:::ai
        LLM --> HallucGuard[Hallucination Guard]:::guard
        HallucGuard --> AnswerVal[Answer Validation]:::guard
        AnswerVal --> Citation[Citation Validation]:::guard
        Citation --> Confidence[Confidence Scoring]:::guard
    end

    Confidence --> Analytics[Retrieval Analytics]:::process
    Confidence --> UpdateCache[Cache Result]:::db
    UpdateCache --> Response([Grounded Response + Citations]):::user
    Cache -->|Hit| Response
```

## 3. Knowledge Graph Architecture (GraphRAG)
Shows how industrial entities are linked conceptually to provide rich, context-aware answers.

```mermaid
graph TD
    classDef entity fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff;
    classDef document fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff;
    classDef incident fill:#ef4444,stroke:#b91c1c,stroke-width:2px,color:#fff;
    classDef engine fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#fff;
    classDef db fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff;

    subgraph Entities
    Machine[Machine: FM101]:::entity
    Incident[Incident: Overheating]:::incident
    SOP[SOP: FM101-Start]:::document
    Sensor[Sensor: Temp-1]:::entity
    end
    
    Machine -->|has_sensor| Sensor
    Machine -->|documented_by| SOP
    Machine -->|experienced| Incident
    Incident -->|requires_review| SOP
    
    subgraph Graph Engine
    Extractor[Entity Extractor]:::engine --> KnowledgeBase[(Graph DB)]:::db
    QueryEngine[Graph Query Engine]:::engine --> KnowledgeBase
    end
```

## 4. Sequence Diagram: AI Copilot Chat
Interaction flow during a real-time Copilot chat session, with color-coded regions mapped to the journey from user prompt to streaming response.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Frontend
    participant API as FastAPI Backend
    participant VectorDB as Vector Store
    participant LLM as AI Model

    rect rgb(239, 246, 255)
    User->>Frontend: Types message "Show SOP"
    Frontend->>API: POST /api/chat
    end
    
    rect rgb(240, 253, 244)
    API->>API: Generate Embedding for Query
    API->>VectorDB: Search nearest vectors
    VectorDB-->>API: Return Top-K chunks
    end
    
    rect rgb(250, 245, 255)
    API->>API: Construct Prompt with context
    API->>LLM: Generate Response (Stream)
    LLM-->>API: Stream chunks
    end
    
    rect rgb(239, 246, 255)
    API-->>Frontend: Stream chunks via SSE/WebSocket
    Frontend-->>User: Render Markdown UI
    end
```

## 5. Database ER (Entity-Relationship) Diagram
Core PostgreSQL schema highlighting how Users, Chats, Messages, and Equipment are related. Rendered with the neutral theme for clarity.

```mermaid
%%{init: {'theme': 'neutral'}}%%
erDiagram
    USERS ||--o{ CHATS : owns
    CHATS ||--o{ MESSAGES : contains
    EQUIPMENT ||--o{ INCIDENTS : has
    EQUIPMENT ||--o{ SOPS : has
    
    USERS {
        uuid id PK
        string email
        string name
        string role
    }
    CHATS {
        uuid id PK
        uuid user_id FK
        string title
        datetime created_at
    }
    MESSAGES {
        uuid id PK
        uuid chat_id FK
        string role
        string content
        datetime created_at
    }
    EQUIPMENT {
        string id PK
        string name
        string type
        string status
    }
```

## 6. Deployment Architecture
Containerized deployment layout, showing how Docker Compose orchestrates the stack locally or in the cloud.

```mermaid
graph TB
    classDef proxy fill:#f43f5e,stroke:#be123c,stroke-width:2px,color:#fff;
    classDef web fill:#0ea5e9,stroke:#0369a1,stroke-width:2px,color:#fff;
    classDef api fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff;
    classDef worker fill:#6366f1,stroke:#4338ca,stroke-width:2px,color:#fff;
    classDef db fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff;

    subgraph Docker Compose Host
        Nginx[Nginx Reverse Proxy]:::proxy
        FrontendCont[Frontend Container :3000]:::web
        BackendCont[FastAPI Container :8000]:::api
        CeleryCont[Celery Worker]:::worker
        RedisCont[(Redis :6379)]:::db
        DBCont[(PostgreSQL :5432)]:::db
        
        Nginx --> FrontendCont
        Nginx --> BackendCont
        FrontendCont --> BackendCont
        BackendCont --> DBCont
        BackendCont --> RedisCont
        CeleryCont --> RedisCont
    end
    
    Internet((Internet)) --> Nginx
```

## 7. Data Flow Diagram
Tracks the lifecycle of IoT sensor data through stream processing into the Predictive Risk models.

```mermaid
flowchart TD
    classDef sensor fill:#94a3b8,stroke:#475569,stroke-width:2px,color:#fff;
    classDef stream fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff;
    classDef db fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff;
    classDef alert fill:#ef4444,stroke:#b91c1c,stroke-width:2px,color:#fff;
    classDef ai fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#fff;

    Sensors((IoT Sensors)):::sensor --> |Telemetry Data| Kafka[Message Queue / Stream]:::stream
    Kafka --> StreamProcessor[Stream Processor]:::stream
    StreamProcessor --> DB[(Time-Series / PostgreSQL)]:::db
    StreamProcessor --> Alerts{Anomaly Detection}:::alert
    Alerts --> |If True| Notification[Trigger Alert / Copilot]:::alert
    DB --> |Historical Data| AIModel[Predictive Risk Model]:::ai
    AIModel --> |Risk Score| Dashboard[Copilot Dashboard]:::ai
```

## 8. Application Workflow
State diagram showing the user journey and dynamic AI Agent routing based on user intent.

```mermaid
stateDiagram-v2
    classDef main fill:#0ea5e9,color:#fff,stroke-width:2px,stroke:#0369a1
    classDef agent fill:#8b5cf6,color:#fff,stroke-width:2px,stroke:#6d28d9
    classDef action fill:#10b981,color:#fff,stroke-width:2px,stroke:#047857

    [*] --> Dashboard : Access App
    Dashboard --> ChatCopilot : Ask Question
    ChatCopilot --> AgentRouting : Analyze Intent
    
    class Dashboard, ChatCopilot main
    
    AgentRouting --> SOPAgent : If procedure query
    AgentRouting --> RiskAgent : If predictive query
    AgentRouting --> IncidentAgent : If failure query
    
    class AgentRouting, SOPAgent, RiskAgent, IncidentAgent agent
    
    SOPAgent --> Response
    RiskAgent --> Response
    IncidentAgent --> Response
    
    Response --> ChatCopilot : Display UI
    ChatCopilot --> ExportPDF : User clicks Export
    
    class Response, ExportPDF action
```

## 9. Intelligence Modules Architecture
Maps out the core feature navigation within the application, specifically highlighting the AI-driven "Intelligence" suite.

```mermaid
graph TD
    classDef core fill:#0ea5e9,stroke:#0369a1,stroke-width:2px,color:#fff;
    classDef category fill:#6366f1,stroke:#4338ca,stroke-width:2px,color:#fff;
    classDef module fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff;
    classDef aifeature fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#fff;

    App[Industrial Brain AI]:::core --> Overview[Overview]:::category
    App --> Intelligence[Intelligence]:::category

    Overview --> Dashboard[Dashboard]:::module
    Overview --> DocHub[Document Hub]:::module
    Overview --> PageIndex[Page Index]:::module
    Overview --> Graph[Knowledge Graph]:::module

    Intelligence --> Copilot[AI Copilot]:::aifeature
    Intelligence --> RCA[Root Cause Analysis]:::aifeature
    Intelligence --> Compliance[Regulatory Compliance]:::aifeature
    Intelligence --> FI[Failure Intelligence]:::aifeature
```
