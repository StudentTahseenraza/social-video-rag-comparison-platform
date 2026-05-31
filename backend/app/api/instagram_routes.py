from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.services.instagram_service import InstagramService
from app.utils.helpers import extract_video_id

router = APIRouter(prefix="/instagram", tags=["Instagram"])
instagram_service = InstagramService()

class InstagramProcessRequest(BaseModel):
    url: str

class InstagramMetadataResponse(BaseModel):
    video_id: str
    creator: str
    views: Optional[int]
    likes: Optional[int]
    comments: Optional[int]
    hashtags: list
    has_transcript: bool

@router.post("/process", response_model=Dict[str, Any])
async def process_instagram_reel(request: InstagramProcessRequest):
    """Process Instagram reel and return metadata with transcript"""
    try:
        metadata = await instagram_service.process_video(request.url)
        
        return {
            "success": True,
            "video_id": metadata.video_id,
            "creator": metadata.creator,
            "views": metadata.views,
            "likes": metadata.likes,
            "comments": metadata.comments,
            "hashtags": metadata.hashtags,
            "duration": metadata.duration,
            "has_transcript": metadata.transcript is not None,
            "transcript_preview": metadata.transcript[:200] if metadata.transcript else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validate/{video_id}")
async def validate_instagram_reel(video_id: str):
    """Validate if an Instagram reel exists and is accessible"""
    try:
        url = f"https://instagram.com/reel/{video_id}"
        
        # Try to extract basic info
        metadata = await instagram_service._extract_metadata_ytdlp(url)
        
        if metadata and metadata.get('uploader'):
            return {
                "valid": True,
                "video_id": video_id,
                "creator": metadata.get('uploader'),
                "has_data": True
            }
        else:
            return {
                "valid": False,
                "video_id": video_id,
                "error": "Could not access reel (may be private or deleted)"
            }
    except Exception as e:
        return {
            "valid": False,
            "video_id": video_id,
            "error": str(e)
        }