from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions
from .provider import KnowledgeProvider
import uuid
from core.config import current_settings

class VectorProvider(KnowledgeProvider):
    def __init__(self, collection_name: str = "dkmes_docs", persist_directory: str = "./data/chroma"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use a default embedding function (all-MiniLM-L6-v2 is standard and fast)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )

    async def ingest(self, text: str) -> bool:
        """
        Ingests text into ChromaDB.
        Splits text into chunks (simple splitting for now) and stores them.
        """
        try:
            # Chunking logic using current_settings
            chunks = self._chunk_text(text) 
            
            ids = [str(uuid.uuid4()) for _ in chunks]
            metadatas = [{"source": "user_input"} for _ in chunks]
            
            self.collection.add(
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            print(f"Ingested {len(chunks)} chunks into Vector DB.")
            return True
        except Exception as e:
            print(f"Error ingesting into Vector DB: {e}")
            return False

    def _chunk_text(self, text: str) -> List[str]:
        """
        Splits text into chunks based on SystemSettings.
        """
        chunk_size = current_settings.chunk_size
        chunk_overlap = current_settings.chunk_overlap
        
        if not text:
            return []
            
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + chunk_size, text_len)
            
            # Simple attempt to not cut words in half if possible
            if end < text_len:
                # Look for last space within the last 100 chars of the chunk to break cleanly
                last_space = text.rfind(' ', start, end)
                if last_space != -1 and (end - last_space) < 100:
                    end = last_space
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start forward, respecting overlap
            start = max(start + 1, end - chunk_overlap)
            
        return chunks

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Performs semantic search using vector embeddings.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        # Format results to match the expected output
        formatted_results = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "score": results['distances'][0][i] if results['distances'] else 0.0
                })
        
        return formatted_results

    async def get_stats(self) -> Dict[str, int]:
        """
        Returns statistics about the vector collection.
        """
        count = self.collection.count()
        return {"vector_chunks": count}

    async def clear(self) -> bool:
        """
        Clears the vector collection.
        """
        try:
            # Delete and recreate
            self.client.delete_collection(self.collection.name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection.name,
                embedding_function=self.embedding_fn
            )
            return True
        except Exception as e:
            print(f"Error clearing Vector DB: {e}")
            return False
