from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
from contextlib import asynccontextmanager

from app.config import settings
from app.api.routes import router
from app.services.rag_service import rag_service
from app.utils.helpers import setup_logging

# Setup logging
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting RAG Chatbot API...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"LLM Model: {settings.llm_model}")
    
    # Initialize services
    from app.services.llm_service import llm_service
    await llm_service.initialize()
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await rag_service.cleanup()

app = FastAPI(
    title="RAG Video Chatbot",
    description="Chat with YouTube and Instagram videos using RAG",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "RAG Video Chatbot API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "environment": settings.environment}