import asyncio
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.utils.helpers import setup_logging
from app.models.schemas import VideoMetadata

logger = setup_logging()

class VectorStore:
    """Professional vector store with ChromaDB and BGE embeddings"""
    
    def __init__(self):
        self.collection = None
        self.is_initialized = False
        self.chroma_client = None
    
    async def initialize(self):
        """Initialize ChromaDB with BGE embeddings"""
        try:
            import chromadb
            from chromadb.utils import embedding_functions
            
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
            
            # Use BGE embeddings
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="BAAI/bge-small-en-v1.5"
            )
            
            # Get or create collection
            try:
                self.collection = self.chroma_client.get_collection(
                    name="video_transcripts",
                    embedding_function=self.embedding_function
                )
                logger.info("Loaded existing ChromaDB collection")
            except:
                self.collection = self.chroma_client.create_collection(
                    name="video_transcripts",
                    embedding_function=self.embedding_function,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("Created new ChromaDB collection")
            
            self.is_initialized = True
            logger.info("Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Vector store initialization failed: {str(e)}")
            self.is_initialized = False
            raise
    
    async def chunk_and_store(self, session_id: str, video_a: VideoMetadata, video_b: VideoMetadata) -> int:
        """Chunk transcripts and store in vector database"""
        if not self.is_initialized:
            await self.initialize()
        
        total_chunks = 0
        
        # Process Video A
        if video_a.transcript:
            chunks_a = self._chunk_transcript(video_a.transcript, video_a.video_id, "A", video_a)
            if chunks_a:
                await self._store_chunks(session_id, chunks_a)
                total_chunks += len(chunks_a)
                logger.info(f"Stored {len(chunks_a)} chunks for Video A")
        
        # Process Video B
        if video_b.transcript:
            chunks_b = self._chunk_transcript(video_b.transcript, video_b.video_id, "B", video_b)
            if chunks_b:
                await self._store_chunks(session_id, chunks_b)
                total_chunks += len(chunks_b)
                logger.info(f"Stored {len(chunks_b)} chunks for Video B")
        
        return total_chunks
    
    def _chunk_transcript(self, transcript: str, video_id: str, label: str, video: VideoMetadata) -> List[Dict[str, Any]]:
        """Split transcript into overlapping chunks"""
        if not transcript:
            return []
        
        chunk_size = 500
        chunk_overlap = 50
        
        # Split into chunks
        chunks = []
        start = 0
        text_length = len(transcript)
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            
            # Try to end at a sentence boundary
            if end < text_length:
                last_period = transcript.rfind('.', start, end)
                last_exclamation = transcript.rfind('!', start, end)
                last_question = transcript.rfind('?', start, end)
                last_boundary = max(last_period, last_exclamation, last_question)
                if last_boundary > start:
                    end = last_boundary + 1
            
            chunk_text = transcript[start:end].strip()
            if chunk_text:
                chunks.append({
                    "chunk_id": f"{video_id}_{len(chunks)}",
                    "video_id": video_id,
                    "label": label,
                    "text": chunk_text,
                    "chunk_index": len(chunks),
                    "metadata": {
                        "creator": video.creator,
                        "title": video.title[:100],
                        "platform": video.platform.value,
                        "views": video.views or 0,
                        "likes": video.likes or 0,
                        "comments": video.comments or 0,
                        "hashtags": ",".join(video.hashtags[:5]),
                        "duration": video.duration or 0
                    }
                })
            
            start = end - chunk_overlap if end < text_length else text_length
        
        return chunks
    
    async def _store_chunks(self, session_id: str, chunks: List[Dict[str, Any]]):
        """Store chunks in ChromaDB"""
        if not chunks:
            return
        
        try:
            ids = [chunk["chunk_id"] for chunk in chunks]
            documents = [chunk["text"] for chunk in chunks]
            metadatas = [
                {
                    "session_id": session_id,
                    "video_id": chunk["video_id"],
                    "label": chunk["label"],
                    "chunk_index": chunk["chunk_index"],
                    "creator": chunk["metadata"]["creator"],
                    "platform": chunk["metadata"]["platform"],
                    "views": chunk["metadata"]["views"],
                    "likes": chunk["metadata"]["likes"],
                    "comments": chunk["metadata"]["comments"],
                    "hashtags": chunk["metadata"]["hashtags"]
                }
                for chunk in chunks
            ]
            
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
        except Exception as e:
            logger.error(f"Failed to store chunks: {str(e)}")
    
    async def retrieve_relevant_chunks(self, query: str, session_id: str, video_a_id: str, video_b_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks for a query"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where={
                    "$and": [
                        {"session_id": session_id},
                        {"video_id": {"$in": [video_a_id, video_b_id]}}
                    ]
                }
            )
            
            chunks = []
            if results['ids'] and results['ids'][0]:
                for i, chunk_id in enumerate(results['ids'][0]):
                    chunks.append({
                        "chunk_id": chunk_id,
                        "text": results['documents'][0][i],
                        "video_id": results['metadatas'][0][i]['video_id'],
                        "label": results['metadatas'][0][i]['label'],
                        "relevance_score": 1 - results['distances'][0][i] if results.get('distances') else 1.0
                    })
            
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to retrieve chunks: {str(e)}")
            return []
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        try:
            count = self.collection.count()
            return {"total_chunks": count, "is_initialized": self.is_initialized}
        except:
            return {"total_chunks": 0, "is_initialized": False}

vector_store = VectorStore()