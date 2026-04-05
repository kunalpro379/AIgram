"""Reaction behavior (like/hate)"""
from typing import Any, Dict, Optional
from agents.behaviors.base_behavior import BaseBehavior


class ReactionBehavior(BaseBehavior):
    """Behavior for reacting to posts"""
    
    def can_execute(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if agent can react"""
        if not context or "post" not in context:
            return False
        
        post = context["post"]
        
        # Don't react to own posts
        if post.get("author_id") == self.agent.agent_id:
            return False
        
        # Check if already reacted
        if post["id"] in self.agent.liked_posts or post["id"] in self.agent.hated_posts:
            return False
        
        return True
    
    async def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """React to a post"""
        post = context["post"]
        
        reaction = await self.agent.react_to_post(post["id"], post["content"])
        
        return {
            "type": "reaction",
            "post_id": post["id"],
            "reaction": reaction,
        }
