# DKMES System Architecture

## High-Level Diagram
```mermaid
graph TD
    subgraph "External World"
        EA[External Agent]
        DE[Data Engineer]
    end

    subgraph "DKMES Core"
        API[API Gateway / Interface Layer]
        
        subgraph "Knowledge Core (Pluggable)"
            KM[Knowledge Manager / Router]
            KB1[Module: Standard RAG]
            KB2[Module: GraphRAG]
            KB3[Module: LightRAG]
            KB_New[Module: Future KB...]
        end
        
        subgraph "Evaluation & Benchmarking"
            Judge[LLM Judge]
            Bench[Benchmark Engine]
        end
        
        subgraph "Management & Observability"
            TraceDB[(Trace/Log Store)]
            AdminUI[Web Portal (React)]
        end
    end

    DE -->|Configures| KM
    DE -->|Runs Experiments| Bench
    DE -->|Inspects Traces| AdminUI
    
    AdminUI -->|Reads| TraceDB
    
    KM -->|Routes Query| KB1
    KM -->|Routes Query| KB2
    KM -->|Routes Query| KB3

    EA -->|1. Request Context| API
    EA -->|2. Submit Solution| API
    
    API -->|Log Interaction| TraceDB
    API -->|Forward Request| Judge
    
    Judge -->|Retrieve Context| KM
    
    Judge -->|Evaluate| Bench
    Bench -->|3. Feedback & Score| API
    API -->|Return Result| EA
```

## Component Details

### 1. Interface Layer (The "Protocol")
- **Role**: The standard communication channel for all external agents.
- **Tech**: REST API (FastAPI) or GraphQL.
- **Key Endpoints**:
    - `POST /evaluate`: Submit a query/code/answer for evaluation.
    - `GET /context/{topic}`: Retrieve authorized domain knowledge to help the agent.
    - `GET /feedback/{submission_id}`: Get detailed feedback on a past submission.

### 2. Knowledge Core (The "Pluggable Brain")
- **Design Philosophy**: Modular and Agnostic. The system treats different knowledge retrieval strategies as interchangeable plugins.
- **Knowledge Manager**: A router that decides which KB module to use for a given query (or uses multiple for comparison).
- **Supported Modules (Examples)**:
    - **Standard RAG**: Basic Vector DB retrieval (Chroma/Pinecone).
    - **GraphRAG**: Knowledge Graph-based retrieval (**FalkorDB**).
    - **LightRAG**: Lightweight, efficient retrieval methods.
    - **Hybrid**: Combinations of the above.
- **Extensibility**: New methodologies can be added by implementing a standard `KnowledgeProvider` interface.

### 3. Evaluation & Benchmarking Engine
- **Role**: 
    1.  **For External Agents**: Evaluate their answers (Teacher role).
    2.  **For Internal Modules**: Compare performance of different KB modules.
- **LLM Judge**: **Google Gemini Pro / Ultra** via Vertex AI.
    - Leverages long context window for analyzing complex SQL and documentation.
- **Benchmark Suite**:
    - Reference: Logic adapted from `hybrid-rag-system` for rigorous evaluation.
    - A collection of "Golden Q&A Pairs".

### 4. Web Portal (React)
- **Tech Stack**: React (Frontend), FastAPI (Backend).
- **Role**: The central hub for Data Engineers to manage and observe the ecosystem.
- **Key Features**:
    - **Interaction Inspector**: A dedicated UI to visualize the exact JSON/Text payloads exchanged between External Agents and DKMES.
        - *View*: "Agent A asked X, DKMES retrieved Context Y, Judge gave Score Z."
    - **Knowledge Curation**: Visual editor for the Knowledge Graph.
    - **Leaderboard/Stats**: Performance metrics for all registered agents.
