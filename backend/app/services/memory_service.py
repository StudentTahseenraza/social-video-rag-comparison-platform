from typing import Dict, List, Any, Optional
from datetime import datetime
import re

class ConversationMemory:
    """Advanced memory with pronoun resolution and context tracking"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "messages": [],
                "last_video_ref": None,
                "last_topic": None,
                "created_at": datetime.now()
            }
        
        # Track last referenced video
        if "Video A" in content or "video a" in content.lower():
            self.sessions[session_id]["last_video_ref"] = "A"
        elif "Video B" in content or "video b" in content.lower():
            self.sessions[session_id]["last_video_ref"] = "B"
        
        self.sessions[session_id]["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
    
    def resolve_references(self, session_id: str, question: str) -> str:
        """Resolve pronouns like 'it', 'they', 'their' to actual video references"""
        if session_id not in self.sessions:
            return question
        
        session = self.sessions[session_id]
        last_ref = session.get("last_video_ref", "A")
        
        # Get last few messages for context
        last_messages = session["messages"][-3:] if session["messages"] else []
        
        question_lower = question.lower()
        resolved = question
        
        # Resolve pronouns based on last reference
        if "it" in question_lower and last_ref:
            resolved = resolved.replace("it", f"Video {last_ref}")
            resolved = resolved.replace("It", f"Video {last_ref}")
        if "they" in question_lower and last_ref:
            resolved = resolved.replace("they", f"Video {last_ref}")
            resolved = resolved.replace("They", f"Video {last_ref}")
        if "their" in question_lower and last_ref:
            resolved = resolved.replace("their", f"Video {last_ref}'s")
            resolved = resolved.replace("Their", f"Video {last_ref}'s")
        if "its" in question_lower and last_ref:
            resolved = resolved.replace("its", f"Video {last_ref}'s")
        
        # Check for "the first video", "the second video"
        if "first video" in question_lower:
            resolved = resolved.replace("first video", "Video A")
        if "second video" in question_lower:
            resolved = resolved.replace("second video", "Video B")
        
        return resolved
    
    def get_context(self, session_id: str) -> str:
        """Get conversation context as string"""
        if session_id not in self.sessions:
            return ""
        
        messages = self.sessions[session_id]["messages"][-5:]
        context = []
        for msg in messages:
            context.append(f"{msg['role']}: {msg['content'][:100]}")
        
        return "\n".join(context)

conversation_memory = ConversationMemory()