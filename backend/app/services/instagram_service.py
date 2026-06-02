import yt_dlp
import asyncio
import os
import tempfile
import re
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.schemas import VideoMetadata, VideoPlatform
from app.utils.helpers import extract_video_id, setup_logging

logger = setup_logging()

class InstagramService:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'ignoreerrors': True,
            'no_color': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        self.temp_dir = tempfile.gettempdir()
    
    async def process_video(self, url: str) -> VideoMetadata:
        """Extract metadata and transcript for Instagram reel"""
        video_id = extract_video_id(url, 'instagram')
        logger.info(f"Processing Instagram reel: {video_id}")
        
        # Extract metadata
        metadata = await self._extract_metadata(url)
        
        # Extract description/caption as transcript
        description = metadata.get('description', '') or metadata.get('caption', '')
        hashtags = self._extract_hashtags(description)
        
        # Use description as transcript (Instagram doesn't provide actual transcripts)
        transcript = description if description else "No transcript available for this Instagram reel. Using metadata only."
        
        # Get creator name
        creator = metadata.get('uploader', metadata.get('channel', 'Unknown Creator'))
        
        # Get metrics
        views = self._safe_int(metadata.get('view_count'))
        likes = self._safe_int(metadata.get('like_count'))
        comments = self._safe_int(metadata.get('comment_count'))
        duration = self._safe_int(metadata.get('duration'))
        
        video_metadata = VideoMetadata(
            video_id=video_id,
            platform=VideoPlatform.INSTAGRAM,
            url=url,
            title=metadata.get('title', '') or f"Instagram Reel {video_id}",
            creator=creator,
            creator_followers=None,
            views=views,
            likes=likes,
            comments=comments,
            hashtags=hashtags,
            upload_date=None,
            duration=duration,
            thumbnail_url=metadata.get('thumbnail'),
            transcript=transcript
        )
        
        logger.info(f"Successfully processed Instagram reel: {video_id} - Creator: {creator}")
        return video_metadata
    
    async def _extract_metadata(self, url: str) -> Dict[str, Any]:
        """Extract metadata using yt-dlp"""
        def sync_extract():
            try:
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info is None:
                        return {}
                    
                    return {
                        'title': info.get('title', ''),
                        'uploader': info.get('uploader', ''),
                        'channel': info.get('channel', ''),
                        'view_count': info.get('view_count'),
                        'like_count': info.get('like_count'),
                        'comment_count': info.get('comment_count'),
                        'duration': info.get('duration'),
                        'description': info.get('description', ''),
                        'caption': info.get('description', ''),
                        'thumbnail': info.get('thumbnail'),
                        'tags': info.get('tags', []),
                    }
            except Exception as e:
                logger.error(f"Instagram metadata extraction failed: {str(e)}")
                return {}
        
        return await asyncio.to_thread(sync_extract)
    
    def _extract_hashtags(self, text: str) -> list:
        if not text:
            return []
        hashtags = re.findall(r'#(\w+)', text)
        seen = set()
        unique = []
        for tag in hashtags:
            if tag.lower() not in seen:
                seen.add(tag.lower())
                unique.append(tag)
        return unique[:15]
    
    def _safe_int(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None