import asyncio
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from app.utils.helpers import setup_logging, chunk_text
from app.models.schemas import VideoMetadata, TranscriptChunk

logger = setup_logging()

class VectorStore:
    """Vector database wrapper with ChromaDB (local, no API key needed)"""
    
    def __init__(self):
        self.collection = None
        self.embedding_function = None
        self.is_initialized = False
        self.chroma_client = None
        
    async def initialize(self):
        """Initialize ChromaDB and embedding model"""
        try:
            import chromadb
            from chromadb.utils import embedding_functions
            from sentence_transformers import SentenceTransformer
            
            # Initialize ChromaDB client (persistent)
            self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
            
            # Initialize embedding function with BGE-small
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
            logger.info("Vector store initialized successfully with BGE embeddings")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            self.is_initialized = False
            raise
    
    async def chunk_and_store(
        self, 
        session_id: str, 
        video_a: VideoMetadata, 
        video_b: VideoMetadata
    ) -> int:
        """Chunk transcripts and store in vector database"""
        if not self.is_initialized:
            await self.initialize()
        
        total_chunks = 0
        
        # Process Video A
        if video_a.transcript:
            chunks_a = await self._chunk_transcript(video_a, "A")
            await self._store_chunks(session_id, video_a.video_id, chunks_a)
            total_chunks += len(chunks_a)
            logger.info(f"Stored {len(chunks_a)} chunks for Video A")
        
        # Process Video B
        if video_b.transcript:
            chunks_b = await self._chunk_transcript(video_b, "B")
            await self._store_chunks(session_id, video_b.video_id, chunks_b)
            total_chunks += len(chunks_b)
            logger.info(f"Stored {len(chunks_b)} chunks for Video B")
        
        return total_chunks
    
    async def _chunk_transcript(
        self, 
        video: VideoMetadata, 
        label: str
    ) -> List[Dict[str, Any]]:
        """Split transcript into overlapping chunks with metadata"""
        if not video.transcript:
            return []
        
        # Use recursive chunking for better context
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        chunks = text_splitter.split_text(video.transcript)
        
        # Create chunk objects with metadata
        chunk_objects = []
        for i, chunk_text in enumerate(chunks):
            chunk = {
                "chunk_id": f"{video.video_id}_{i}_{uuid.uuid4().hex[:4]}",
                "video_id": video.video_id,
                "label": label,
                "text": chunk_text,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "metadata": {
                    "creator": video.creator,
                    "title": video.title[:100],
                    "platform": video.platform.value,
                    "views": video.views,
                    "likes": video.likes,
                    "comments": video.comments,
                    "engagement_rate": self._calculate_engagement(video),
                    "hashtags": video.hashtags[:5],
                    "upload_date": str(video.upload_date) if video.upload_date else None,
                    "duration": video.duration
                }
            }
            chunk_objects.append(chunk)
        
        return chunk_objects
    
    async def _store_chunks(
        self, 
        session_id: str, 
        video_id: str, 
        chunks: List[Dict[str, Any]]
    ):
        """Store chunks in ChromaDB"""
        if not chunks:
            return
        
        try:
            # Prepare data for ChromaDB
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
                    "views": chunk["metadata"]["views"] or 0,
                    "likes": chunk["metadata"]["likes"] or 0,
                    "comments": chunk["metadata"]["comments"] or 0,
                    "hashtags": ",".join(chunk["metadata"]["hashtags"]),
                    "title": chunk["metadata"]["title"]
                }
                for chunk in chunks
            ]
            
            # Add to collection
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Stored {len(chunks)} chunks in vector DB for video {video_id}")
            
        except Exception as e:
            logger.error(f"Failed to store chunks: {str(e)}")
            raise
    
    async def retrieve_relevant_chunks(
        self, 
        query: str, 
        session_id: str,
        video_a_id: str,
        video_b_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks for a query"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Query with metadata filtering
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k * 2,  # Get more then filter
                where={
                    "$and": [
                        {"session_id": session_id},
                        {"video_id": {"$in": [video_a_id, video_b_id]}}
                    ]
                }
            )
            
            # Format results
            chunks = []
            if results['ids'] and results['ids'][0]:
                for i, chunk_id in enumerate(results['ids'][0]):
                    chunks.append({
                        "chunk_id": chunk_id,
                        "text": results['documents'][0][i],
                        "video_id": results['metadatas'][0][i]['video_id'],
                        "label": results['metadatas'][0][i]['label'],
                        "relevance_score": results['distances'][0][i] if results.get('distances') else 1.0,
                        "metadata": results['metadatas'][0][i]
                    })
            
            # Sort by relevance and limit
            chunks.sort(key=lambda x: x['relevance_score'])
            chunks = chunks[:top_k]
            
            logger.info(f"Retrieved {len(chunks)} relevant chunks for query: {query[:50]}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to retrieve chunks: {str(e)}")
            return []
    
    def _calculate_engagement(self, video: VideoMetadata) -> Optional[float]:
        """Calculate engagement rate"""
        if video.views and video.views > 0:
            total_engagement = (video.likes or 0) + (video.comments or 0)
            return (total_engagement / video.views) * 100
        return None
    
    async def clear_session(self, session_id: str):
        """Clear all chunks for a session"""
        try:
            # Get all IDs for this session
            results = self.collection.get(
                where={"session_id": session_id}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Cleared {len(results['ids'])} chunks for session {session_id}")
                
        except Exception as e:
            logger.error(f"Failed to clear session: {str(e)}")
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "is_initialized": self.is_initialized,
                "collection_name": "video_transcripts"
            }
        except:
            return {"total_chunks": 0, "is_initialized": False}

# Global instance
vector_store = VectorStore()