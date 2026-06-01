import yt_dlp
import requests
import json
import re
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.schemas import VideoMetadata, VideoPlatform
from app.utils.helpers import extract_video_id, setup_logging

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
        video_id = extract_video_id(url, 'youtube')
        logger.info(f"Processing YouTube video: {video_id}")
        
        metadata = await self._extract_metadata(url)
        
        if not metadata:
            raise ValueError(f"Failed to extract metadata for YouTube video: {url}")
        
        # Get transcript - CRITICAL FIX
        transcript = await self._get_transcript_working(video_id)
        
        if transcript:
            logger.info(f"✅ Got transcript for {video_id}: {len(transcript)} characters")
        else:
            logger.warning(f"❌ No transcript for {video_id}")
        
        upload_date = None
        if metadata.get('upload_date'):
            try:
                upload_date = datetime.strptime(metadata['upload_date'], '%Y%m%d')
            except:
                pass
        
        hashtags = self._extract_hashtags(metadata.get('description', ''))
        creator = metadata.get('channel') or metadata.get('uploader') or 'Unknown Creator'
        
        return VideoMetadata(
            video_id=video_id,
            platform=VideoPlatform.YOUTUBE,
            url=url,
            title=metadata.get('title', 'Untitled Video'),
            creator=creator,
            creator_followers=None,
            views=metadata.get('view_count'),
            likes=metadata.get('like_count'),
            comments=metadata.get('comment_count'),
            hashtags=hashtags,
            upload_date=upload_date,
            duration=metadata.get('duration'),
            thumbnail_url=metadata.get('thumbnail'),
            transcript=transcript
        )
    
    async def _get_transcript_working(self, video_id: str) -> Optional[str]:
        """Get transcript using yt-dlp with proper caption extraction"""
        
        def sync_extract():
            try:
                url = f"https://www.youtube.com/watch?v={video_id}"
                
                ydl_opts = {
                    'quiet': True,
                    'skip_download': True,
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'subtitlesformat': 'json3',
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    # Try automatic captions
                    if 'automatic_captions' in info:
                        for lang in ['en', 'en-US', 'en-GB']:
                            if lang in info['automatic_captions']:
                                captions = info['automatic_captions'][lang]
                                if captions:
                                    caption_url = captions[0]['url']
                                    response = requests.get(caption_url, timeout=30)
                                    if response.status_code == 200:
                                        data = response.json()
                                        text_parts = []
                                        if 'events' in data:
                                            for event in data['events']:
                                                if 'segs' in event:
                                                    for seg in event['segs']:
                                                        if 'utf8' in seg:
                                                            text_parts.append(seg['utf8'])
                                        if text_parts:
                                            transcript = ' '.join(text_parts)
                                            logger.info(f"Got captions from automatic: {len(transcript)} chars")
                                            return transcript
                    
                    # Try manual subtitles
                    if 'subtitles' in info:
                        for lang in ['en', 'en-US', 'en-GB']:
                            if lang in info['subtitles']:
                                subs = info['subtitles'][lang]
                                if subs:
                                    sub_url = subs[0]['url']
                                    response = requests.get(sub_url, timeout=30)
                                    if response.status_code == 200:
                                        if sub_url.endswith('.json'):
                                            data = response.json()
                                            text_parts = []
                                            if 'events' in data:
                                                for event in data['events']:
                                                    if 'segs' in event:
                                                        for seg in event['segs']:
                                                            if 'utf8' in seg:
                                                                text_parts.append(seg['utf8'])
                                            if text_parts:
                                                transcript = ' '.join(text_parts)
                                                logger.info(f"Got captions from manual: {len(transcript)} chars")
                                                return transcript
                    
                    return None
                    
            except Exception as e:
                logger.error(f"Transcript extraction error: {e}")
                return None
        
        return await asyncio.to_thread(sync_extract)
    
    async def _extract_metadata(self, url: str) -> Dict[str, Any]:
        def sync_extract():
            try:
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        return {}
                    return {
                        'title': info.get('title'),
                        'uploader': info.get('uploader'),
                        'channel': info.get('channel'),
                        'view_count': info.get('view_count'),
                        'like_count': info.get('like_count'),
                        'comment_count': info.get('comment_count'),
                        'duration': info.get('duration'),
                        'upload_date': info.get('upload_date'),
                        'description': info.get('description', ''),
                        'thumbnail': info.get('thumbnail'),
                    }
            except Exception as e:
                logger.error(f"Metadata error: {e}")
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
        return unique[:10]