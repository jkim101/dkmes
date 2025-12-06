"""
Ingest AI/ML documents into Agent Beta's vector store.
"""

import os
import sys
import asyncio

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from knowledge.vector_provider import VectorProvider


async def ingest_documents():
    """Ingest all markdown documents from aiml_docs folder."""
    
    # Initialize Beta's vector store
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    chroma_dir = os.path.join(data_dir, "chroma_beta")
    docs_dir = os.path.join(data_dir, "aiml_docs")
    
    os.makedirs(chroma_dir, exist_ok=True)
    
    vector_provider = VectorProvider(
        collection_name="agent_beta_docs",
        persist_directory=chroma_dir
    )
    
    # Find all markdown files
    doc_files = [f for f in os.listdir(docs_dir) if f.endswith('.md')]
    
    print(f"\n{'='*60}")
    print(f"  Agent Beta Document Ingestion")
    print(f"{'='*60}\n")
    
    for doc_file in doc_files:
        doc_path = os.path.join(docs_dir, doc_file)
        
        with open(doc_path, 'r') as f:
            content = f.read()
        
        print(f"📄 Ingesting: {doc_file}")
        print(f"   Size: {len(content)} characters")
        
        success = await vector_provider.ingest(content)
        
        if success:
            print(f"   ✅ Successfully ingested")
        else:
            print(f"   ❌ Failed to ingest")
    
    # Show stats
    stats = await vector_provider.get_stats()
    print(f"\n📊 Vector Store Stats:")
    print(f"   Chunks: {stats.get('vector_chunks', 0)}")
    print(f"\n✅ Ingestion complete!")


if __name__ == "__main__":
    asyncio.run(ingest_documents())
