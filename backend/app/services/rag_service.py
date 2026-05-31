import asyncio
from typing import Dict, Any, List, AsyncGenerator
from datetime import datetime
from collections import defaultdict
from app.services.vector_store import vector_store
from app.services.llm_service import llm_service
from app.models.schemas import VideoMetadata, ChatMessage
from app.utils.helpers import setup_logging

logger = setup_logging()

class RAGService:
    """RAG service managing chat sessions, memory, and retrieval"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
    async def store_video_transcript(
        self, 
        session_id: str, 
        video_a: VideoMetadata, 
        video_b: VideoMetadata
    ):
        """Store video transcripts in vector DB"""
        try:
            # Initialize session
            self.sessions[session_id] = {
                "video_a": video_a,
                "video_b": video_b,
                "chat_history": [],
                "created_at": datetime.now()
            }
            
            # Chunk and store in vector DB
            total_chunks = await vector_store.chunk_and_store(
                session_id, video_a, video_b
            )
            
            logger.info(f"Session {session_id}: Stored {total_chunks} chunks")
            
        except Exception as e:
            logger.error(f"Failed to store transcripts: {str(e)}")
            raise
    
    async def chat_stream(
        self,
        session_id: str,
        question: str,
        video_a_id: str,
        video_b_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat response with citations"""
        
        try:
            # Get session data
            session = self.sessions.get(session_id)
            if not session:
                yield {"error": "Session not found"}
                return
            
            # Retrieve relevant chunks
            chunks = await vector_store.retrieve_relevant_chunks(
                query=question,
                session_id=session_id,
                video_a_id=video_a_id,
                video_b_id=video_b_id,
                top_k=6
            )
            
            # Add metadata to chunks if missing
            enriched_chunks = await self._enrich_chunks_with_metadata(chunks, session)
            
            # Generate streaming response
            full_response = ""
            citations = []
            
            async for chunk in llm_service.generate_response(
                query=question,
                context_chunks=enriched_chunks,
                chat_history=session["chat_history"]
            ):
                full_response += chunk
                yield {"content": chunk}
            
            # Generate citations based on chunks used
            citations = self._generate_citations(enriched_chunks)
            
            # Store in chat history
            session["chat_history"].append({
                "role": "user",
                "content": question,
                "timestamp": datetime.now().isoformat()
            })
            session["chat_history"].append({
                "role": "assistant",
                "content": full_response,
                "citations": citations,
                "timestamp": datetime.now().isoformat()
            })
            
            # Send final citations
            yield {"citations": citations}
            
        except Exception as e:
            logger.error(f"Chat stream error: {str(e)}")
            yield {"error": str(e)}
    
    async def _enrich_chunks_with_metadata(
        self, 
        chunks: List[Dict[str, Any]], 
        session: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Add video metadata to chunks for better context"""
        
        video_a = session["video_a"]
        video_b = session["video_b"]
        
        enriched = []
        for chunk in chunks:
            video_id = chunk["video_id"]
            video = video_a if video_a.video_id == video_id else video_b
            
            chunk["video_metadata"] = {
                "title": video.title,
                "creator": video.creator,
                "views": video.views,
                "likes": video.likes,
                "comments": video.comments,
                "hashtags": video.hashtags,
                "duration": video.duration,
                "platform": video.platform.value
            }
            
            # Add engagement rate if available
            if video.views and video.views > 0:
                engagement = ((video.likes or 0) + (video.comments or 0)) / video.views * 100
                chunk["video_metadata"]["engagement_rate"] = round(engagement, 2)
            
            enriched.append(chunk)
        
        return enriched
    
    def _generate_citations(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate citations from chunks"""
        citations = []
        seen_videos = set()
        
        for chunk in chunks:
            video_label = chunk.get("label", chunk.get("video_id", "Unknown"))
            if video_label not in seen_videos:
                citations.append({
                    "source": f"Video {video_label}",
                    "video_id": chunk["video_id"],
                    "chunk_preview": chunk["text"][:100] + "...",
                    "relevance": round(chunk.get("relevance_score", 1.0), 3)
                })
                seen_videos.add(video_label)
        
        return citations
    
    async def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a session"""
        session = self.sessions.get(session_id)
        if session:
            return session["chat_history"]
        return []
    
    async def answer_specific_queries(
        self,
        session_id: str,
        question_type: str
    ) -> str:
        """Answer specific query types efficiently"""
        
        session = self.sessions.get(session_id)
        if not session:
            return "Session not found"
        
        video_a = session["video_a"]
        video_b = session["video_b"]
        
        # Prepare video data
        video_a_data = {
            "title": video_a.title,
            "creator": video_a.creator,
            "views": video_a.views,
            "likes": video_a.likes,
            "comments": video_a.comments,
            "followers": video_a.creator_followers,
            "hashtags": video_a.hashtags,
            "transcript_preview": video_a.transcript[:300] if video_a.transcript else None
        }
        
        video_b_data = {
            "title": video_b.title,
            "creator": video_b.creator,
            "views": video_b.views,
            "likes": video_b.likes,
            "comments": video_b.comments,
            "followers": video_b.creator_followers,
            "hashtags": video_b.hashtags,
            "transcript_preview": video_b.transcript[:300] if video_b.transcript else None
        }
        
        # Map question types
        question_map = {
            "engagement": f"What is the engagement rate of Video A vs Video B? Engagement rate = (likes + comments) / views * 100",
            "hook": f"Compare the hooks (first 5 seconds) of Video A and Video B. Video A hook: {video_a.transcript[:100] if video_a.transcript else 'Not available'}. Video B hook: {video_b.transcript[:100] if video_b.transcript else 'Not available'}",
            "creator": f"Who is the creator of Video B and how many followers do they have? Creator: {video_b.creator}, Followers: {video_b.creator_followers}",
            "improvements": f"Suggest improvements for Video B based on what worked in Video A. Video A successful elements: {video_a.transcript[:200] if video_a.transcript else 'Not available'}. Video B areas for improvement: {video_b.transcript[:200] if video_b.transcript else 'Not available'}"
        }
        
        question = question_map.get(question_type, f"Compare Video A and Video B: {question_type}")
        
        answer = await llm_service.answer_specific_question(
            question, video_a_data, video_b_data
        )
        
        return answer
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up RAG service...")
        # Any cleanup needed

# Global instance
rag_service = RAGService()