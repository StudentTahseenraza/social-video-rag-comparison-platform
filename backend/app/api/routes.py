from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Dict
import json
import asyncio
from datetime import datetime
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
from app.services.memory_service import conversation_memory
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
    """Process YouTube and Instagram videos in real-time"""
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
    """Stream chat responses using RAG with metadata and memory"""
    async def generate():
        session_id = request.session_id
        
        try:
            session = rag_service.sessions.get(session_id)
            
            if not session:
                error_msg = "Session not found. Please process videos first."
                for char in error_msg:
                    yield f"data: {json.dumps({'content': char})}\n\n"
                    await asyncio.sleep(0.03)
                yield "data: [DONE]\n\n"
                return
            
            video_a = session["video_a"]
            video_b = session["video_b"]
            
            # Helper functions
            def fmt_num(value):
                if value is None:
                    return "N/A"
                try:
                    if isinstance(value, (int, float)):
                        if value >= 1000000:
                            return f"{value/1000000:.1f}M"
                        if value >= 1000:
                            return f"{value/1000:.1f}K"
                        return f"{value:,}"
                    return str(value)
                except:
                    return "N/A"
            
            def fmt_percent(value):
                if value is None:
                    return "N/A"
                try:
                    return f"{value:.2f}%"
                except:
                    return "N/A"
            
            def calc_eng(v):
                if v.views and v.views > 0 and v.likes is not None and v.comments is not None:
                    return ((v.likes + v.comments) / v.views) * 100
                return None
            
            eng_a = calc_eng(video_a)
            eng_b = calc_eng(video_b)
            
            # Build metadata context
            metadata_context = f"""
VIDEO A METADATA:
- Title: {video_a.title}
- Creator: {video_a.creator}
- Platform: {video_a.platform.value.upper()}
- Views: {fmt_num(video_a.views)}
- Likes: {fmt_num(video_a.likes)}
- Comments: {fmt_num(video_a.comments)}
- Duration: {video_a.duration if video_a.duration else 'N/A'} seconds
- Hashtags: {', '.join(video_a.hashtags[:5]) if video_a.hashtags else 'None'}
- Engagement Rate: {fmt_percent(eng_a)}

VIDEO B METADATA:
- Title: {video_b.title}
- Creator: {video_b.creator}
- Platform: {video_b.platform.value.upper()}
- Views: {fmt_num(video_b.views)}
- Likes: {fmt_num(video_b.likes)}
- Comments: {fmt_num(video_b.comments)}
- Duration: {video_b.duration if video_b.duration else 'N/A'} seconds
- Hashtags: {', '.join(video_b.hashtags[:5]) if video_b.hashtags else 'None'}
- Engagement Rate: {fmt_percent(eng_b)}
"""
            
            # Search for transcript chunks
            chunks = await vector_store.search(request.message, session_id, top_k=5)
            
            # Build transcript context
            transcript_context = ""
            for i, chunk in enumerate(chunks):
                label = chunk.get("label", "Video")
                text = chunk["text"]
                original_chunk = chunk.get("chunk_index", i) + 1
                transcript_context += f"\n[{label} - Chunk {original_chunk}]: {text}\n"
            
            # Build conversation history
            history_context = ""
            if session.get("chat_history"):
                last_messages = session["chat_history"][-6:]
                for msg in last_messages:
                    history_context += f"{msg['role']}: {msg['content']}\n"
            
            # ========== COMPREHENSIVE FOLLOW-UP HANDLING ==========
            follow_up_indicators = ["why", "how", "that", "this", "explain", "elaborate", "more detail", "tell me more", "what about", "and"]
            is_follow_up = any(indicator in request.message.lower() for indicator in follow_up_indicators)
            
            resolved_question = request.message
            
            if is_follow_up and session.get("chat_history"):
                # Get the last assistant response
                last_assistant = None
                last_user = None
                
                for msg in reversed(session["chat_history"]):
                    if msg["role"] == "assistant" and last_assistant is None:
                        last_assistant = msg["content"]
                    elif msg["role"] == "user" and last_user is None:
                        last_user = msg["content"]
                    if last_assistant and last_user:
                        break
                
                if last_assistant:
                    if "that" in request.message.lower() or "this" in request.message.lower():
                        resolved_question = f"""
Previous context:
User asked: "{last_user}"
Assistant answered: "{last_assistant}"

Now user asks: "{request.message}"

Based on the previous answer, please explain your reasoning and provide more details."""
                    
                    elif request.message.lower().startswith("why") or request.message.lower().startswith("how"):
                        resolved_question = f"""
Previous context:
User asked: "{last_user}"
Assistant answered: "{last_assistant}"

Now user asks: "{request.message}"

Please explain the reasoning behind your previous answer in more detail."""
            
            # Simple pronoun resolution for non-follow-ups
            elif session.get("chat_history"):
                last_messages_text = " ".join([m["content"] for m in session["chat_history"][-3:]])
                
                if "they" in resolved_question.lower() or "them" in resolved_question.lower():
                    if "Video B" in last_messages_text or "BBC News" in last_messages_text:
                        resolved_question = resolved_question.replace("they", "Video B (BBC News)")
                        resolved_question = resolved_question.replace("them", "Video B")
                    elif "Video A" in last_messages_text or "Rick Astley" in last_messages_text:
                        resolved_question = resolved_question.replace("they", "Video A (Rick Astley)")
                        resolved_question = resolved_question.replace("them", "Video A")
                
                if "it" in resolved_question.lower():
                    if "Video A" in last_messages_text or "Rick Astley" in last_messages_text:
                        resolved_question = resolved_question.replace("it", "Video A")
                    elif "Video B" in last_messages_text or "BBC News" in last_messages_text:
                        resolved_question = resolved_question.replace("it", "Video B")
            
            # Build final prompt
            prompt = f"""You are a video analysis expert. Answer questions based on the provided information.

CONVERSATION HISTORY (for context/memory):
{history_context}

VIDEO METADATA (for creator, likes, views, comments, engagement):
{metadata_context}

VIDEO TRANSCRIPTS (for content analysis):
{transcript_context}

QUESTION: {resolved_question}

INSTRUCTIONS:
1. For questions about CREATOR, LIKES, VIEWS, COMMENTS, ENGAGEMENT - use METADATA
2. For questions about CONTENT, LYRICS, HOOKS, STRATEGY - use TRANSCRIPTS
3. For follow-up questions (why, how, explain, elaborate, tell me more, that, this):
   - Reference the previous assistant answer
   - Explain the reasoning behind your previous statements
   - Provide additional evidence from the transcripts or metadata
4. For follow-up questions asking about "that" or "this" - refer to the most recent topic discussed
5. Be specific and cite which video (A or B)
6. If information is not available, say "Not available in the data"

ANSWER:"""
            
            # Stream response
            response_text = ""
            async for chunk in llm_service.generate_response(prompt):
                if chunk:
                    response_text += chunk
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
                    await asyncio.sleep(0.015)
            
            # Add citations with correct chunk numbers
            citations = []
            for i, chunk in enumerate(chunks[:3]):
                original_chunk_num = chunk.get("chunk_index", i) + 1
                citations.append({
                    "source": f"Video {chunk.get('label', 'Unknown')} - Chunk {original_chunk_num}",
                    "preview": chunk["text"][:100] + "..."
                })
            
            if citations:
                yield f"data: {json.dumps({'citations': citations})}\n\n"
            
            # Store in memory
            if "chat_history" not in session:
                session["chat_history"] = []
            
            session["chat_history"].append({
                "role": "user",
                "content": request.message,
                "timestamp": datetime.now().isoformat()
            })
            session["chat_history"].append({
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.now().isoformat()
            })
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Chat stream error: {str(e)}")
            import traceback
            traceback.print_exc()
            error_msg = f"Error: {str(e)}"
            for char in error_msg:
                yield f"data: {json.dumps({'error': char})}\n\n"
                await asyncio.sleep(0.03)
            yield "data: [DONE]\n\n"
    
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


@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {"message": "API is working!", "status": "ok"}