from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Dict
import json
import asyncio

from app.models.schemas import (
    ProcessVideosRequest, 
    ProcessVideosResponse,
    ChatRequest,
    ChatMessage
)
from app.services.youtube_service import YouTubeService
from app.services.instagram_service import InstagramService
from app.services.rag_service import rag_service
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

@router.post("/process-videos", response_model=ProcessVideosResponse)
async def process_videos(
    request: ProcessVideosRequest,
    background_tasks: BackgroundTasks
):
    """
    Process YouTube and Instagram videos:
    - Extract metadata
    - Get/Generate transcripts
    - Calculate engagement rates
    - Create embeddings and store in vector DB
    """
    try:
        session_id = generate_session_id()
        logger.info(f"Processing videos for session {session_id}")
        
        # Process YouTube video
        logger.info(f"Processing YouTube: {request.youtube_url}")
        video_a = await youtube_service.process_video(request.youtube_url)
        
        # Process Instagram video
        logger.info(f"Processing Instagram: {request.instagram_url}")
        video_b = await instagram_service.process_video(request.instagram_url)
        
        # Calculate engagement
        from app.models.schemas import EngagementMetrics
        
        engagement_a = EngagementMetrics(
            video_id=video_a.video_id,
            views=video_a.views,
            likes=video_a.likes,
            comments=video_a.comments
        ).calculate_rate()
        
        engagement_b = EngagementMetrics(
            video_id=video_b.video_id,
            views=video_b.views,
            likes=video_b.likes,
            comments=video_b.comments
        ).calculate_rate()
        
        # Add messages for missing data
        if video_b.views is None:
            engagement_b.message = "Limited Instagram data available"
        
        # Store in vector DB (background)
        background_tasks.add_task(
            rag_service.store_video_transcript,
            session_id,
            video_a,
            video_b
        )
        
        logger.info(f"Successfully processed both videos for session {session_id}")
        
        return ProcessVideosResponse(
            session_id=session_id,
            video_a=video_a,
            video_b=video_b,
            engagement_a=engagement_a,
            engagement_b=engagement_b
        )
        
    except Exception as e:
        logger.error(f"Failed to process videos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat responses with RAG
    """
    async def generate():
        try:
            async for chunk in rag_service.chat_stream(
                session_id=request.session_id,
                question=request.message,
                video_a_id=request.video_a_id,
                video_b_id=request.video_b_id
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Chat stream error: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/session/{session_id}/history")
async def get_session_history(session_id: str):
    """Get chat history for a session"""
    history = await rag_service.get_chat_history(session_id)
    return {"session_id": session_id, "history": history}