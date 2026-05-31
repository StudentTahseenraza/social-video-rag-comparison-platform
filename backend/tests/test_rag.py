import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vector_store import vector_store
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.models.schemas import VideoMetadata, VideoPlatform
from app.utils.helpers import setup_logging
from datetime import datetime

logger = setup_logging()

async def test_vector_store():
    """Test vector store operations"""
    logger.info("\n" + "="*60)
    logger.info("Testing Vector Store")
    logger.info("="*60)
    
    # Initialize
    await vector_store.initialize()
    
    # Test data
    test_chunks = [
        {
            "chunk_id": "test_1",
            "video_id": "test_video",
            "label": "A",
            "text": "This is a test video about AI technology and machine learning.",
            "metadata": {"creator": "Test Creator", "views": 1000}
        }
    ]
    
    # Store test chunks
    # Note: This would need collection setup
    
    stats = await vector_store.get_collection_stats()
    logger.info(f"Collection stats: {stats}")

async def test_llm_service():
    """Test LLM service"""
    logger.info("\n" + "="*60)
    logger.info("Testing LLM Service")
    logger.info("="*60)
    
    await llm_service.initialize()
    
    # Test response
    context_chunks = [
        {"label": "A", "text": "Video A has 1M views and 50K likes"},
        {"label": "B", "text": "Video B has 500K views and 10K likes"}
    ]
    
    response = ""
    async for chunk in llm_service.generate_response(
        query="Which video has better engagement?",
        context_chunks=context_chunks,
        chat_history=[]
    ):
        response += chunk
    
    logger.info(f"LLM Response: {response[:200]}...")

async def test_full_rag():
    """Test full RAG pipeline with mock data"""
    logger.info("\n" + "="*60)
    logger.info("Testing Full RAG Pipeline")
    logger.info("="*60)
    
    # Create mock videos
    video_a = VideoMetadata(
        video_id="test_a",
        platform=VideoPlatform.YOUTUBE,
        url="https://youtube.com/test",
        title="Test Video A",
        creator="Creator A",
        views=100000,
        likes=5000,
        comments=200,
        hashtags=["test", "ai"],
        transcript="This is a test transcript for video A. It has great content about machine learning and AI applications in real world scenarios."
    )
    
    video_b = VideoMetadata(
        video_id="test_b",
        platform=VideoPlatform.INSTAGRAM,
        url="https://instagram.com/test",
        title="Test Video B",
        creator="Creator B",
        views=50000,
        likes=2000,
        comments=100,
        hashtags=["test", "reel"],
        transcript="This is a test transcript for video B. It shows quick tips about social media growth."
    )
    
    # Store in RAG
    session_id = "test_session"
    await rag_service.store_video_transcript(session_id, video_a, video_b)
    
    # Test chat
    questions = [
        "Why did Video A get more engagement than Video B?",
        "What's the engagement rate of each?",
        "Compare the hooks"
    ]
    
    for question in questions:
        logger.info(f"\nQuestion: {question}")
        logger.info("-" * 40)
        
        async for chunk in rag_service.chat_stream(
            session_id=session_id,
            question=question,
            video_a_id=video_a.video_id,
            video_b_id=video_b.video_id
        ):
            if chunk.get('content'):
                print(chunk['content'], end='', flush=True)
            elif chunk.get('citations'):
                logger.info(f"\n\nCitations: {chunk['citations']}")
        
        print("\n")

async def main():
    """Run all tests"""
    logger.info("🚀 Starting RAG Pipeline Tests")
    
    # Run tests
    await test_vector_store()
    await test_llm_service()
    await test_full_rag()
    
    logger.info("\n✅ RAG pipeline tests complete!")

if __name__ == "__main__":
    asyncio.run(main())