from abc import ABC, abstractmethod
from typing import List, Dict, Any

class KnowledgeProvider(ABC):
    """
    Abstract base class for different knowledge retrieval modules (Vector, Graph, etc.)
    """

    @abstractmethod
    async def ingest(self, data: Any) -> bool:
        """
        Ingest data into the knowledge base.
        """
        pass

    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for a given query.
        """
        pass
