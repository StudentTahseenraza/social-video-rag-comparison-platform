import yt_dlp
import asyncio
import os
import tempfile
from typing import Optional
from app.models.schemas import VideoMetadata, VideoPlatform
from app.utils.helpers import extract_video_id

class InstagramService:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
    
    async def process_video(self, url: str) -> VideoMetadata:
        """Extract metadata and generate transcript for Instagram reel"""
        video_id = extract_video_id(url, 'instagram')
        
        # Extract metadata
        metadata = await self._extract_metadata(url)
        
        # Generate transcript from audio
        transcript = await self._generate_transcript(url)
        
        return VideoMetadata(
            video_id=video_id,
            platform=VideoPlatform.INSTAGRAM,
            url=url,
            title=metadata.get('title', '') or metadata.get('description', '')[:100],
            creator=metadata.get('uploader', 'unknown'),
            creator_followers=metadata.get('channel_follower_count'),  # Sometimes available
            views=metadata.get('view_count'),
            likes=metadata.get('like_count'),
            comments=metadata.get('comment_count'),
            hashtags=self._extract_hashtags(metadata.get('description', '')),
            upload_date=metadata.get('upload_date'),
            duration=metadata.get('duration'),
            thumbnail_url=metadata.get('thumbnail'),
            transcript=transcript
        )
    
    async def _extract_metadata(self, url: str) -> dict:
        """Extract metadata using yt-dlp"""
        def sync_extract():
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                    return info
                except Exception as e:
                    print(f"Instagram metadata extraction failed: {e}")
                    return {}
        
        return await asyncio.to_thread(sync_extract)
    
    async def _generate_transcript(self, url: str) -> Optional[str]:
        """Download video and generate transcript using faster-whisper"""
        try:
            # Download video
            video_path = await self._download_video(url)
            if not video_path:
                return None
            
            # Generate transcript
            transcript = await self._transcribe_audio(video_path)
            
            # Cleanup
            if os.path.exists(video_path):
                os.remove(video_path)
            
            return transcript
        except Exception as e:
            print(f"Transcript generation failed: {e}")
            return None
    
    async def _download_video(self, url: str) -> Optional[str]:
        """Download video to temp file"""
        def sync_download():
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_path = temp_file.name
            temp_file.close()
            
            ydl_opts = {
                'outtmpl': temp_path,
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([url])
                    return temp_path
                except:
                    return None
        
        return await asyncio.to_thread(sync_download)
    
    async def _transcribe_audio(self, video_path: str) -> Optional[str]:
        """Transcribe using faster-whisper (to be implemented in Phase 2)"""
        # Placeholder - will implement with faster-whisper in Phase 2
        return "Transcript generation will be implemented in Phase 2"
    
    def _extract_hashtags(self, text: str) -> list:
        """Extract hashtags from caption"""
        import re
        if not text:
            return []
        return re.findall(r'#(\w+)', text)