from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
from app.services.youtube_service import YouTubeService
from app.utils.helpers import extract_video_id

router = APIRouter(prefix="/youtube", tags=["YouTube"])
youtube_service = YouTubeService()

@router.get("/metadata/{video_id}")
async def get_youtube_metadata(video_id: str):
    """Get metadata for a YouTube video by ID"""
    try:
        url = f"https://youtube.com/watch?v={video_id}"
        metadata = await youtube_service._extract_metadata(url)
        
        if not metadata:
            raise HTTPException(status_code=404, detail="Video not found")
        
        return {
            "video_id": video_id,
            **metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transcript/{video_id}")
async def get_youtube_transcript(video_id: str):
    """Get transcript for a YouTube video"""
    try:
        transcript = await youtube_service._get_transcript(video_id)
        
        if not transcript:
            raise HTTPException(status_code=404, detail="No transcript available")
        
        return {
            "video_id": video_id,
            "transcript": transcript,
            "length": len(transcript.split())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate")
async def validate_youtube_url(url: str):
    """Validate if a URL is a valid YouTube video"""
    try:
        video_id = extract_video_id(url, 'youtube')
        metadata = await youtube_service._extract_metadata(url)
        
        if not metadata:
            return {"valid": False, "error": "Could not fetch video data"}
        
        return {
            "valid": True,
            "video_id": video_id,
            "title": metadata.get('title'),
            "duration": metadata.get('duration'),
            "has_transcript": await youtube_service._get_transcript(video_id) is not None
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}