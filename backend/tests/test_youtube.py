import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.youtube_service import YouTubeService
from app.utils.helpers import setup_logging

logger = setup_logging()

async def test_youtube_extraction():
    """Test YouTube metadata and transcript extraction"""
    
    youtube_service = YouTubeService()
    
    # Test URLs
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Astley - has transcript
        "https://youtu.be/jNQXAC9IVRw",  # First YouTube video
        "https://www.youtube.com/shorts/SXHMnicI6Pg"  # Shorts format
    ]
    
    for url in test_urls:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing: {url}")
        
        try:
            metadata = await youtube_service.process_video(url)
            
            logger.info(f"✅ Successfully processed: {metadata.title}")
            logger.info(f"   Creator: {metadata.creator}")
            logger.info(f"   Views: {metadata.views:,}")
            logger.info(f"   Likes: {metadata.likes:,}")
            logger.info(f"   Duration: {metadata.duration} seconds")
            logger.info(f"   Hashtags: {metadata.hashtags}")
            logger.info(f"   Transcript length: {len(metadata.transcript) if metadata.transcript else 0} chars")
            logger.info(f"   Has transcript: {metadata.transcript is not None}")
            
        except Exception as e:
            logger.error(f"❌ Failed: {str(e)}")

async def test_transcript_extraction():
    """Test transcript extraction specifically"""
    
    youtube_service = YouTubeService()
    
    # Video known to have transcript
    video_id = "dQw4w9WgXcQ"
    
    transcript = await youtube_service._get_transcript(video_id)
    
    if transcript:
        logger.info(f"✅ Transcript extracted successfully")
        logger.info(f"   Length: {len(transcript)} characters")
        logger.info(f"   Preview: {transcript[:200]}...")
    else:
        logger.error("❌ Failed to extract transcript")

if __name__ == "__main__":
    logger.info("Starting YouTube Service Tests...")
    
    # Run tests
    asyncio.run(test_youtube_extraction())
    asyncio.run(test_transcript_extraction())
    
    logger.info("\n✅ Tests complete!")