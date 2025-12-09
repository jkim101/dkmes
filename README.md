<p align="center">
  <img src="https://img.shields.io/badge/Status-Active%20Development-brightgreen" alt="Status"/>
  <img src="https://img.shields.io/badge/Version-1.1.0-blue" alt="Version"/>
  <img src="https://img.shields.io/badge/Agents-3%20Active-orange" alt="Agents"/>
</p>

<h1 align="center">🧠 DKMES</h1>
<h3 align="center">Data Knowledge Management Eco-System</h3>

<p align="center">
  <strong>A Multi-Agent Knowledge Platform utilizing Agent-to-Agent (A2A) Protocol</strong>
</p>

---

## 🎯 What is DKMES?

DKMES is a **Multi-Agent System (MAS)** designed to discover, connect, and leverage organizational knowledge. It goes beyond simple document search by deploying specialized agents that collaborate to solve complex problems.

At its core, DKMES implements the **Agent-to-Agent (A2A) Protocol**, allowing independent AI agents to exchange knowledge, request tasks, and share feedback autonomously.

---

## 🤖 Multi-Agent Architecture

DKMES consists of three specialized agents working in harmony:

| Agent | Name | Role | Port | Focus |
|-------|------|------|------|-------|
| **Alpha** | `dkmes-alpha` | **Orchestrator & Knowledge Core** | `8000` | Manages the central Knowledge Graph, Vector DB, and routing. Serves as the primary interface for users. |
| **Beta** | `agent-beta-aiml` | **AI/ML Researcher** | `8001` | Specialist in Machine Learning, Deep Learning, and AI trends. Provides deep technical insights. |
| **Gamma** | `agent-gamma-analytics` | **Data Analyst** | `8002` | Specialist in data visualization, statistics, and business intelligence. Analyzes datasets and generates charts. |

---

## ✨ Key Features

### 🔌 Agent-to-Agent (A2A) Protocol
- **Autonomous Collaboration**: Agents dynamically discover peers and request help based on domain expertise.
- **Knowledge Exchange**: Standardized JSON-RPC protocol for sharing context and answers.
- **Federated Feedback**: Agents rate each other's responses, improving system quality over time.

### 📚 Hybrid RAG (Retrieval-Augmented Generation)
- **Vector Search**: Finds relevant text chunks via semantic similarity.
- **Graph Search**: Navigates entity relationships to understand context.
- **Hybrid Fusion**: Combines both strategies for superior answer quality.

### 🧪 Evaluation Studio
- **Interactive Mode**: Test RAG strategies (Vector vs Graph vs Hybrid) side-by-side with real-time metrics.
- **Batch Evaluation**: Upload Q&A datasets (JSON) to automatically benchmark system performance.
- **Metrics**: Tracks **Faithfulness**, **Answer Relevance**, and **ROUGE-L** scores.

### 📊 Trace Inspector & Dashboard
- **Full Observability**: Visualize every step of the agent's reasoning process.
- **System Activity**: Monitor query loads, latency trends, and strategy distribution.
- **Visual Knowledge Graph**: Interactive 3D/2D visualization of the organization's knowledge structure.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker (for Redis/FalkorDB)
- Google Cloud Project with Vertex AI API enabled

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/jkim101/dkmes.git
cd dkmes

# 2. Start Infrastructure (Vector DB, Graph DB)
docker-compose up -d

# 3. Start Agent Alpha (Orchestrator)
cd backend
poetry install
poetry run python main.py
# Running on http://localhost:8000

# 4. Start Agent Beta (AI/ML) - In a new terminal
cd ../agent_beta
pip install -r requirements.txt
python main.py
# Running on http://localhost:8001

# 5. Start Agent Gamma (Analytics) - In a new terminal
cd ../agent_gamma
poetry install
poetry run python main.py
# Running on http://localhost:8002

# 6. Start Frontend Dashboard - In a new terminal
cd ../frontend
npm install
npm run dev
# Access at http://localhost:5173
```

---

## 🎯 Use Cases

- **Complex Problem Solving**: A user asks "How can we apply LLMs to our sales data?". Alpha decomposes the task, queries Beta for LLM techniques, queries Gamma for sales data analysis, and synthesizes a complete strategy.
- **Knowledge Gap Analysis**: The system proactively identifies missing links in the knowledge graph.
- **Automated Research**: Beta agent monitors arXiv for new papers and updates the knowledge base automatically.

---

<p align="center">
  <i>"Individual agents are smart. Together, they are intelligent."</i>
</p>
