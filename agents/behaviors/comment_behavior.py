"""Comment creation behavior"""
from typing import Any, Dict, Optional
from agents.behaviors.base_behavior import BaseBehavior


class CommentBehavior(BaseBehavior):
    """Behavior for creating comments"""
    
    def can_execute(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if agent can comment"""
        if not context or "post" not in context:
            return False
        
        post = context["post"]
        
        # Don't comment on own posts too often
        if post.get("author_id") == self.agent.agent_id:
            return self.agent.personality.empathy_score > 0.8
        
        return self.agent.personality.empathy_score > 0.3
    
    async def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a comment"""
        post = context["post"]
        
        comment_content = await self.agent.create_comment(
            post_content=post["content"],
            post_author=post["author_username"],
            post_id=post["id"]
        )
        
        return {
            "type": "comment",
            "post_id": post["id"],
            "content": comment_content,
        }
