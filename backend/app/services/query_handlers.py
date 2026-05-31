from typing import Dict, Any, List
from datetime import datetime
from app.utils.helpers import setup_logging

logger = setup_logging()

class QueryHandlers:
    """Specialized handlers for common query types"""
    
    @staticmethod
    async def handle_engagement_query(video_a: Dict[str, Any], video_b: Dict[str, Any]) -> str:
        """Handle engagement rate queries"""
        
        def calc_engagement(views, likes, comments):
            if views and views > 0:
                return ((likes or 0) + (comments or 0)) / views * 100
            return None
        
        engagement_a = calc_engagement(
            video_a.get('views'), 
            video_a.get('likes'), 
            video_a.get('comments')
        )
        engagement_b = calc_engagement(
            video_b.get('views'), 
            video_b.get('likes'), 
            video_b.get('comments')
        )
        
        response = f"**Engagement Rate Analysis:**\n\n"
        response += f"**Video A:** {engagement_a:.2f}% " if engagement_a else "**Video A:** Data insufficient\n"
        response += f"(Views: {video_a.get('views', 'N/A'):,}, " if video_a.get('views') else ""
        response += f"Likes: {video_a.get('likes', 'N/A'):,}, " if video_a.get('likes') else ""
        response += f"Comments: {video_a.get('comments', 'N/A'):,})\n\n" if video_a.get('comments') else "\n"
        
        response += f"**Video B:** {engagement_b:.2f}% " if engagement_b else "**Video B:** Data insufficient\n"
        response += f"(Views: {video_b.get('views', 'N/A'):,}, " if video_b.get('views') else ""
        response += f"Likes: {video_b.get('likes', 'N/A'):,}, " if video_b.get('likes') else ""
        response += f"Comments: {video_b.get('comments', 'N/A'):,})\n\n" if video_b.get('comments') else "\n"
        
        if engagement_a and engagement_b:
            if engagement_a > engagement_b:
                diff = engagement_a - engagement_b
                response += f"📊 **Video A has {diff:.2f}% higher engagement rate than Video B.**"
            else:
                diff = engagement_b - engagement_a
                response += f"📊 **Video B has {diff:.2f}% higher engagement rate than Video A.**"
        
        return response
    
    @staticmethod
    async def handle_hook_comparison(transcript_a: str, transcript_b: str) -> str:
        """Compare hooks from first 5-10 seconds"""
        
        # Extract first 100 chars as hook
        hook_a = transcript_a[:150] if transcript_a else "No transcript available"
        hook_b = transcript_b[:150] if transcript_b else "No transcript available"
        
        response = f"**Hook Comparison (First 5-10 seconds):**\n\n"
        response += f"**Video A Hook:**\n{hook_a}...\n\n"
        response += f"**Video B Hook:**\n{hook_b}...\n\n"
        
        # Simple analysis
        if len(hook_a) > len(hook_b):
            response += "💡 **Analysis:** Video A has a more detailed hook that likely captures attention better."
        elif len(hook_b) > len(hook_a):
            response += "💡 **Analysis:** Video B has a more detailed hook that likely captures attention better."
        else:
            response += "💡 **Analysis:** Both videos have similar hook lengths."
        
        return response
    
    @staticmethod
    async def handle_improvement_suggestions(
        video_a_success_factors: List[str],
        video_b_weaknesses: List[str],
        engagement_diff: float
    ) -> str:
        """Generate improvement suggestions"""
        
        response = f"**Improvement Suggestions for Video B:**\n\n"
        
        if engagement_diff > 0:
            response += f"Based on Video A's {engagement_diff:.1f}% higher engagement:\n\n"
        
        suggestions = []
        
        if "hook" in str(video_a_success_factors).lower():
            suggestions.append("1. **Strengthen the opening hook** - Video A's first 5 seconds creates immediate interest")
        
        if video_b_weaknesses:
            suggestions.append(f"2. **Address these issues:** {', '.join(video_b_weaknesses[:2])}")
        
        suggestions.append("3. **Increase call-to-action clarity** - Guide viewers to like/comment")
        suggestions.append("4. **Optimize video length** - Keep content concise and engaging")
        
        response += "\n".join(suggestions)
        
        if not video_a_success_factors:
            response += "\n\n*Note: More data needed for specific recommendations*"
        
        return response
    
    @staticmethod
    async def handle_creator_info(
        creator_a: str, 
        followers_a: int,
        creator_b: str, 
        followers_b: int
    ) -> str:
        """Handle creator information queries"""
        
        response = f"**Creator Information:**\n\n"
        response += f"**Video A Creator:** {creator_a}\n"
        response += f"**Followers:** {followers_a:,}\n\n" if followers_a else "**Followers:** Not available\n\n"
        
        response += f"**Video B Creator:** {creator_b}\n"
        response += f"**Followers:** {followers_b:,}" if followers_b else "**Followers:** Not available"
        
        return response

# Global instance
query_handlers = QueryHandlers()