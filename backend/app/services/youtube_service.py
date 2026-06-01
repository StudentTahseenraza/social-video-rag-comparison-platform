import yt_dlp
import requests
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
        """Extract metadata and transcript from YouTube video"""
        video_id = extract_video_id(url, 'youtube')
        logger.info(f"Processing YouTube video: {video_id}")
        
        # Extract metadata
        metadata = await self._extract_metadata(url)
        
        if not metadata:
            raise ValueError(f"Failed to extract metadata for YouTube video: {url}")
        
        # Get transcript using working method
        transcript = await self._get_transcript_working(video_id)
        
        # Parse upload date
        upload_date = None
        if metadata.get('upload_date'):
            try:
                upload_date = datetime.strptime(metadata['upload_date'], '%Y%m%d')
            except:
                pass
        
        # Extract hashtags
        description = metadata.get('description', '')
        hashtags = self._extract_hashtags(description)
        
        creator = metadata.get('channel') or metadata.get('uploader') or 'Unknown Creator'
        
        video_metadata = VideoMetadata(
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
        
        logger.info(f"Successfully processed YouTube video: {video_id} - Transcript: {len(transcript) if transcript else 0} chars")
        return video_metadata
    
    async def _get_transcript_working(self, video_id: str) -> Optional[str]:
        """WORKING METHOD: Extract transcript using yt-dlp"""
        
        def sync_extract():
            try:
                url = f"https://www.youtube.com/watch?v={video_id}"
                
                ydl_opts = {
                    'quiet': True,
                    'skip_download': True,
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'subtitlesformat': 'json3',
                    'subtitleslangs': ['en'],
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    # Try automatic captions first
                    if 'automatic_captions' in info and 'en' in info['automatic_captions']:
                        captions = info['automatic_captions']['en']
                        if captions:
                            caption_url = captions[0]['url']
                            response = requests.get(caption_url)
                            
                            if response.status_code == 200:
                                data = response.json()
                                
                                if 'events' in data:
                                    text_parts = []
                                    for event in data['events']:
                                        if 'segs' in event:
                                            for seg in event['segs']:
                                                if 'utf8' in seg:
                                                    text_parts.append(seg['utf8'])
                                    
                                    transcript = ' '.join(text_parts)
                                    if transcript:
                                        logger.info(f"Got automatic captions for {video_id}: {len(transcript)} chars")
                                        return transcript
                    
                    # Try regular subtitles
                    if 'subtitles' in info and 'en' in info['subtitles']:
                        subtitles = info['subtitles']['en']
                        if subtitles:
                            caption_url = subtitles[0]['url']
                            response = requests.get(caption_url)
                            
                            if response.status_code == 200:
                                if caption_url.endswith('.json'):
                                    data = response.json()
                                    if 'events' in data:
                                        text_parts = []
                                        for event in data['events']:
                                            if 'segs' in event:
                                                for seg in event['segs']:
                                                    if 'utf8' in seg:
                                                        text_parts.append(seg['utf8'])
                                        
                                        transcript = ' '.join(text_parts)
                                        if transcript:
                                            logger.info(f"Got regular subtitles for {video_id}: {len(transcript)} chars")
                                            return transcript
                    
                    logger.warning(f"No captions found for {video_id}")
                    return None
                    
            except Exception as e:
                logger.error(f"Transcript extraction error: {str(e)}")
                return None
        
        return await asyncio.to_thread(sync_extract)
    
    async def _extract_metadata(self, url: str) -> Dict[str, Any]:
        """Extract metadata using yt-dlp"""
        def sync_extract():
            try:
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info is None:
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
                logger.error(f"Error extracting metadata: {str(e)}")
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