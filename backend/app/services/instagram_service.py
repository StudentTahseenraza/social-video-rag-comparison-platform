import yt_dlp
import asyncio
import os
import tempfile
import subprocess
import re
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path
from app.models.schemas import VideoMetadata, VideoPlatform
from app.utils.helpers import extract_video_id, setup_logging, chunk_text
from app.services.transcript_service import TranscriptService

logger = setup_logging()

class InstagramService:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'ignoreerrors': True,
            'no_color': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.transcript_service = TranscriptService()
        self.temp_dir = tempfile.gettempdir()
        
    async def process_video(self, url: str) -> VideoMetadata:
        """
        Extract metadata and generate transcript for Instagram reel
        Implements multiple fallback strategies for robustness
        """
        video_id = extract_video_id(url, 'instagram')
        logger.info(f"Processing Instagram reel: {video_id}")
        
        # Strategy 1: Try yt-dlp for metadata
        metadata = await self._extract_metadata_ytdlp(url)
        
        # Strategy 2: If yt-dlp fails, try instaloader approach
        if not metadata or not metadata.get('uploader'):
            logger.warning(f"yt-dlp failed for {video_id}, trying fallback method")
            metadata = await self._extract_metadata_fallback(url)
        
        # Strategy 3: If still no metadata, create basic structure
        if not metadata:
            metadata = {
                'title': f"Instagram Reel {video_id}",
                'uploader': 'Unknown Creator',
                'view_count': None,
                'like_count': None,
                'comment_count': None,
                'duration': None,
                'upload_date': datetime.now().strftime('%Y%m%d'),
                'description': '',
                'thumbnail': None
            }
            logger.warning(f"Using fallback metadata for {video_id}")
        
        # Generate transcript from video/audio
        transcript = await self._generate_transcript_robust(url, video_id)
        
        # Extract hashtags from description/caption
        description = metadata.get('description', '') or metadata.get('caption', '')
        hashtags = self._extract_hashtags(description)
        
        # Parse upload date
        upload_date = None
        if metadata.get('upload_date'):
            try:
                upload_date_str = str(metadata['upload_date'])
                if len(upload_date_str) == 8:  # YYYYMMDD format
                    upload_date = datetime.strptime(upload_date_str, '%Y%m%d')
                else:
                    upload_date = datetime.now()
            except:
                upload_date = datetime.now()
        
        # Get follower count if available
        follower_count = None
        if metadata.get('channel_follower_count'):
            follower_count = metadata['channel_follower_count']
        elif metadata.get('uploader_followers'):
            follower_count = metadata['uploader_followers']
        
        video_metadata = VideoMetadata(
            video_id=video_id,
            platform=VideoPlatform.INSTAGRAM,
            url=url,
            title=metadata.get('title', '') or f"Instagram Reel {video_id}",
            creator=metadata.get('uploader', 'Unknown Creator'),
            creator_followers=follower_count,
            views=self._safe_int(metadata.get('view_count')),
            likes=self._safe_int(metadata.get('like_count')),
            comments=self._safe_int(metadata.get('comment_count')),
            hashtags=hashtags,
            upload_date=upload_date,
            duration=self._safe_int(metadata.get('duration')),
            thumbnail_url=metadata.get('thumbnail'),
            transcript=transcript
        )
        
        logger.info(f"Successfully processed Instagram reel: {video_id} - Creator: {video_metadata.creator}")
        return video_metadata
    
    async def _extract_metadata_ytdlp(self, url: str) -> Dict[str, Any]:
        """Extract metadata using yt-dlp (primary method)"""
        def sync_extract():
            try:
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info is None:
                        return {}
                    
                    # Clean and map fields
                    return {
                        'title': info.get('title', ''),
                        'uploader': info.get('uploader', ''),
                        'view_count': info.get('view_count'),
                        'like_count': info.get('like_count'),
                        'comment_count': info.get('comment_count'),
                        'duration': info.get('duration'),
                        'upload_date': info.get('upload_date'),
                        'description': info.get('description', ''),
                        'caption': info.get('description', ''),
                        'thumbnail': info.get('thumbnail'),
                        'channel_follower_count': info.get('channel_follower_count'),
                        'uploader_followers': info.get('uploader_followers'),
                        'tags': info.get('tags', []),
                    }
            except Exception as e:
                logger.error(f"yt-dlp metadata extraction failed: {str(e)}")
                return {}
        
        return await asyncio.to_thread(sync_extract)
    
    async def _extract_metadata_fallback(self, url: str) -> Dict[str, Any]:
        """Fallback metadata extraction using alternative approach"""
        try:
            # Try to extract basic info from URL
            video_id = extract_video_id(url, 'instagram')
            
            # Use yt-dlp with different options
            fallback_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': 'in_playlist',
                'force_generic_extractor': True,
            }
            
            def sync_fallback():
                with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                    try:
                        info = ydl.extract_info(url, download=False)
                        if info:
                            return {
                                'uploader': info.get('uploader', 'Instagram Creator'),
                                'view_count': info.get('view_count'),
                                'like_count': info.get('like_count'),
                                'duration': info.get('duration'),
                                'description': info.get('description', ''),
                            }
                    except:
                        pass
                return {}
            
            return await asyncio.to_thread(sync_fallback)
            
        except Exception as e:
            logger.error(f"Fallback metadata extraction failed: {str(e)}")
            return {}
    
    async def _generate_transcript_robust(self, url: str, video_id: str) -> Optional[str]:
        """
        Generate transcript with multiple strategies:
        1. Try to find existing captions
        2. Download video and transcribe with Whisper
        3. Use description as fallback
        """
        
        # Strategy 1: Check if video has captions/subtitles
        captions = await self._extract_captions(url)
        if captions:
            logger.info(f"Found captions for Instagram reel {video_id}")
            return captions
        
        # Strategy 2: Download and transcribe
        transcript = await self._download_and_transcribe(url, video_id)
        if transcript:
            logger.info(f"Successfully generated transcript for {video_id}")
            return transcript
        
        # Strategy 3: Use description as fallback
        logger.warning(f"No transcript available for {video_id}, using description")
        return "No transcript available. Video description or captions could not be extracted."
    
    async def _extract_captions(self, url: str) -> Optional[str]:
        """Extract existing captions/subtitles from Instagram reel"""
        def sync_extract():
            try:
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info and info.get('subtitles'):
                        # Get English subtitles if available
                        subs = info.get('subtitles', {})
                        for lang in ['en', 'en-US', 'original']:
                            if lang in subs and subs[lang]:
                                return " ".join([s.get('text', '') for s in subs[lang]])
                    return None
            except Exception as e:
                logger.debug(f"Caption extraction failed: {str(e)}")
                return None
        
        return await asyncio.to_thread(sync_extract)
    
    async def _download_and_transcribe(self, url: str, video_id: str) -> Optional[str]:
        """Download video and transcribe using faster-whisper"""
        video_path = None
        
        try:
            # Download video
            video_path = await self._download_instagram_video(url, video_id)
            if not video_path:
                logger.error(f"Failed to download video for {video_id}")
                return None
            
            # Extract audio and transcribe
            transcript = await self.transcript_service.transcribe_video(video_path)
            
            return transcript
            
        except Exception as e:
            logger.error(f"Download/transcribe failed for {video_id}: {str(e)}")
            return None
            
        finally:
            # Cleanup
            if video_path and os.path.exists(video_path):
                await self._cleanup_file(video_path)
    
    async def _download_instagram_video(self, url: str, video_id: str) -> Optional[str]:
        """Download Instagram reel video"""
        def sync_download():
            try:
                # Create temp file path
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix='.mp4',
                    dir=self.temp_dir,
                    prefix=f"ig_{video_id}_"
                )
                temp_path = temp_file.name
                temp_file.close()
                
                # Download video
                ydl_opts = {
                    'outtmpl': temp_path,
                    'quiet': True,
                    'no_warnings': True,
                    'format': 'best[ext=mp4]/best',
                    'no-playlist': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                    logger.info(f"Downloaded video to {temp_path} ({os.path.getsize(temp_path)} bytes)")
                    return temp_path
                else:
                    logger.error(f"Downloaded file is empty or missing: {temp_path}")
                    return None
                    
            except Exception as e:
                logger.error(f"Video download failed: {str(e)}")
                return None
        
        return await asyncio.to_thread(sync_download)
    
    async def _cleanup_file(self, file_path: str):
        """Clean up temporary file"""
        def sync_cleanup():
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Cleaned up {file_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {file_path}: {str(e)}")
        
        await asyncio.to_thread(sync_cleanup)
    
    def _extract_hashtags(self, text: str) -> list:
        """Extract hashtags from caption/description"""
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
        
        return unique_hashtags[:15]  # Limit to 15 hashtags
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert to int, return None if invalid"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None