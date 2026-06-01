from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Dict
import json
import asyncio
from langchain_core.messages import HumanMessage

from app.models.schemas import (
    ProcessVideosRequest, 
    ProcessVideosResponse,
    ChatRequest
)
from app.services.youtube_service import YouTubeService
from app.services.instagram_service import InstagramService
from app.services.rag_service import rag_service
from app.services.llm_service import llm_service
from app.services.vector_store import vector_store
from app.utils.helpers import generate_session_id, setup_logging
from app.api.youtube_routes import router as youtube_router
from app.api.instagram_routes import router as instagram_router

logger = setup_logging()
router = APIRouter()

# Include sub-routers
router.include_router(youtube_router)
router.include_router(instagram_router)

youtube_service = YouTubeService()
instagram_service = InstagramService()

@router.post("/process-videos")
async def process_videos(
    request: ProcessVideosRequest,
    background_tasks: BackgroundTasks
):
    """Process YouTube and Instagram videos in real-time - NO FALLBACKS"""
    try:
        session_id = generate_session_id()
        logger.info(f"Processing videos for session {session_id}")
        
        # Process YouTube video - real data only
        logger.info(f"Processing YouTube: {request.youtube_url}")
        video_a = await youtube_service.process_video(request.youtube_url)
        
        # Process Instagram video - real data only
        logger.info(f"Processing Instagram: {request.instagram_url}")
        video_b = await instagram_service.process_video(request.instagram_url)
        
        # Calculate engagement
        from app.models.schemas import EngagementMetrics
        
        def calc_engagement(views, likes, comments):
            if views and views > 0 and likes is not None and comments is not None:
                return ((likes + comments) / views) * 100
            return None
        
        engagement_a = EngagementMetrics(
            video_id=video_a.video_id,
            views=video_a.views,
            likes=video_a.likes,
            comments=video_a.comments,
            engagement_rate=calc_engagement(video_a.views, video_a.likes, video_a.comments)
        )
        
        engagement_b = EngagementMetrics(
            video_id=video_b.video_id,
            views=video_b.views,
            likes=video_b.likes,
            comments=video_b.comments,
            engagement_rate=calc_engagement(video_b.views, video_b.likes, video_b.comments)
        )
        
        # Store in vector DB
        background_tasks.add_task(
            rag_service.store_video_transcript,
            session_id,
            video_a,
            video_b
        )
        
        logger.info(f"Successfully processed both videos for session {session_id}")
        
        return {
            "session_id": session_id,
            "video_a": video_a.dict(),
            "video_b": video_b.dict(),
            "engagement_a": engagement_a.dict(),
            "engagement_b": engagement_b.dict()
        }
        
    except Exception as e:
        logger.error(f"Failed to process videos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def generate():
        try:
            session = rag_service.sessions.get(request.session_id)
            if not session:
                yield {"error": "Session not found"}
                return
            
            # Resolve pronouns using memory
            resolved_question = conversation_memory.resolve_references(
                request.session_id, request.message
            )
            
            video_a = session["video_a"]
            video_b = session["video_b"]
            
            # Search for chunks
            chunks = await vector_store.search(resolved_question, request.session_id, top_k=5)
            
            # Build context with chunk-level citations
            context = ""
            for i, chunk in enumerate(chunks):
                label = chunk.get("label", "Video")
                text = chunk["text"]
                context += f"\n[{label} - Chunk {i+1}]: {text}\n"
            
            if not context:
                if video_a.transcript:
                    context += f"\n[A - Full Transcript]: {video_a.transcript[:1000]}\n"
                if video_b.transcript:
                    context += f"\n[B - Full Transcript]: {video_b.transcript[:1000]}\n"
            
            question_lower = resolved_question.lower()
            
            # Route to specific handlers
            if "improvement" in question_lower or "suggest" in question_lower:
                prompt = f"""Based on Video A's success, suggest specific improvements for Video B.

Video A Content: {video_a.transcript[:800] if video_a.transcript else 'N/A'}
Video B Content: {video_b.transcript[:800] if video_b.transcript else 'N/A'}

Provide 3-5 actionable recommendations for Video B."""
            
            elif "hook" in question_lower or "opening" in question_lower:
                prompt = f"""Compare these hooks:
Video A: "{video_a.transcript[:200] if video_a.transcript else 'N/A'}"
Video B: "{video_b.transcript[:200] if video_b.transcript else 'N/A'}"
Analyze which is stronger and why."""
            
            else:
                prompt = f"""Answer based on transcripts:
{context}
Question: {resolved_question}
Be specific and cite chunks."""
            
            # Stream response
            async for chunk in llm_service.generate_response(prompt):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            
            # Add chunk-level citations
            citations = []
            for i, chunk in enumerate(chunks[:3]):
                citations.append({
                    "source": f"Video {chunk.get('label', 'Unknown')} - Chunk {i+1}",
                    "preview": chunk["text"][:100] + "..."
                })
            
            if citations:
                yield f"data: {json.dumps({'citations': citations})}\n\n"
            
            # Store in memory
            conversation_memory.add_message(request.session_id, "user", request.message)
            # Response will be added after streaming
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/session/{session_id}/history")
async def get_session_history(session_id: str):
    """Get chat history for a session"""
    history = await rag_service.get_chat_history(session_id)
    return {"session_id": session_id, "history": history}


@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {"message": "API is working!", "status": "ok"} 