#!/usr/bin/env python3
"""
Quick script to test Instagram reel processing
Usage: python scripts/test_instagram_reel.py "https://instagram.com/reel/..."
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.instagram_service import InstagramService
from app.utils.helpers import setup_logging

logger = setup_logging()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_instagram_reel.py <instagram_reel_url>")
        print("Example: python test_instagram_reel.py https://www.instagram.com/reel/C_AcKPTxsC5/")
        sys.exit(1)
    
    url = sys.argv[1]
    logger.info(f"Processing Instagram reel: {url}")
    
    service = InstagramService()
    
    try:
        result = await service.process_video(url)
        
        print("\n" + "="*60)
        print("✅ Instagram Reel Processing Results")
        print("="*60)
        print(f"Video ID: {result.video_id}")
        print(f"Creator: {result.creator}")
        print(f"Creator Followers: {result.creator_followers or 'N/A'}")
        print(f"Views: {result.views:,}" if result.views else "Views: N/A")
        print(f"Likes: {result.likes:,}" if result.likes else "Likes: N/A")
        print(f"Comments: {result.comments:,}" if result.comments else "Comments: N/A")
        print(f"Duration: {result.duration} seconds" if result.duration else "Duration: N/A")
        print(f"Hashtags: {', '.join(result.hashtags[:10])}" if result.hashtags else "Hashtags: None")
        print(f"Has Transcript: {result.transcript is not None}")
        if result.transcript:
            print(f"Transcript Preview: {result.transcript[:200]}...")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Failed to process: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())