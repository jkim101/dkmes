# 🧠 DKMES (Data Knowledge Management Eco-System) Comprehensive Documentation

This document serves as a comprehensive guide detailing the usage, features, metrics, and technology specification of the DKMES system.

---

## 📑 Table of Contents

1. [Introduction](#1-introduction)
2. [User Manual](#2-user-manual)
3. [Feature Guide](#3-feature-guide)
4. [Metrics Reference](#4-metrics-reference)
5. [Technology Specification](#5-technology-specification)

---

## 1. Introduction

**DKMES** is a hybrid knowledge management platform that combines Vector and Graph technologies to manage distributed data and tacit knowledge within an organization. Going beyond simple document search, it visualizes relationships between concepts and supports complex problem-solving through Multi-Agent collaboration.

---

## 2. User Manual

### 2.1 Dashboard
The first screen seen upon accessing the system, showing the overall status of the knowledge base.

*   **Stats Cards**
    *   **Vector Chunks**: Total number of text chunks currently indexed (embedded) in the system.
    *   **Graph Nodes**: Number of unique entities registered in the Knowledge Graph.
    *   **Relationships**: Number of edges connecting concepts.
    *   **System Status**: Indicates the connection status (Online/Offline) of the backend system and DBs.

*   **System Activity Charts**
    *   **Time Range Toggle**: Click `24h` or `7 Days` to change the chart's time basis.
    *   **Query Activity**: Line/Area chart showing the frequency of user queries over time.
    *   **RAG Strategy Distribution**: Pie chart showing the ratio of strategies (Vector, Graph, Hybrid) used for processing queries.
    *   **Response Latency Trend**: Shows the trend of time taken to generate responses (in seconds), including Min/Max/Avg latency.

### 2.2 Data Manager
The page for ingesting new knowledge into the system.

*   **Upload Area**: Drag and drop files or click to select.
*   **Upload Mode Selection**
    *   **Append (Default)**: Adds new data to the existing knowledge base.
    *   **Replace All**: **Clears** all existing vector and graph data and rebuilds the knowledge base with the currently uploaded file. **Warning**: This action cannot be undone.
*   **Process File Button**: Starts the upload and indexing process. Progress is displayed step-by-step.
*   **Indexed Files List**: Check the list, size, and upload date of files currently stored in the system.

### 2.3 Playground
A chat interface for conversing with AI agents to search for information.

*   **RAG Strategy Selection**
    *   **Vector Only**: Answering quickly using only similarity search.
    *   **Graph Only**: Answering by exploring relationships in the Knowledge Graph.
    *   **Hybrid (Best)**: Combines both methods to provide the richest answer. (Recommended)
*   **Fusion Mode**: When enabled, sends the query to Peer Agents (e.g., Agent Beta) in other domains to synthesize information.
*   **Chat Input**: Enter a question and press Enter or the send icon.
*   **Response Area**: Displays the AI's answer along with visual indicators of the **Context** and **Graph** used as the basis.

### 2.4 Evaluation Studio
An expert tool for quantitatively evaluating and comparing the quality of RAG system answers.

*   **Mode Tabs**
    *   **Interactive Mode**: Simultaneously runs Vector, Graph, and Hybrid strategies for a single query to compare them.
    *   **Batch Mode**: Uploads a prepared Q&A dataset (JSON) to evaluate a large number of questions in batch.
*   **Interactive Settings**
    *   **Persona**: Sets a virtual user persona (Novice, Intermediate, Expert) as the evaluation criteria. The definition of a 'good answer' changes based on the persona.
*   **Results Screen**: Displays Scores and Radar Charts (Faithfulness, Relevance, ROUGE) for each strategy.

### 2.5 Graph Explorer
Visualizes and explores the constructed Knowledge Graph in 3D.

*   **Search Bar**: Search for a specific node (concept) to center the view on it.
*   **3D Viewer**: Rotate with mouse drag, Zoom In/Out with wheel. Click a node to see detailed information.
*   **Node Color**: Colors are differentiated based on node importance or type.

### 2.6 Trace Inspector
Inspects the internal operation process of the system like a microscope.

*   **Trace List**: A list of all recently executed request traces. Displays Success/Failure status and duration.
*   **Span Details**: Clicking a trace reveals the timeline of detailed internal steps (Retrieval, LLM Generation, Graph Query, etc.) and input/output data. Useful for debugging.

### 2.7 Orchestrator
Manages the Multi-Agent system.

*   **Registered Agents**: Shows the list of agents currently participating in the network and their status (Active/Inactive).
*   **Knowledge Exchange Log**: Checks the log of knowledge exchanged (Query & Response) between agents.

### 2.8 Settings
Adjusts system parameters.

*   **LLM Parameters**: Gemini model selection, Temperature (Creativity), Max Tokens (Length).
*   **RAG Strategy**: Default retrieval strategy and number of results (Top K).
*   **Ingestion Config**: Document Chunking size and Overlap size settings.
*   **Save Configuration**: Saves changes to the backend and applies them immediately.

---

## 3. Feature Guide

### 3.1 Hybrid Retrieval
The DKMES search engine operates via two concurrent paths:
1.  **Semantic Search (Vector)**: Converts the user's question into a vector to find semantically similar text chunks in ChromaDB. Good for finding contextually similar content.
2.  **Structural Search (Graph)**: Extracts key keywords from the question to explore the Knowledge Graph in FalkorDB. Powerful for structural questions like "What is the relationship between A and B?".
3.  **Reranking & Synthesis**: Merges the two results (Fusion) and uses them as optimal context when the LLM generates the final answer.

### 3.2 Auto-KG Construction
When a user uploads a document, the backend's `GeminiSpec` analyzes the text to perform:
1.  **Entity Extraction**: Extracts important concepts (Nouns, Proper Nouns). (e.g., "Project Alpha", "Q3 Deadline")
2.  **Relationship Extraction**: Defines relationships between concepts using verbs or prepositional phrases. (e.g., "Project Alpha" -[HAS_DEADLINE]-> "Q3 Deadline")
3.  **Cypher Query Generation**: Converts extracted information into Graph DB queries (Cypher) and stores them in FalkorDB.

### 3.3 Knowledge Exchange Protocol (KEP)
A standard protocol for collaboration between agents with different domain knowledge (e.g., Agent Alpha-Data, Agent Beta-AI).
1.  User asks a complex question. (e.g., "AI models required for building a Data Lakehouse?")
2.  Agent Alpha (Local) finds information related to "Data Lakehouse".
3.  Simultaneously sends a signal (Request) to Agent Beta (Remote) asking about "AI models".
4.  Synthesizes respective answers to present a unified response to the user.

---

## 4. Metrics Reference

DKMES evaluates answer quality using 3 key metrics based on the **RAGAS (Retrieval Augmented Generation Assessment)** framework. All scores are floats between 0.0 and 1.0.

### 4.1 Faithfulness
*   **Definition**: Measures if the generated answer is based **only on the provided Context**. Scores drop if external knowledge or hallucinations are mixed in.
*   **Calculation**: LLM checks (Context, Answer) pairs to determine "Are all sentences in the Answer supported by the Context?".
*   **Purpose**: Prevention of false information generation (Hallucination).

### 4.2 Answer Relevance
*   **Definition**: Measures how relevant the generated answer is to the **User's original Question**. Scores drop for irrelevant answers.
*   **Calculation**: LLM evaluates (Question, Answer) pairs to determine "Does the Answer address the intent of the Question?".
*   **Purpose**: Ensuring user satisfaction and response utility.

### 4.3 Context Recall
*   **Definition**: Measures if the retrieved Context contains all necessary information to derive the Ground Truth. (Calculated only in Batch Mode when Ground Truth exists)
*   **Calculation**: LLM checks (Ground Truth, Context) pairs to determine "Do key facts from Ground Truth exist within the Context?".
*   **Purpose**: Evaluation of Search Engine (Retrieval) performance.

### 4.4 System Metrics
*   **Latency (sec)**: Total time elapsed from when the user inputs a question until the answer starts rendering.
*   **Throughput (Chunk/sec)**: Number of document chunks processed per second in the Data Manager.

---

## 5. Technology Specification

### 5.1 Frontend (User Interface)
*   **Framework**: [React](https://react.dev/) v18.2.0
*   **Build Tool**: [Vite](https://vitejs.dev/) v5.2.0
*   **Language**: TypeScript
*   **Charting**: [Recharts](https://recharts.org/) v3.5.1 (Dashboard Charts)
*   **Graph Visualization**: `react-force-graph-3d` (Knowledge Graph Rendering)
*   **Icons**: `lucide-react`
*   **Styling**: CSS Modules + Vanilla CSS Variables

### 5.2 Backend (API & Core Logic)
*   **Framework**: [FastAPI](https://fastapi.tiangolo.com/) v0.109.0 (Python 3.10+)
*   **Server**: Uvicorn (ASGI Server)
*   **AI Engine**:
    *   **LLM Model**: Google Gemini Pro / Flash (via `google-generativeai` SDK)
    *   **Embeddings**: `sentence-transformers` (Local Embedding) or Gemini Embedding
*   **Databases**:
    *   **Vector DB**: [ChromaDB](https://www.trychroma.com/) (Persistent Local Storage)
    *   **Graph DB**: [FalkorDB](https://www.falkordb.com/) (Dockerized RedisGraph) via `falkordb-python` client
    *   **Trace/Meta DB**: SQLite (`traces.db`, `assessment.db`)

### 5.3 Infrastructure & Deployment
*   **Containerization**: Docker & Docker Compose
*   **Port Mapping**:
    *   Frontend: `5174`
    *   Agent Alpha (Backend): `8000`
    *   Agent Beta (Peer): `8001`
    *   FalkorDB: `6379`
*   **Environment Variables**: Manage API Keys and settings in `.env.local` file
