import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.rag_engine import RAGEngine
from backend import config
from qdrant_client import QdrantClient
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize RAG Engine on startup inside the worker process
    # This avoids double-locking the local Qdrant database during uvicorn imports
    app.state.rag_engine = RAGEngine()
    yield

app = FastAPI(title="HR Copilot AI API", version="1.0.0", lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    top_k: int = 10

class ChatResponse(BaseModel):
    answer: str
    chunks: list[dict]

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, http_request: Request):
    if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your_openai_api_key_here":
        raise HTTPException(
            status_code=500, 
            detail="OpenAI API Anahtarı (.env dosyası) ayarlanmamış. Lütfen root dizindeki .env dosyasını güncelleyin."
        )
    
    try:
        rag_engine = http_request.app.state.rag_engine
        # 1. Search for related chunks
        chunks = rag_engine.search(request.message, limit=request.top_k)
        
        # 2. Generate answer
        answer = rag_engine.generate_answer(request.message, chunks)
        
        return ChatResponse(answer=answer, chunks=chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")
async def search_endpoint(request: SearchRequest, http_request: Request):
    try:
        rag_engine = http_request.app.state.rag_engine
        chunks = rag_engine.search(request.query, limit=request.limit)
        return {"chunks": chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def status_endpoint(http_request: Request):
    openai_configured = bool(config.OPENAI_API_KEY and config.OPENAI_API_KEY != "your_openai_api_key_here")
    
    qdrant_configured = False
    collection_exists = False
    total_points = 0
    
    try:
        # Re-use the existing client from rag_engine to prevent database locking
        rag_engine = http_request.app.state.rag_engine
        qc = rag_engine.qdrant_client
        qdrant_configured = True
        
        collections = qc.get_collections()
        collection_names = [c.name for c in collections.collections]
        if config.COLLECTION_NAME in collection_names:
            collection_exists = True
            collection_info = qc.get_collection(config.COLLECTION_NAME)
            total_points = collection_info.points_count
    except Exception as e:
        print(f"Error checking Qdrant status: {e}")
        
    return {
        "status": "healthy",
        "openai_configured": openai_configured,
        "qdrant_configured": qdrant_configured,
        "collection_exists": collection_exists,
        "total_points": total_points,
        "collection_name": config.COLLECTION_NAME
    }

if __name__ == "__main__":
    # Disable reload to avoid double import locking of SQLite/Qdrant
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)
