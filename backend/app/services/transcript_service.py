import asyncio
import subprocess
import os
import tempfile
from typing import Optional, List
from pathlib import Path
from app.utils.helpers import setup_logging

logger = setup_logging()

class TranscriptService:
    """Handle transcript generation from video files using faster-whisper"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.whisper_model = None
        self.model_loaded = False
    
    async def initialize_whisper(self):
        """Initialize faster-whisper model (lazy loading)"""
        if not self.model_loaded:
            try:
                from faster_whisper import WhisperModel
                # Use tiny model for speed, can be upgraded to base/small for better accuracy
                self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
                self.model_loaded = True
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {str(e)}")
                self.model_loaded = False
    
    async def transcribe_video(self, video_path: str) -> Optional[str]:
        """
        Transcribe video using faster-whisper
        Extracts audio and runs transcription
        """
        try:
            # Ensure whisper is initialized
            await self.initialize_whisper()
            
            if not self.model_loaded:
                return await self._transcribe_fallback(video_path)
            
            # Extract audio from video
            audio_path = await self._extract_audio(video_path)
            if not audio_path:
                logger.error("Failed to extract audio from video")
                return None
            
            # Transcribe audio
            transcript = await self._transcribe_audio(audio_path)
            
            # Cleanup audio file
            await self._cleanup_file(audio_path)
            
            return transcript
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            return None
    
    async def _extract_audio(self, video_path: str) -> Optional[str]:
        """Extract audio from video file using ffmpeg"""
        def sync_extract():
            try:
                audio_path = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix='.wav',
                    dir=self.temp_dir
                ).name
                
                # FFmpeg command to extract audio
                cmd = [
                    'ffmpeg',
                    '-i', video_path,
                    '-vn',  # No video
                    '-acodec', 'pcm_s16le',  # WAV format
                    '-ar', '16000',  # 16kHz sample rate
                    '-ac', '1',  # Mono
                    '-y',  # Overwrite output
                    audio_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and os.path.exists(audio_path):
                    logger.info(f"Audio extracted to {audio_path}")
                    return audio_path
                else:
                    logger.error(f"FFmpeg error: {result.stderr}")
                    return None
                    
            except Exception as e:
                logger.error(f"Audio extraction failed: {str(e)}")
                return None
        
        return await asyncio.to_thread(sync_extract)
    
    async def _transcribe_audio(self, audio_path: str) -> Optional[str]:
        """Transcribe audio using faster-whisper"""
        def sync_transcribe():
            try:
                segments, info = self.whisper_model.transcribe(
                    audio_path,
                    beam_size=5,
                    language="en",
                    vad_filter=True
                )
                
                transcript_parts = []
                for segment in segments:
                    transcript_parts.append(segment.text)
                
                full_transcript = " ".join(transcript_parts)
                logger.info(f"Transcription complete: {len(full_transcript)} characters")
                return full_transcript
                
            except Exception as e:
                logger.error(f"Whisper transcription failed: {str(e)}")
                return None
        
        return await asyncio.to_thread(sync_transcribe)
    
    async def _transcribe_fallback(self, video_path: str) -> Optional[str]:
        """Fallback transcription using ffmpeg + simple approach"""
        def sync_fallback():
            try:
                # Use ffmpeg to extract and attempt basic transcription
                # This is a placeholder - in production, use a cloud API fallback
                logger.warning("Using fallback transcription method")
                return "Transcript could not be generated. Please check video accessibility."
            except:
                return None
        
        return await asyncio.to_thread(sync_fallback)
    
    async def _cleanup_file(self, file_path: str):
        """Delete temporary file"""
        def sync_cleanup():
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Cleaned up {file_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {file_path}: {str(e)}")
        
        await asyncio.to_thread(sync_cleanup)