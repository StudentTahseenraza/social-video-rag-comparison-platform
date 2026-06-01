import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # OpenRouter API
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    
    # App Settings
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # RAG Settings
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "500"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    top_k_results: int = int(os.getenv("TOP_K_RESULTS", "5"))
    
    # LLM Settings
    llm_model: str = os.getenv("LLM_MODEL", "openai/gpt-3.5-turbo")
    temperature: float = float(os.getenv("TEMPERATURE", "0.7"))
    
    # Video Processing
    max_video_size_mb: int = int(os.getenv("MAX_VIDEO_SIZE_MB", "100"))
    temp_dir: str = os.getenv("TEMP_DIR", "/tmp/rag_chatbot")

settings = Settings()