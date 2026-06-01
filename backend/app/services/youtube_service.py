import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)
from app.models.schemas import VideoMetadata, VideoPlatform
from app.utils.helpers import extract_video_id, setup_logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import re

logger = setup_logging()

class YouTubeService:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'ignoreerrors': True,
            'no_color': True,
        }
        
    async def process_video(self, url: str) -> VideoMetadata:
        """
        Extract metadata and transcript from YouTube video
        Returns complete VideoMetadata object
        """
        video_id = extract_video_id(url, 'youtube')
        logger.info(f"Processing YouTube video: {video_id}")
        
        # Extract metadata with yt-dlp
        metadata = await self._extract_metadata(url)
        
        if not metadata:
            raise ValueError(f"Failed to extract metadata for YouTube video: {url}")
        
        # Get transcript (with fallback)
        transcript = await self._get_transcript(video_id)
        
        # If no transcript available, try to generate from audio
        if not transcript:
            logger.warning(f"No transcript available for {video_id}, attempting audio transcription")
            transcript = await self._generate_transcript_from_audio(url)
        
        # Parse upload date
        upload_date = None
        if metadata.get('upload_date'):
            try:
                upload_date = datetime.strptime(metadata['upload_date'], '%Y%m%d')
            except:
                pass
        
        # Extract hashtags from description
        description = metadata.get('description', '')
        hashtags = self._extract_hashtags(description)
        
        # Get creator name (handle different field names)
        creator = (
            metadata.get('channel') or 
            metadata.get('uploader') or 
            metadata.get('creator') or 
            'Unknown Creator'
        )
        
        video_metadata = VideoMetadata(
            video_id=video_id,
            platform=VideoPlatform.YOUTUBE,
            url=url,
            title=metadata.get('title', 'Untitled Video'),
            creator=creator,
            creator_followers=None,  # YouTube doesn't expose subscriber count easily
            views=metadata.get('view_count'),
            likes=metadata.get('like_count'),
            comments=metadata.get('comment_count'),
            hashtags=hashtags,
            upload_date=upload_date,
            duration=metadata.get('duration'),
            thumbnail_url=metadata.get('thumbnail'),
            transcript=transcript
        )
        
        logger.info(f"Successfully processed YouTube video: {video_id} - {video_metadata.title[:50]}")
        return video_metadata
    
    async def _extract_metadata(self, url: str) -> Dict[str, Any]:
        """Extract metadata using yt-dlp with async wrapper"""
        def sync_extract():
            try:
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info is None:
                        logger.error(f"Failed to extract info for {url}")
                        return {}
                    
                    # Clean and return relevant fields
                    return {
                        'title': info.get('title'),
                        'uploader': info.get('uploader'),
                        'channel': info.get('channel'),
                        'creator': info.get('creator'),
                        'view_count': info.get('view_count'),
                        'like_count': info.get('like_count'),
                        'comment_count': info.get('comment_count'),
                        'duration': info.get('duration'),
                        'upload_date': info.get('upload_date'),
                        'description': info.get('description', ''),
                        'thumbnail': info.get('thumbnail'),
                        'tags': info.get('tags', []),
                        'categories': info.get('categories', []),
                    }
            except Exception as e:
                logger.error(f"Error extracting YouTube metadata: {str(e)}")
                return {}
        
        return await asyncio.to_thread(sync_extract)
    
    async def _get_transcript(self, video_id: str) -> Optional[str]:
        """Get transcript using youtube-transcript-api"""
        try:
            def sync_get_transcript():
                try:
                    from youtube_transcript_api import YouTubeTranscriptApi
                    # Correct method - get_transcript is a function, not class method
                    transcript_list = YouTubeTranscriptApi().get_transcript(video_id, languages=['en'])
                    full_text = ' '.join([entry['text'] for entry in transcript_list])
                    return full_text
                except Exception as e:
                    logger.warning(f"Transcript error for {video_id}: {str(e)}")
                    return None
            
            return await asyncio.to_thread(sync_get_transcript)
            
        except Exception as e:
            logger.error(f"Failed to get transcript for {video_id}: {str(e)}")
            return None
    
    async def _generate_transcript_from_audio(self, url: str) -> Optional[str]:
        """
        Fallback: Download audio and transcribe using faster-whisper
        Will be fully implemented in Phase 2
        """
        # Placeholder - will implement with faster-whisper
        logger.info(f"Audio transcription fallback triggered for {url}")
        
        # For now, return a message indicating transcript is being processed
        # In production, this would queue a background job
        return "Transcript is being generated from audio. Please check back later."
    
    def _extract_hashtags(self, text: str) -> list:
        """Extract hashtags from description"""
        if not text:
            return []
        # Find all #hashtag patterns
        hashtags = re.findall(r'#(\w+)', text)
        # Remove duplicates while preserving order
        seen = set()
        unique_hashtags = []
        for tag in hashtags:
            if tag.lower() not in seen:
                seen.add(tag.lower())
                unique_hashtags.append(tag)
        return unique_hashtags[:10]  # Limit to 10 hashtags
    
    async def get_video_details(self, video_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific video ID"""
        url = f"https://youtube.com/watch?v={video_id}"
        return await self._extract_metadata(url)