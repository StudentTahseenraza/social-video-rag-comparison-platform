import asyncio
from typing import Dict, Any, List, AsyncGenerator
from datetime import datetime
from collections import defaultdict
from app.services.vector_store import vector_store
from app.services.llm_service import llm_service
from app.services.memory_service import conversation_memory
from app.agents.video_analyzer_agent import video_analyzer_agent
from app.models.schemas import VideoMetadata, ChatMessage
from app.utils.helpers import setup_logging

logger = setup_logging()

class RAGService:
    """Enhanced RAG service with agent support and advanced memory"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.agent = None
        
    async def initialize_agent(self):
        """Initialize the LangGraph agent"""
        if not self.agent:
            self.agent = video_analyzer_agent
            self.agent.build_workflow()
            logger.info("LangGraph agent initialized")
    
    async def store_video_transcript(
        self, 
        session_id: str, 
        video_a: VideoMetadata, 
        video_b: VideoMetadata
    ):
        """Store video transcripts in vector DB with enhanced metadata"""
        try:
            # Initialize session
            self.sessions[session_id] = {
                "video_a": video_a,
                "video_b": video_b,
                "chat_history": [],
                "created_at": datetime.now(),
                "video_metrics": {
                    "a_engagement": self._calculate_engagement(video_a),
                    "b_engagement": self._calculate_engagement(video_b),
                    "comparison_ready": True
                }
            }
            
            # Store in memory service
            conversation_memory.update_context(session_id, "video_a_creator", video_a.creator)
            conversation_memory.update_context(session_id, "video_b_creator", video_b.creator)
            conversation_memory.update_context(session_id, "video_a_views", video_a.views)
            conversation_memory.update_context(session_id, "video_b_views", video_b.views)
            
            # Chunk and store in vector DB
            total_chunks = await vector_store.chunk_and_store(
                session_id, video_a, video_b
            )
            
            # Store engagement metrics in context
            if video_a.transcript:
                conversation_memory.update_context(
                    session_id, 
                    "video_a_hook", 
                    video_a.transcript[:100]
                )
            if video_b.transcript:
                conversation_memory.update_context(
                    session_id, 
                    "video_b_hook", 
                    video_b.transcript[:100]
                )
            
            logger.info(f"Session {session_id}: Stored {total_chunks} chunks with enhanced context")
            
            # Initialize agent
            await self.initialize_agent()
            
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
        """Stream chat response with agent-based reasoning"""
        
        try:
            # Get session data
            session = self.sessions.get(session_id)
            if not session:
                yield {"error": "Session not found"}
                return
            
            # Get conversation context
            context = conversation_memory.get_context(session_id, last_n=5)
            
            # Check if this is a follow-up question (has pronouns referring to previous)
            is_followup = self._is_followup_question(question, context)
            
            if is_followup:
                # Resolve pronouns using context
                resolved_question = await self._resolve_references(question, session_id)
                logger.info(f"Resolved follow-up: '{question}' -> '{resolved_question}'")
                question = resolved_question
            
            # Use agent for complex questions
            if self._is_complex_question(question):
                logger.info(f"Using LangGraph agent for complex question: {question}")
                
                async for result in self.agent.process_question(
                    session_id=session_id,
                    question=question,
                    video_a_id=video_a_id,
                    video_b_id=video_b_id
                ):
                    if result.get("type") == "complete":
                        # Store in memory
                        conversation_memory.add_message(
                            session_id, "user", question, {"important": True}
                        )
                        conversation_memory.add_message(
                            session_id, "assistant", result["content"], 
                            {"citations": result.get("citations", [])}
                        )
                        
                        yield {
                            "content": result["content"],
                            "citations": result.get("citations", []),
                            "analysis_steps": result.get("analysis_steps", [])
                        }
                    elif result.get("type") == "analysis":
                        yield {"thinking": result["content"]}
                    elif result.get("type") == "error":
                        yield {"error": result["error"]}
            else:
                # Use simple RAG for straightforward questions
                async for chunk in self._simple_rag_response(
                    session_id, question, video_a_id, video_b_id, context
                ):
                    yield chunk
            
        except Exception as e:
            logger.error(f"Chat stream error: {str(e)}")
            yield {"error": str(e)}
    
    async def _simple_rag_response(
        self,
        session_id: str,
        question: str,
        video_a_id: str,
        video_b_id: str,
        context: List[Dict[str, Any]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Simple RAG response for straightforward questions"""
        
        session = self.sessions[session_id]
        
        # Retrieve relevant chunks
        chunks = await vector_store.retrieve_relevant_chunks(
            query=question,
            session_id=session_id,
            video_a_id=video_a_id,
            video_b_id=video_b_id,
            top_k=5
        )
        
        # Enrich chunks with metadata
        enriched_chunks = await self._enrich_chunks_with_metadata(chunks, session)
        
        # Build prompt with context
        prompt = self._build_rag_prompt(question, enriched_chunks, context)
        
        # Stream response
        full_response = ""
        async for chunk in llm_service.llm.astream([HumanMessage(content=prompt)]):
            if chunk.content:
                full_response += chunk.content
                yield {"content": chunk.content}
        
        # Generate citations
        citations = self._generate_citations(enriched_chunks)
        
        # Store in memory
        conversation_memory.add_message(session_id, "user", question)
        conversation_memory.add_message(session_id, "assistant", full_response, {"citations": citations})
        
        yield {"citations": citations}
    
    def _is_complex_question(self, question: str) -> bool:
        """Determine if question requires agent-based reasoning"""
        
        complex_patterns = [
            "why did", "compare", "analyze", "explain", 
            "what worked", "suggest improvements", "difference between",
            "how could", "what if", "what makes"
        ]
        
        question_lower = question.lower()
        return any(pattern in question_lower for pattern in complex_patterns)
    
    def _is_followup_question(self, question: str, context: List[Dict[str, Any]]) -> bool:
        """Check if question references previous conversation"""
        
        followup_indicators = ["it", "they", "that", "this", "those", "these", "its", "their"]
        question_lower = question.lower()
        
        # Check for pronouns
        has_pronoun = any(indicator in question_lower.split() for indicator in followup_indicators)
        
        # Check if question is short and context exists
        is_short = len(question.split()) < 8
        has_context = len(context) > 0
        
        return has_pronoun and is_short and has_context
    
    async def _resolve_references(self, question: str, session_id: str) -> str:
        """Resolve pronouns and references using conversation context"""
        
        context = conversation_memory.get_context(session_id, last_n=3)
        
        if not context:
            return question
        
        # Get last assistant response
        last_response = None
        for msg in reversed(context):
            if msg["role"] == "assistant":
                last_response = msg["content"]
                break
        
        if not last_response:
            return question
        
        # Extract key entities from last response
        entities = []
        if "video a" in last_response.lower():
            entities.append("Video A")
        if "video b" in last_response.lower():
            entities.append("Video B")
        
        # Replace pronouns with entities
        resolved = question
        if "it" in resolved.lower() and entities:
            resolved = resolved.replace("it", entities[0])
            resolved = resolved.replace("It", entities[0])
        if "they" in resolved.lower() and entities:
            resolved = resolved.replace("they", f"{entities[0]} and {entities[1]}" if len(entities) > 1 else entities[0])
        
        return resolved
    
    async def _enrich_chunks_with_metadata(
        self, 
        chunks: List[Dict[str, Any]], 
        session: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Add video metadata to chunks"""
        
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
                "engagement_rate": self._calculate_engagement(video),
                "hashtags": video.hashtags[:5]
            }
            enriched.append(chunk)
        
        return enriched
    
    def _build_rag_prompt(
        self, 
        question: str, 
        chunks: List[Dict[str, Any]], 
        context: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for RAG response"""
        
        context_str = ""
        for chunk in chunks:
            label = chunk.get('label', chunk.get('video_id', 'Video'))
            context_str += f"\n[{label}]: {chunk['text']}\n"
        
        history_str = ""
        for msg in context[-3:]:
            history_str += f"{msg['role']}: {msg['content']}\n"
        
        return f"""You are a video analysis expert. Use the following context to answer the question.

PREVIOUS CONVERSATION:
{history_str}

RETRIEVED CONTEXT:
{context_str}

QUESTION: {question}

INSTRUCTIONS:
1. Answer based ONLY on the provided context
2. Cite which video (A or B) each piece of information comes from
3. If information is missing, say "Not available in the video data"
4. Be specific and provide actionable insights
5. Keep response concise but informative

ANSWER:"""
    
    def _generate_citations(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate citations from chunks"""
        citations = []
        seen = set()
        
        for chunk in chunks:
            label = chunk.get('label', 'Unknown')
            if label not in seen:
                citations.append({
                    "source": f"Video {label}",
                    "video_id": chunk["video_id"],
                    "preview": chunk["text"][:100] + "...",
                    "relevance": round(chunk.get("relevance_score", 1.0), 3)
                })
                seen.add(label)
        
        return citations
    
    def _calculate_engagement(self, video: VideoMetadata) -> float:
        """Calculate engagement rate"""
        if video.views and video.views > 0:
            total = (video.likes or 0) + (video.comments or 0)
            return round((total / video.views) * 100, 2)
        return 0.0
    
    async def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chat history from memory service"""
        return conversation_memory.get_context(session_id)
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up RAG service...")
        conversation_memory.cleanup_old_sessions()

# Global instance
rag_service = RAGService()