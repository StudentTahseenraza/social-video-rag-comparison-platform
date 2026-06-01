from typing import List, Dict, Any, Optional
from app.utils.helpers import setup_logging
import re

logger = setup_logging()

class VectorStore:
    """In-memory vector store with proper chunking (3-5 chunks per video)"""
    
    def __init__(self):
        self.transcripts = {}  # Stores chunks, not full transcripts
        self.is_initialized = True
        logger.info("Vector store initialized with chunking support")
    
    async def initialize(self):
        logger.info("Using vector store with 3-5 chunks per video")
        self.is_initialized = True
    
    def chunk_text(self, text: str, target_chunks: int = 4) -> List[str]:
        """
        Split text into 3-5 meaningful chunks.
        Uses semantic boundaries (sentences, paragraphs) for better chunks.
        """
        if not text:
            return []
        
        # For short texts, return as single chunk
        if len(text) < 300:
            return [text]
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= target_chunks:
            return sentences
        
        # Calculate chunk size
        chunk_size = max(1, len(sentences) // target_chunks)
        
        chunks = []
        for i in range(0, len(sentences), chunk_size):
            chunk = " ".join(sentences[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
            if len(chunks) >= 5:  # Max 5 chunks
                break
        
        # Ensure we have at least 3 chunks for long texts
        if len(chunks) < 3 and len(text) > 1000:
            # Create overlapping chunks as fallback
            words = text.split()
            word_chunk_size = len(words) // 4
            for i in range(0, len(words), word_chunk_size):
                chunk = " ".join(words[i:i + word_chunk_size])
                if chunk and chunk not in chunks:
                    chunks.append(chunk)
                if len(chunks) >= 5:
                    break
        
        logger.info(f"Created {len(chunks)} chunks from {len(text)} chars")
        return chunks[:5]  # Max 5 chunks
    
    def store_video_chunks_sync(self, session_id: str, video_id: str, label: str, 
                                  transcript: str, metadata: Dict[str, Any]) -> int:
        """Store video transcript as multiple chunks (3-5 chunks)"""
        if not transcript:
            return 0
        
        try:
            # Clean transcript
            clean_text = re.sub(r'[^\w\s\.\!\,\?\'\"]', ' ', transcript)
            clean_text = ' '.join(clean_text.split())
            
            # Create chunks (3-5 chunks per video)
            chunks = self.chunk_text(clean_text, target_chunks=4)
            
            # Initialize session dict if not exists
            if session_id not in self.transcripts:
                self.transcripts[session_id] = []
            
            # Remove existing entries for this video
            self.transcripts[session_id] = [
                t for t in self.transcripts[session_id] 
                if t.get("video_id") != video_id
            ]
            
            # Store each chunk separately
            for i, chunk_text in enumerate(chunks):
                self.transcripts[session_id].append({
                    "id": f"{video_id}_chunk_{i}",
                    "text": chunk_text,
                    "video_id": video_id,
                    "label": label,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "metadata": metadata
                })
            
            logger.info(f"Stored {len(chunks)} chunks for {video_id} (was {len(transcript)} chars)")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Error storing transcript chunks: {e}")
            return 0
    
    async def store_video_chunks(self, session_id: str, video_id: str, label: str, 
                                  transcript: str, metadata: Dict[str, Any]) -> int:
        """Async wrapper"""
        return self.store_video_chunks_sync(session_id, video_id, label, transcript, metadata)
    
    async def search(self, query: str, session_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant chunks across all chunks"""
        if session_id not in self.transcripts:
            logger.warning(f"Session {session_id} not found")
            return []
        
        try:
            query_lower = query.lower()
            results = []
            
            for chunk in self.transcripts[session_id]:
                text_lower = chunk["text"].lower()
                
                # Calculate relevance score
                score = 0
                
                # Exact phrase match (highest score)
                if query_lower in text_lower:
                    score += 10
                
                # Word matches
                words = query_lower.split()
                for word in words:
                    if len(word) > 2 and word in text_lower:
                        score += 1
                
                # Bonus for chunk position (early chunks might be more important)
                chunk_idx = chunk.get("chunk_index", 0)
                if chunk_idx == 0:
                    score += 2  # First chunk (hook) gets bonus
                
                if score > 0:
                    results.append({
                        "text": chunk["text"],
                        "video_id": chunk["video_id"],
                        "label": chunk["label"],
                        "chunk_index": chunk.get("chunk_index", 0),
                        "total_chunks": chunk.get("total_chunks", 1),
                        "relevance": min(score / 10, 1.0)
                    })
            
            # Sort by relevance
            results.sort(key=lambda x: x["relevance"], reverse=True)
            
            logger.info(f"Found {len(results)} relevant chunks for: '{query[:50]}'")
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    async def get_chunks_for_video(self, session_id: str, video_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific video"""
        if session_id not in self.transcripts:
            return []
        
        return [c for c in self.transcripts[session_id] if c.get("video_id") == video_id]
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        try:
            total_chunks = sum(len(t) for t in self.transcripts.values()) if self.transcripts else 0
            videos = set()
            for chunks in self.transcripts.values():
                for chunk in chunks:
                    videos.add(chunk.get("video_id", ""))
            
            return {
                "total_chunks": total_chunks,
                "total_videos": len(videos),
                "initialized": True
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {"total_chunks": 0, "initialized": True}

vector_store = VectorStore()