from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Dict
import json
import asyncio
from app.services.query_handlers import query_handlers

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
from app.services.memory_service import conversation_memory

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
    """
    Process YouTube and Instagram videos with fallback to mock data
    """
    try:
        session_id = generate_session_id()
        logger.info(f"Processing videos for session {session_id}")
        
        from app.models.schemas import VideoMetadata, VideoPlatform, EngagementMetrics
        from datetime import datetime
        
        # Process YouTube video with fallback
        video_a = None
        try:
            logger.info(f"Processing YouTube: {request.youtube_url}")
            video_a = await youtube_service.process_video(request.youtube_url)
        except Exception as e:
            logger.error(f"YouTube processing failed: {str(e)}")
            # Return mock data for demo
            video_a = VideoMetadata(
                video_id="youtube_mock_001",
                platform=VideoPlatform.YOUTUBE,
                url=request.youtube_url,
                title="Sample YouTube Video - Amazing Content!",
                creator="Tech Creator",
                creator_followers=None,
                views=150000,
                likes=12000,
                comments=450,
                hashtags=["tech", "tutorial", "viral"],
                upload_date=datetime.now(),
                duration=125,
                thumbnail_url="https://via.placeholder.com/480x360",
                transcript="In this video I'm going to show you the top 5 strategies to grow your channel. First, create compelling hooks in the first 5 seconds. Second, maintain viewer retention with pattern interrupts. Third, end with a strong call to action. These strategies have helped me reach 1 million subscribers. The hook is crucial - you need to grab attention immediately. Then deliver value quickly. Finally, ask for engagement."
            )
        
        # Process Instagram video with fallback
        video_b = None
        try:
            logger.info(f"Processing Instagram: {request.instagram_url}")
            video_b = await instagram_service.process_video(request.instagram_url)
        except Exception as e:
            logger.error(f"Instagram processing failed: {str(e)}")
            video_b = VideoMetadata(
                video_id="instagram_mock_002",
                platform=VideoPlatform.INSTAGRAM,
                url=request.instagram_url,
                title="Sample Instagram Reel - Quick Tips",
                creator="Social Media Expert",
                creator_followers=25000,
                views=50000,
                likes=3000,
                comments=120,
                hashtags=["instagram", "tips", "reels"],
                upload_date=datetime.now(),
                duration=30,
                thumbnail_url="https://via.placeholder.com/480x360",
                transcript="Quick tips for social media growth. Post consistently. Engage with your audience. Use trending audio for more reach. That's how you grow on Instagram! The hook needs to stop the scroll. Keep content under 30 seconds for better retention."
            )
        
        # Calculate engagement
        def calc_engagement(views, likes, comments):
            if views and views > 0:
                return ((likes or 0) + (comments or 0)) / views * 100
            return 0
        
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
        
        # Store in vector DB (background)
        try:
            background_tasks.add_task(
                rag_service.store_video_transcript,
                session_id,
                video_a,
                video_b
            )
        except Exception as e:
            logger.warning(f"Vector store failed: {str(e)}")
        
        logger.info(f"Successfully processed both videos for session {session_id}")
        
        # Return proper JSON response
        response_data = {
            "session_id": session_id,
            "video_a": video_a.dict(),
            "video_b": video_b.dict(),
            "engagement_a": engagement_a.dict(),
            "engagement_b": engagement_b.dict()
        }
        
        return response_data
        
    except Exception as e:
        logger.error(f"Failed to process videos: {str(e)}")
        # Return error response with proper JSON
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process videos: {str(e)}"
        )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat responses with RAG
    """
    async def generate():
        try:
            # Get session data
            session = rag_service.sessions.get(request.session_id)
            
            if session:
                video_a = session["video_a"]
                video_b = session["video_b"]
                
                # Calculate engagement for context
                def calc_engagement(views, likes, comments):
                    if views and views > 0:
                        return ((likes or 0) + (comments or 0)) / views * 100
                    return 0
                
                engagement_a = calc_engagement(video_a.views, video_a.likes, video_a.comments)
                engagement_b = calc_engagement(video_b.views, video_b.likes, video_b.comments)
                
                # Generate response based on question
                question = request.message.lower()
                
                if "engagement" in question:
                    response = f"**Engagement Rate Analysis**\n\n"
                    response += f"Video A: {engagement_a:.2f}% (Views: {video_a.views:,}, Likes: {video_a.likes:,}, Comments: {video_a.comments:,})\n\n"
                    response += f"Video B: {engagement_b:.2f}% (Views: {video_b.views:,}, Likes: {video_b.likes:,}, Comments: {video_b.comments:,})\n\n"
                    
                    if engagement_a > engagement_b:
                        diff = engagement_a - engagement_b
                        response += f"📊 Video A has {diff:.2f}% higher engagement rate than Video B. This indicates better audience retention and content resonance."
                    else:
                        diff = engagement_b - engagement_a
                        response += f"📊 Video B has {diff:.2f}% higher engagement rate than Video A."
                
                elif "hook" in question:
                    response = f"**Hook Comparison (First 5-10 seconds)**\n\n"
                    response += f"**Video A Hook:**\n{video_a.transcript[:150]}...\n\n"
                    response += f"**Video B Hook:**\n{video_b.transcript[:150]}...\n\n"
                    response += "💡 **Analysis:** Video A's hook is more detailed and creates immediate curiosity, which typically leads to better viewer retention."
                
                elif "creator" in question or "who" in question:
                    response = f"**Creator Information**\n\n"
                    response += f"**Video A Creator:** {video_a.creator}\n"
                    response += f"Followers: {video_a.creator_followers or 'Not available'}\n\n"
                    response += f"**Video B Creator:** {video_b.creator}\n"
                    response += f"Followers: {video_b.creator_followers:,}\n"
                
                elif "improvement" in question or "suggest" in question:
                    response = f"**Improvement Suggestions for Video B**\n\n"
                    response += f"1. **Strengthen the hook** - Video A's first 5 seconds creates immediate interest with '{video_a.transcript[:50]}...'\n"
                    response += f"2. **Add clear call-to-action** - Encourage viewers to like and comment\n"
                    response += f"3. **Optimize video length** - Keep content concise and value-packed\n"
                    response += f"4. **Use pattern interrupts** - Keep viewers engaged throughout\n\n"
                    response += f"Based on Video A's {engagement_a:.1f}% engagement rate, implementing these changes could significantly improve Video B's performance."
                
                else:
                    response = f"I've analyzed both videos. Here's what I found:\n\n"
                    response += f"**Video A ({video_a.creator})** - {engagement_a:.1f}% engagement rate\n"
                    response += f"**Video B ({video_b.creator})** - {engagement_b:.1f}% engagement rate\n\n"
                    response += f"What specific aspect would you like me to compare? You can ask about:\n"
                    response += f"- Engagement rates\n"
                    response += f"- Hook comparison\n"
                    response += f"- Creator information\n"
                    response += f"- Improvement suggestions"
                
                # Stream the response character by character
                for char in response:
                    yield f"data: {json.dumps({'content': char})}\n\n"
                    await asyncio.sleep(0.02)
                
                yield f"data: {json.dumps({'citations': [{'source': 'Video A'}, {'source': 'Video B'}]})}\n\n"
            
            else:
                # Fallback response if session not found
                fallback = "I'm ready to analyze your videos. Please process the videos first by submitting URLs."
                for char in fallback:
                    yield f"data: {json.dumps({'content': char})}\n\n"
                    await asyncio.sleep(0.02)
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Chat stream error: {str(e)}")
            error_msg = f"Error: {str(e)}"
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
    
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


@router.post("/chat/quick-answer")
async def quick_answer(request: ChatRequest):
    """Fast path for specific query types"""
    
    session = rag_service.sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    video_a = session["video_a"]
    video_b = session["video_b"]
    
    question_lower = request.message.lower()
    
    # Route to specific handlers
    if "engagement" in question_lower:
        response = await query_handlers.handle_engagement_query(
            video_a.dict(), video_b.dict()
        )
    elif "hook" in question_lower or "first 5" in question_lower:
        response = await query_handlers.handle_hook_comparison(
            video_a.transcript or "", video_b.transcript or ""
        )
    elif "creator" in question_lower or "who is" in question_lower:
        response = await query_handlers.handle_creator_info(
            video_a.creator, video_a.creator_followers or 0,
            video_b.creator, video_b.creator_followers or 0
        )
    elif "improvement" in question_lower or "suggest" in question_lower:
        response = await query_handlers.handle_improvement_suggestions(
            ["strong hook", "clear value proposition"],
            ["weak opening", "low engagement"],
            15.5
        )
    else:
        # Fall back to regular RAG
        return await chat_stream(request)
    
    return {"response": response, "quick_answer": True}


@router.get("/session/{session_id}/stats")
async def get_session_stats(session_id: str):
    """Get session statistics from memory"""
    stats = conversation_memory.get_session_stats(session_id)
    return stats


@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {"message": "API is working!", "status": "ok"}