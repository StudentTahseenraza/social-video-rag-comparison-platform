from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json
from app.utils.helpers import setup_logging

logger = setup_logging()

class ConversationMemory:
    """Advanced conversation memory with summarization and pruning"""
    
    def __init__(self, max_history: int = 20, summarize_threshold: int = 15):
        self.max_history = max_history
        self.summarize_threshold = summarize_threshold
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.summaries: Dict[str, str] = {}
        
    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to conversation memory"""
        
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "messages": [],
                "context": {},
                "created_at": datetime.now(),
                "last_accessed": datetime.now()
            }
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.sessions[session_id]["messages"].append(message)
        self.sessions[session_id]["last_accessed"] = datetime.now()
        
        # Prune if needed
        if len(self.sessions[session_id]["messages"]) > self.max_history:
            self._prune_messages(session_id)
        
        # Summarize if threshold reached
        if len(self.sessions[session_id]["messages"]) >= self.summarize_threshold:
            self._summarize_conversation(session_id)
    
    def get_context(self, session_id: str, last_n: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation context"""
        
        if session_id not in self.sessions:
            return []
        
        messages = self.sessions[session_id]["messages"][-last_n:]
        
        # Add summary if available
        if session_id in self.summaries:
            context = [{
                "role": "system",
                "content": f"Previous conversation summary: {self.summaries[session_id]}",
                "timestamp": datetime.now().isoformat()
            }]
            context.extend(messages)
            return context
        
        return messages
    
    def update_context(self, session_id: str, key: str, value: Any):
        """Update session context with extracted information"""
        
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "messages": [],
                "context": {},
                "created_at": datetime.now(),
                "last_accessed": datetime.now()
            }
        
        self.sessions[session_id]["context"][key] = value
    
    def get_context_value(self, session_id: str, key: str) -> Optional[Any]:
        """Get specific context value"""
        
        if session_id in self.sessions:
            return self.sessions[session_id]["context"].get(key)
        return None
    
    def _prune_messages(self, session_id: str):
        """Prune old messages while preserving important ones"""
        
        messages = self.sessions[session_id]["messages"]
        
        # Keep important messages (with citations or key info)
        important = []
        regular = []
        
        for msg in messages:
            if msg.get("metadata", {}).get("important") or len(msg["content"]) > 200:
                important.append(msg)
            else:
                regular.append(msg)
        
        # Keep all important, trim regular to fit
        keep_count = self.max_history - len(important)
        if keep_count > 0 and regular:
            regular = regular[-keep_count:]
        
        self.sessions[session_id]["messages"] = important + regular
    
    async def _summarize_conversation(self, session_id: str):
        """Summarize conversation to maintain context"""
        
        messages = self.sessions[session_id]["messages"]
        
        # Extract key information
        key_topics = []
        video_references = []
        
        for msg in messages:
            content = msg["content"].lower()
            if "video a" in content or "video b" in content:
                video_references.append(msg["content"])
            if len(content) > 50:  # Substantive messages
                key_topics.append(content[:100])
        
        summary = f"Conversation covered {len(video_references)} video comparisons. "
        summary += f"Key topics: {'; '.join(key_topics[:3])}"
        
        self.summaries[session_id] = summary
        logger.info(f"Summarized conversation for session {session_id}")
    
    def clear_session(self, session_id: str):
        """Clear session memory"""
        
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.summaries:
            del self.summaries[session_id]
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics about a session"""
        
        if session_id not in self.sessions:
            return {"exists": False}
        
        session = self.sessions[session_id]
        return {
            "exists": True,
            "message_count": len(session["messages"]),
            "created_at": session["created_at"].isoformat(),
            "last_accessed": session["last_accessed"].isoformat(),
            "age_hours": (datetime.now() - session["created_at"]).total_seconds() / 3600,
            "has_summary": session_id in self.summaries,
            "context_keys": list(session["context"].keys())
        }
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove sessions older than max_age_hours"""
        
        now = datetime.now()
        expired = []
        
        for session_id, session in self.sessions.items():
            age = (now - session["last_accessed"]).total_seconds() / 3600
            if age > max_age_hours:
                expired.append(session_id)
        
        for session_id in expired:
            self.clear_session(session_id)
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
        
        return len(expired)

# Global memory instance
conversation_memory = ConversationMemory()