from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from typing import List, Dict
import shutil
import os
import uuid
from pypdf import PdfReader

router = APIRouter(tags=["documents"])

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_document(request: Request, file: UploadFile = File(...), mode: str = Form("append")):
    # Get providers from app.state (shared with main.py)
    vector_provider = request.app.state.vector_provider
    graph_provider = request.app.state.graph_provider
    
    try:
        # Handle replace mode - clear all existing data
        if mode == "replace":
            # Clear uploaded files
            if os.path.exists(UPLOAD_DIR):
                for filename in os.listdir(UPLOAD_DIR):
                    file_path_to_delete = os.path.join(UPLOAD_DIR, filename)
                    if os.path.isfile(file_path_to_delete):
                        os.remove(file_path_to_delete)
            
            # Clear Vector DB
            await vector_provider.clear()
            
            # Clear Graph DB
            await graph_provider.clear()
            
            print("🔄 Replace mode: Cleared all existing data")
        
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
