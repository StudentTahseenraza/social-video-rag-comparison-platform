from typing import Dict, Any, List, AsyncGenerator
from datetime import datetime
from app.services.vector_store import vector_store
from app.services.llm_service import llm_service
from app.models.schemas import VideoMetadata
from app.utils.helpers import setup_logging
from langchain_core.messages import HumanMessage

logger = setup_logging()

class RAGService:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    async def store_video_transcript(self, session_id: str, video_a: VideoMetadata, video_b: VideoMetadata):
        """Store video transcripts"""
        try:
            logger.info(f"STORING TRANSCRIPTS FOR SESSION {session_id}")
            
            self.sessions[session_id] = {
                "video_a": video_a,
                "video_b": video_b,
                "chat_history": [],
                "created_at": datetime.now()
            }
            
            if video_a.transcript:
                logger.info(f"Video A transcript: {len(video_a.transcript)} chars")
                result = vector_store.store_video_chunks_sync(
                    session_id=session_id,
                    video_id=video_a.video_id,
                    label="A",
                    transcript=video_a.transcript,
                    metadata={"creator": video_a.creator, "platform": video_a.platform.value}
                )
                logger.info(f"✅ Stored {result} chunks for Video A")
            
            if video_b.transcript:
                logger.info(f"Video B transcript: {len(video_b.transcript)} chars")
                result = vector_store.store_video_chunks_sync(
                    session_id=session_id,
                    video_id=video_b.video_id,
                    label="B",
                    transcript=video_b.transcript,
                    metadata={"creator": video_b.creator, "platform": video_b.platform.value}
                )
                logger.info(f"✅ Stored {result} chunks for Video B")
            
            stats = await vector_store.get_collection_stats()
            logger.info(f"📊 Vector DB stats: {stats}")
            
        except Exception as e:
            logger.error(f"Failed to store transcripts: {e}")
    
    async def chat_stream(self, session_id: str, question: str, video_a_id: str, video_b_id: str):
        """Stream chat response using RAG with actual transcript retrieval"""
        
        session = self.sessions.get(session_id)
        if not session:
            yield {"error": "Session not found"}
            return
        
        video_a = session["video_a"]
        video_b = session["video_b"]
        
        # Search for relevant chunks using the vector store
        chunks = await vector_store.search(question, session_id, top_k=3)
        
        # Build context from retrieved chunks
        context = ""
        for chunk in chunks:
            label = chunk.get("label", "Video")
            text = chunk["text"]
            context += f"\n[{label}]: {text}\n"
            logger.info(f"Retrieved chunk from {label}: {text[:100]}...")
        
        # If no chunks found, use transcripts directly
        if not context:
            logger.warning("No chunks found, using direct transcripts")
            if video_a.transcript:
                context += f"\n[A]: {video_a.transcript[:1000]}\n"
            if video_b.transcript:
                context += f"\n[B]: {video_b.transcript[:1000]}\n"
        
        # Build prompt that specifically asks for transcript content
        prompt = f"""You are a video analysis expert. Use the following transcript content to answer the question.

VIDEO TRANSCRIPTS:
{context}

QUESTION: {question}

INSTRUCTIONS:
1. Answer based ONLY on the transcript content above
2. If the question asks for specific lyrics or spoken content, quote directly from the transcript
3. Cite which video (A or B) the information comes from
4. If the transcript doesn't contain the answer, say "The transcript does not contain that information"

ANSWER:"""
        
        try:
            full_response = ""
            async for chunk in llm_service.llm.astream([HumanMessage(content=prompt)]):
                if chunk.content:
                    full_response += chunk.content
                    yield {"content": chunk.content}
            
            # Add citations with actual transcript previews
            citations = []
            if video_a.transcript:
                citations.append({
                    "source": f"Video A ({video_a.platform.value})", 
                    "preview": video_a.transcript[:150] + "..."
                })
            if video_b.transcript:
                citations.append({
                    "source": f"Video B ({video_b.platform.value})", 
                    "preview": video_b.transcript[:150] + "..."
                })
            
            yield {"citations": citations}
            
        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            yield {"error": str(e)}
    
    async def get_chat_history(self, session_id: str) -> List[Dict]:
        session = self.sessions.get(session_id, {})
        return session.get("chat_history", [])
    
    async def cleanup(self):
        pass

rag_service = RAGService()