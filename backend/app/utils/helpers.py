import re
import uuid
import logging
from datetime import datetime
from typing import Optional, List
import json

def extract_video_id(url: str, platform: str) -> str:
    """Extract video ID from YouTube or Instagram URL"""
    if platform == 'youtube':
        patterns = [
            r'(?:youtube\.com\/watch\?v=)([\w-]+)',
            r'(?:youtu\.be\/)([\w-]+)',
            r'(?:youtube\.com\/embed\/)([\w-]+)',
            r'(?:youtube\.com\/shorts\/)([\w-]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
    elif platform == 'instagram':
        patterns = [
            r'(?:instagram\.com\/reel\/)([\w-]+)',
            r'(?:instagram\.com\/p\/)([\w-]+)',
            r'(?:instagram\.com\/tv\/)([\w-]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
    
    raise ValueError(f"Could not extract {platform} video ID from URL: {url}")

def generate_session_id() -> str:
    """Generate unique session ID"""
    return str(uuid.uuid4())[:8]

def format_duration(seconds: Optional[int]) -> str:
    """Format duration in seconds to MM:SS"""
    if not seconds:
        return "N/A"
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:02d}"

def format_number(num: Optional[int]) -> str:
    """Format large numbers with K/M/B suffix"""
    if not num:
        return "N/A"
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.1f}B"
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    if num >= 1_000:
        return f"{num/1_000:.1f}K"
    return str(num)

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[dict]:
    """
    Split text into overlapping chunks with metadata
    Returns list of chunks with index and timestamps if available
    """
    if not text:
        return []
    
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        chunk_text = ' '.join(chunk_words)
        
        chunks.append({
            'index': len(chunks),
            'text': chunk_text,
            'start_char': i * len(words[0]) if words else 0,
            'end_char': (i + len(chunk_words)) * len(words[0]) if words else 0,
            'word_count': len(chunk_words)
        })
        
        if i + chunk_size >= len(words):
            break
    
    return chunks

def safe_json_parse(json_str: str) -> dict:
    """Safely parse JSON with error handling"""
    try:
        return json.loads(json_str)
    except:
        return {}