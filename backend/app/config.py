from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    google_api_key: str
    qdrant_url: Optional[str] = None
    qdrant_api_key: Optional[str] = None
    youtube_api_key: Optional[str] = None
    redis_url: str = "redis://localhost:6379"
    
    # App Settings
    environment: str = "development"
    debug: bool = True
    
    # RAG Settings
    chunk_size: int = 500
    chunk_overlap: int = 50
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    top_k_results: int = 5
    
    # LLM Settings
    llm_model: str = "gemini-1.5-flash"
    temperature: float = 0.7
    
    # Video Processing
    max_video_size_mb: int = 100
    temp_dir: str = "/tmp/rag_chatbot"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()