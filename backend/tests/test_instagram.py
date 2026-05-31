import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.instagram_service import InstagramService
from app.utils.helpers import setup_logging

logger = setup_logging()

async def test_instagram_extraction():
    """Test Instagram metadata and transcript extraction"""
    
    instagram_service = InstagramService()
    
    # Public Instagram reels for testing (use public figure accounts)
    test_urls = [
        "https://www.instagram.com/reel/C_AcKPTxsC5/",  # Example - replace with working public reel
        "https://www.instagram.com/reel/C_AcKPTxsC5/",  # Add more test URLs
    ]
    
    logger.info("="*60)
    logger.info("Testing Instagram Reel Extraction")
    logger.info("Note: Instagram data availability varies")
    logger.info("="*60)
    
    for url in test_urls:
        logger.info(f"\n📱 Testing: {url}")
        
        try:
            metadata = await instagram_service.process_video(url)
            
            logger.info(f"✅ Successfully processed: {metadata.title[:50]}")
            logger.info(f"   Creator: {metadata.creator}")
            logger.info(f"   Views: {metadata.views:,}" if metadata.views else "   Views: Not available")
            logger.info(f"   Likes: {metadata.likes:,}" if metadata.likes else "   Likes: Not available")
            logger.info(f"   Comments: {metadata.comments:,}" if metadata.comments else "   Comments: Not available")
            logger.info(f"   Hashtags: {metadata.hashtags[:5]}")
            logger.info(f"   Transcript length: {len(metadata.transcript) if metadata.transcript else 0} chars")
            logger.info(f"   Follower count: {metadata.creator_followers:,}" if metadata.creator_followers else "   Follower count: Not available")
            
        except Exception as e:
            logger.error(f"❌ Failed: {str(e)}")

async def test_transcript_generation():
    """Test transcript generation specifically"""
    
    instagram_service = InstagramService()
    
    # Use a URL that definitely has a video
    test_url = "https://www.instagram.com/reel/C_AcKPTxsC5/"
    
    logger.info("\n" + "="*60)
    logger.info("Testing Transcript Generation")
    logger.info("="*60)
    
    transcript = await instagram_service._generate_transcript_robust(test_url, "test_reel")
    
    if transcript:
        logger.info(f"✅ Transcript generated")
        logger.info(f"   Length: {len(transcript)} characters")
        logger.info(f"   Preview: {transcript[:200]}...")
    else:
        logger.error("❌ Failed to generate transcript")

async def test_metadata_fallbacks():
    """Test metadata fallback strategies"""
    
    instagram_service = InstagramService()
    
    # Test with URL that might have limited data
    test_url = "https://www.instagram.com/reel/C_AcKPTxsC5/"
    
    logger.info("\n" + "="*60)
    logger.info("Testing Metadata Fallbacks")
    logger.info("="*60)
    
    # Try primary method
    metadata1 = await instagram_service._extract_metadata_ytdlp(test_url)
    logger.info(f"Primary method: {'Success' if metadata1 else 'Failed'}")
    
    # Try fallback method
    metadata2 = await instagram_service._extract_metadata_fallback(test_url)
    logger.info(f"Fallback method: {'Success' if metadata2 else 'Failed'}")
    
    # Combined result
    final_metadata = {**(metadata1 or {}), **(metadata2 or {})}
    logger.info(f"Final metadata fields: {list(final_metadata.keys())}")

if __name__ == "__main__":
    logger.info("🚀 Starting Instagram Service Tests...")
    
    # Run tests
    asyncio.run(test_instagram_extraction())
    asyncio.run(test_transcript_generation())
    asyncio.run(test_metadata_fallbacks())
    
    logger.info("\n✅ Instagram tests complete!")
    logger.info("Note: If tests fail, Instagram may have changed their API")
    logger.info("The service includes fallbacks to handle various scenarios")