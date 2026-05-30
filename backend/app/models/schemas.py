from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class VideoPlatform(str, Enum):
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"

class VideoMetadata(BaseModel):
    video_id: str
    platform: VideoPlatform
    url: str
    title: str
    creator: str
    creator_followers: Optional[int] = None
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    hashtags: List[str] = []
    upload_date: Optional[datetime] = None
    duration: Optional[int] = None  # seconds
    thumbnail_url: Optional[str] = None
    transcript: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class EngagementMetrics(BaseModel):
    video_id: str
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    engagement_rate: Optional[float] = None
    message: Optional[str] = None
    
    def calculate_rate(self):
        if self.views and self.views > 0:
            total_engagement = (self.likes or 0) + (self.comments or 0)
            self.engagement_rate = (total_engagement / self.views) * 100
        else:
            self.engagement_rate = None
        return self

class TranscriptChunk(BaseModel):
    chunk_id: str
    video_id: str
    text: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = {}

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    citations: List[Dict[str, Any]] = []
    timestamp: datetime = Field(default_factory=datetime.now)

class ChatRequest(BaseModel):
    session_id: str
    message: str
    video_a_id: str
    video_b_id: str

class ProcessVideosRequest(BaseModel):
    youtube_url: str
    instagram_url: str

class ProcessVideosResponse(BaseModel):
    session_id: str
    video_a: VideoMetadata
    video_b: VideoMetadata
    engagement_a: EngagementMetrics
    engagement_b: EngagementMetrics