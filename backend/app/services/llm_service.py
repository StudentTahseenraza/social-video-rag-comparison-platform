import asyncio
from typing import AsyncGenerator, List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.config import settings
from app.utils.helpers import setup_logging

logger = setup_logging()

class LLMService:
    """LLM service with Gemini (free tier) and streaming support"""
    
    def __init__(self):
        self.llm = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize Gemini LLM"""
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=settings.llm_model,
                google_api_key=settings.google_api_key,
                temperature=settings.temperature,
                streaming=True,
                convert_system_message_to_human=True
            )
            self.is_initialized = True
            logger.info(f"LLM service initialized with {settings.llm_model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}")
            self.is_initialized = False
            raise
    
    async def generate_response(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        chat_history: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response with RAG context"""
        
        if not self.is_initialized:
            await self.initialize()
        
        # Build context from chunks
        context = self._build_context(context_chunks)
        
        # Build system prompt
        system_prompt = self._build_system_prompt(context)
        
        # Build messages with history
        messages = [SystemMessage(content=system_prompt)]
        
        # Add chat history (last 5 messages for context)
        for msg in chat_history[-10:]:
            if msg['role'] == 'user':
                messages.append(HumanMessage(content=msg['content']))
            else:
                messages.append(AIMessage(content=msg['content']))
        
        # Add current query
        messages.append(HumanMessage(content=query))
        
        # Stream response
        try:
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"LLM streaming error: {str(e)}")
            yield f"Error generating response: {str(e)}"
    
    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved chunks"""
        if not chunks:
            return "No relevant video context available."
        
        context_parts = []
        for chunk in chunks:
            video_label = chunk.get('label', chunk.get('video_id', 'Unknown'))
            text = chunk['text']
            context_parts.append(f"[Video {video_label}]: {text}")
        
        return "\n\n".join(context_parts)
    
    def _build_system_prompt(self, context: str) -> str:
        """Build system prompt with instructions"""
        return f"""You are a video analysis expert comparing two videos (Video A and Video B).

CONTEXT FROM VIDEOS:
{context}

INSTRUCTIONS:
1. Answer based ONLY on the provided context
2. If information is missing, say "Not available in the video data"
3. Cite which video (A or B) each piece of information comes from
4. Compare metrics when relevant
5. Be specific and actionable for improvement suggestions
6. Keep responses concise but informative

AVAILABLE METRICS:
- Engagement rate = (likes + comments) / views × 100
- Creator name and follower count (if available)
- Video hooks (first 5-10 seconds of transcript)
- View counts, likes, comments

Remember: Always cite your sources from the context!"""
    
    async def answer_specific_question(
        self,
        question: str,
        video_a_data: Dict[str, Any],
        video_b_data: Dict[str, Any]
    ) -> str:
        """Answer specific predefined questions efficiently"""
        
        prompt = f"""
Question: {question}

Video A Data:
{self._format_video_data(video_a_data)}

Video B Data:
{self._format_video_data(video_b_data)}

Provide a clear, comparative answer based on the data above.
"""
        messages = [HumanMessage(content=prompt)]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    def _format_video_data(self, data: Dict[str, Any]) -> str:
        """Format video data for prompt"""
        lines = []
        for key, value in data.items():
            if value is not None:
                lines.append(f"  {key}: {value}")
        return "\n".join(lines) if lines else "  No data available"

# Global instance
llm_service = LLMService()