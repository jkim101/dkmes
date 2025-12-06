<p align="center">
  <img src="https://img.shields.io/badge/Status-Active%20Development-brightgreen" alt="Status"/>
  <img src="https://img.shields.io/badge/Version-1.0.0-blue" alt="Version"/>
</p>

<h1 align="center">🧠 DKMES</h1>
<h3 align="center">Data Knowledge Management Eco-System</h3>

<p align="center">
  <strong>An intelligent knowledge management platform that discovers, connects, and leverages organizational tacit knowledge</strong>
</p>

---

## 🎯 What is DKMES?

DKMES is an intelligent platform that **connects scattered data and knowledge across your organization**.

Traditional knowledge management systems merely store and search documents. But true knowledge exists not just in documents, but in the **relationships between data**, **hidden patterns**, and **tacit expertise**.

DKMES discovers this **invisible knowledge** and delivers it to the right people at the right time.

---

## ✨ Key Features

### 📚 Hybrid RAG (Retrieval-Augmented Generation)
- **Vector Search**: Discover relevant information through semantic similarity
- **Graph Search**: Navigate through relationships between concepts
- **Hybrid**: Combine both approaches for optimal context retrieval

### 🕸️ Knowledge Graph
- Automatically extract **entities** and **relationships** from documents
- Explore knowledge connections intuitively with 3D visualization
- Discover hidden patterns and knowledge gaps

### 🤖 Multi-Agent Collaboration
- AI agents with different domain expertise work together
- **Knowledge Exchange Protocol (KEP)** enables distributed knowledge utilization
- Handle complex questions that a single agent cannot solve

### 📊 RAG Evaluation Studio
- **Real-time comparison** of Vector, Graph, and Hybrid strategies
- RAGAS-based evaluation metrics (Faithfulness, Relevance, Recall)
- Batch evaluation for large-scale quality verification

### 🔍 Trace Inspector
- **Transparent tracking** of all RAG pipeline operations
- Visualize the complete flow: Retrieval → Context → Answer Generation
- Insights for debugging and optimization

---

## 🌟 Why DKMES?

| Traditional Approach | DKMES |
|---------------------|-------|
| Relies on keyword search | Hybrid semantic + relationship-based search |
| Only stores documents | Automatically builds knowledge graphs from documents |
| Single-perspective answers | Rich insights through multi-agent collaboration |
| Black-box AI | Transparent reasoning process with evaluation metrics |

---

## 🚀 Getting Started

```bash
# 1. Clone the repository
git clone https://github.com/jkim101/dkmes.git
cd dkmes

# 2. Start Graph DB with Docker
docker-compose up -d

# 3. Run the backend
cd backend
poetry install
poetry run uvicorn main:app --reload --port 8000

# 4. Run the frontend (new terminal)
cd frontend
npm install
npm run dev
```

**Access**: http://localhost:5174

---

## 🎯 Use Cases

- **Enterprise Knowledge Management**: Unified search across scattered internal documents, wikis, and notes
- **Research Analysis**: Visualize key concept relationships in papers and reports
- **Customer Support Enhancement**: Intelligently connect past cases with solutions
- **Accelerated Onboarding**: Help new employees quickly access organizational tacit knowledge

---

<p align="center">
  <i>"Knowledge gains power when connected."</i>
</p>
