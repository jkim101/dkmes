import asyncio
from knowledge.vector_provider import VectorProvider

async def main():
    print("Initializing VectorProvider...")
    vp = VectorProvider(persist_directory="./data/chroma_test")
    print("VectorProvider initialized.")
    
    print("Ingesting text...")
    await vp.ingest("Test document")
    print("Ingestion complete.")
    
    print("Searching...")
    results = await vp.search("Test")
    print(f"Search results: {results}")

if __name__ == "__main__":
    asyncio.run(main())
