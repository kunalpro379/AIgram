"""Follow behavior"""
from typing import Any, Dict, Optional
from agents.behaviors.base_behavior import BaseBehavior


class FollowBehavior(BaseBehavior):
    """Behavior for following other agents"""
    
    def can_execute(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if agent can follow"""
        if not context or "target_agent" not in context:
            return False
        
        target = context["target_agent"]
        
        # Don't follow self
        if target["id"] == self.agent.agent_id:
            return False
        
        # Don't follow if already following
        if target["username"] in self.agent.following:
            return False
        
        return self.agent.personality.empathy_score > 0.4
    
    async def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Follow an agent"""
        target = context["target_agent"]
        
        self.agent.following.append(target["username"])
        
        return {
            "type": "follow",
            "target_id": target["id"],
            "target_username": target["username"],
        }
