import asyncio
import subprocess
import os
import tempfile
from typing import Optional
from app.utils.helpers import setup_logging

logger = setup_logging()

class TranscriptService:
    """Handle transcript generation from video files"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    async def download_audio(self, url: str) -> Optional[str]:
        """Download audio from video URL using yt-dlp"""
        def sync_download():
            try:
                # Create temp file path
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix='.mp3',
                    dir=self.temp_dir
                )
                temp_path = temp_file.name
                temp_file.close()
                
                # Download audio only
                cmd = [
                    'yt-dlp',
                    '-f', 'bestaudio',
                    '--extract-audio',
                    '--audio-format', 'mp3',
                    '--audio-quality', '128K',
                    '--output', temp_path,
                    '--no-playlist',
                    '--quiet',
                    '--no-warnings',
                    url
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and os.path.exists(temp_path):
                    logger.info(f"Successfully downloaded audio to {temp_path}")
                    return temp_path
                else:
                    logger.error(f"Failed to download audio: {result.stderr}")
                    return None
                    
            except Exception as e:
                logger.error(f"Error downloading audio: {str(e)}")
                return None
        
        return await asyncio.to_thread(sync_download)
    
    async def transcribe_audio(self, audio_path: str) -> Optional[str]:
        """
        Transcribe audio using faster-whisper
        Will be fully implemented in Phase 2
        """
        # Placeholder - actual implementation in Phase 2
        logger.info(f"Transcribing audio from {audio_path}")
        
        # For now, return placeholder
        return "Audio transcription will be available in Phase 2"
    
    async def cleanup_file(self, file_path: str):
        """Delete temporary file"""
        def sync_cleanup():
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up {file_path}")
            except Exception as e:
                logger.error(f"Failed to cleanup {file_path}: {str(e)}")
        
        await asyncio.to_thread(sync_cleanup)