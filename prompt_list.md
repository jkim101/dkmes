# System Prompts Inventory

Current list of hardcoded prompts in `backend/core/gemini_client.py`.

| Prompt ID | Function/Purpose | Location | Description |
|-----------|------------------|----------|-------------|
| **`answer_generation`** | Final Answer Generation | `gemini_client.py` | Generates final answer from retrieved context. Handles "not found" cases. |
| **`graph_extraction`** | GraphRAG Creation | `gemini_client.py` | Extracts Entities and Relationships from text to build Knowledge Graph (Cypher generation). |
| **`rag_evaluation`** | Search Quality Judge | `gemini_client.py` | Evaluates if retrieved context is sufficient for the query. Supports multiple personas (Novice/Intermediate/Expert). |
| **`keyword_extraction`** | Search Optimization | `gemini_client.py` | Extracts semantic keywords from natural language queries for Graph DB search. |
| **`metric_faithfulness`** | Hallucination Detection | `gemini_client.py` | Scores (0.0-1.0) whether the answer is derived solely from the provided context. |
| **`metric_relevance`** | Answer Relevance | `gemini_client.py` | Scores whether the answer directly addresses the user's intent. |
| **`metric_recall`** | Context Recall | `gemini_client.py` | Scores whether the retrieved context contains the known ground truth. |
| **`agent_system`** | Agentic Workflow | `gemini_client.py` | System prompt for autonomous tool usage, planning (ReAct), and reasoning. |
