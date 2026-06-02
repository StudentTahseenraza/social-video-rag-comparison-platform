from fastapi import FastAPI, HTTPException, BackgroundTasks
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
    logger.info("=" * 50)
    logger.info("Starting RAG Video Chatbot API v1.0.0")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"LLM Model: {settings.llm_model}")
    logger.info(f"Embedding Model: {settings.embedding_model}")
    logger.info(f"Chunk Size: {settings.chunk_size}")
    logger.info("=" * 50)
    
    # Initialize services
    try:
        from app.services.llm_service import llm_service
        await llm_service.initialize()
        logger.info("✅ LLM Service initialized")
    except Exception as e:
        logger.error(f"❌ LLM Service failed: {str(e)}")
    
    try:
        from app.services.vector_store import vector_store
        await vector_store.initialize()
        logger.info("✅ Vector Store initialized")
        stats = await vector_store.get_collection_stats()
        logger.info(f"   Vector DB stats: {stats}")
    except Exception as e:
        logger.warning(f"⚠️ Vector Store initialization failed: {str(e)}")
        logger.warning("   Continuing without vector DB...")
    
    yield
    
    # Shutdown
    logger.info("Shutting down RAG Chatbot API...")
    await rag_service.cleanup()
    logger.info("Shutdown complete")

app = FastAPI(
    title="RAG Video Chatbot API",
    description="API for comparing YouTube and Instagram videos using RAG",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",           # Local development
        "http://localhost:3000",            # Local alternative
        "https://social-video-rag-comparison-platfor.vercel.app",  # Your Vercel URL
        "https://*.vercel.app",              # All Vercel preview deployments
        "https://social-video-rag-comparison-platform-1.onrender.com",  # Self URL
    ],
    allow_credentials=True,
    allow_methods=["*"],                     # Allow all HTTP methods
    allow_headers=["*"],                     # Allow all headers
    expose_headers=["*"],
)

# Include router with /api/v1 prefix
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "RAG Video Chatbot API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "environment": settings.environment,
        "timestamp": asyncio.get_event_loop().time()
    }