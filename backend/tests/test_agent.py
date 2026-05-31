import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.video_analyzer_agent import video_analyzer_agent
from app.services.rag_service import rag_service
from app.models.schemas import VideoMetadata, VideoPlatform
from app.utils.helpers import setup_logging

logger = setup_logging()

async def test_agent_workflow():
    """Test the LangGraph agent workflow"""
    
    logger.info("\n" + "="*60)
    logger.info("Testing LangGraph Agent Workflow")
    logger.info("="*60)
    
    # Create mock videos
    video_a = VideoMetadata(
        video_id="test_a_123",
        platform=VideoPlatform.YOUTUBE,
        url="https://youtube.com/test",
        title="How to Grow Your Channel - Top Strategies",
        creator="Growth Expert",
        views=150000,
        likes=12000,
        comments=450,
        hashtags=["growth", "tips", "youtube"],
        transcript="In this video I'm going to show you the top 5 strategies to grow your channel. First, create compelling hooks in the first 5 seconds. Second, maintain viewer retention with pattern interrupts. Third, end with a strong call to action. These strategies have helped me reach 1 million subscribers."
    )
    
    video_b = VideoMetadata(
        video_id="test_b_456",
        platform=VideoPlatform.INSTAGRAM,
        url="https://instagram.com/test",
        title="Quick Instagram Tips",
        creator="Social Media Coach",
        views=50000,
        likes=3000,
        comments=120,
        hashtags=["instagram", "tips", "reels"],
        transcript="Here are 3 quick Instagram tips. Post consistently. Use trending audio. Engage with comments. That's it for today!"
    )
    
    # Store in RAG
    session_id = "test_agent_session"
    await rag_service.store_video_transcript(session_id, video_a, video_b)
    
    # Initialize agent
    video_analyzer_agent.build_workflow()
    
    # Test complex questions
    test_questions = [
        "Why did Video A get more engagement than Video B?",
        "What specific strategies from Video A could improve Video B?",
        "Compare the hooks and suggest improvements",
        "Analyze the content strategy differences"
    ]
    
    for question in test_questions:
        logger.info(f"\n📝 Question: {question}")
        logger.info("-" * 40)
        
        async for result in video_analyzer_agent.process_question(
            session_id=session_id,
            question=question,
            video_a_id=video_a.video_id,
            video_b_id=video_b.video_id
        ):
            if result.get("type") == "analysis":
                logger.info(f"🔍 Analysis step: {result.get('content')}")
            elif result.get("type") == "complete":
                logger.info(f"✅ Final response:\n{result.get('content')[:500]}")
                if result.get("citations"):
                    logger.info(f"\n📚 Citations: {result.get('citations')}")
            elif result.get("type") == "error":
                logger.error(f"❌ Error: {result.get('error')}")
        
        await asyncio.sleep(1)  # Rate limiting

async def test_memory_management():
    """Test conversation memory features"""
    
    logger.info("\n" + "="*60)
    logger.info("Testing Memory Management")
    logger.info("="*60)
    
    from app.services.memory_service import conversation_memory
    
    session_id = "memory_test_session"
    
    # Add messages
    conversation_memory.add_message(session_id, "user", "What's the engagement rate?")
    conversation_memory.add_message(session_id, "assistant", "Video A has 8% engagement, Video B has 4%")
    conversation_memory.add_message(session_id, "user", "Why is it higher?")
    
    # Test follow-up resolution
    resolved = await rag_service._resolve_references("Why is it higher?", session_id)
    logger.info(f"Original: 'Why is it higher?'")
    logger.info(f"Resolved: '{resolved}'")
    
    # Test context retrieval
    context = conversation_memory.get_context(session_id)
    logger.info(f"Context length: {len(context)} messages")
    
    # Test stats
    stats = conversation_memory.get_session_stats(session_id)
    logger.info(f"Session stats: {stats}")

async def main():
    """Run all agent tests"""
    logger.info("🚀 Starting LangGraph Agent Tests")
    
    await test_agent_workflow()
    await test_memory_management()
    
    logger.info("\n✅ Agent tests complete!")

if __name__ == "__main__":
    asyncio.run(main())