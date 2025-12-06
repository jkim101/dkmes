from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List, Dict
import shutil
import os
import uuid
from pypdf import PdfReader
from knowledge.graph_provider import GraphProvider
from knowledge.vector_provider import VectorProvider
from core.gemini_client import GeminiClient

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Global providers (in a real app, use dependency injection)
# We will initialize these in main.py and pass them or use a singleton pattern
# For now, we'll instantiate them here if they are stateless enough, 
# OR better, we rely on the main app to pass them. 
# But to keep it simple and working with the existing main.py structure, 
# let's import the singletons if possible, or re-instantiate (careful with connections).

# Actually, let's just re-instantiate for now as they seem to manage their own connections.
# Ideally, we should refactor main.py to use `app.state.graph_provider`.
gemini_client = GeminiClient() # Re-uses env vars
graph_provider = GraphProvider(gemini_client=gemini_client)
vector_provider = VectorProvider()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename)[1].lower()
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Process immediately (or use BackgroundTasks)
        text_content = ""
        
        if file_ext == ".pdf":
            reader = PdfReader(file_path)
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
        elif file_ext in [".txt", ".md", ".csv"]:
            with open(file_path, "r", encoding="utf-8") as f:
                text_content = f.read()
        else:
            return {"message": "File saved but format not supported for auto-ingestion", "filename": file.filename}

        if text_content:
            # Ingest into Vector DB
            await vector_provider.ingest(text_content)
            
            # Ingest into Graph DB
            await graph_provider.ingest(text_content)

        return {
            "id": file_id,
            "filename": file.filename,
            "status": "processed",
            "message": "File uploaded and ingested successfully"
        }
        
    except Exception as e:
        print(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def list_documents():
    files = []
    if os.path.exists(UPLOAD_DIR):
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                files.append({
                    "filename": filename,
                    "size": os.path.getsize(file_path),
                    "status": "processed" # Assuming all in this dir are processed
                })
    return files
