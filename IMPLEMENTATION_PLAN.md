# DKMES Detailed Implementation Plan

## Phase 1: Foundation & Google Cloud Setup
**Goal**: Initialize the project with Google Cloud integration and a basic "Walking Skeleton".
- [x] **Project Initialization**
    - [x] Create Git repository and directory structure (`/backend`, `/frontend`, `/lib`).
    - [x] **Backend**: Set up Python Poetry project with `fastapi`, `google-cloud-aiplatform`, `uvicorn`.
    - [x] **Frontend**: Set up React + Vite + TypeScript project.
- [x] **Google Vertex AI Integration**
    - [x] Configure GCP Credentials (Service Account).
    - [x] Implement `GeminiClient` wrapper to handle API calls to Gemini Pro.
    - [x] Create a simple test script to verify Gemini connectivity.
- [x] **Basic API & UI**
    - [x] Implement `POST /api/v1/evaluate` (Mock response).
    - [x] Build a "Hello World" React page that calls this API.

## Phase 2: Knowledge Core (The "Brain")
**Goal**: Implement the modular knowledge system, referencing `hybrid-rag-system`.
- [ ] **Hybrid RAG Analysis**
    - [ ] Clone/Inspect `hybrid-rag-system` (if available) or review its logic.
    - [ ] Extract key logic for:
        - Graph construction (Nodes/Edges).
        - Hybrid retrieval strategies (Vector + Graph).
- [ ] **Knowledge Manager Implementation**
    - [ ] Define `KnowledgeProvider` interface.
    - [x] **Vector Module**: Implement using `ChromaDB` (local) or `Vertex AI Vector Search`.
    - [x] **Graph Module**: Implement using **FalkorDB** (Low-latency Graph Database).
        - Reference: [FalkorDB Website](https://www.falkordb.com/)
        - **[x]**: Implement **LLM-based Graph Construction** (replacing rule-based logic).
            - Use Gemini to extract Entities and Relationships from unstructured text/schema.
    - [ ] **Router**: Implement logic to choose between or combine modules.

## Phase 3: Evaluation Engine (The "Teacher")
**Goal**: Build the grading system using Gemini.
- [ ] **LLM Judge (Gemini)**
    - [ ] Design System Prompts for Gemini to act as a "Strict Data Engineer".
    - [ ] Implement `JudgeService` that takes (User Answer, Golden Answer, Context) and returns a Score + Feedback.
- [ ] **Benchmarking Suite**
    - [ ] Create a schema for Test Cases (`json` or `yaml`).
    - [ ] Port evaluation metrics/logic from `hybrid-rag-system`.
    - [ ] Implement a runner to batch-process test cases and calculate aggregate scores.

## Phase 4: Observability & Web Portal
**Goal**: Visualize the process.
- [ ] **Trace Logging**
    - [ ] Middleware to capture every Request/Response/LLM Call.
    - [ ] Store traces in a lightweight DB (e.g., SQLite or Firestore).
- [ ] **Interaction Inspector UI**
    - [ ] **Trace List**: Table showing recent agent interactions.
    - **Detail View**:
        - Show the exact Prompt sent to Gemini.
        - Show the retrieved Context chunks.
        - Show the JSON feedback returned.

## Phase 5: Pilot & Refinement
- [x] **Pilot Data Ingestion**
    - [x] Ingest sample datasets (e.g., General knowledge PDFs) into the Graph.
    - [x] Upload sample documentation to the Vector Store.
- [x] **End-to-End Test**
    - [x] Simulate an External Agent asking a question.
    - [x] Verify DKMES retrieves context, judges the answer, and returns feedback.

## Phase 6: Deployment & Packaging (Future)
**Goal**: Package the application for production deployment.
- [ ] **Dockerization**
    - [ ] Create `Dockerfile` for Backend (FastAPI).
    - [ ] Create `Dockerfile` for Frontend (Nginx/React).
    - [ ] Update `docker-compose.yml` to orchestrate all services (App, DBs).
- [ ] **CI/CD**
    - [ ] Set up GitHub Actions for automated testing and building.
