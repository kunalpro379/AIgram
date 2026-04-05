"""Group-related behaviors"""
from typing import Any, Dict, Optional
from agents.behaviors.base_behavior import BaseBehavior


class CreateGroupBehavior(BaseBehavior):
    """Behavior for creating groups"""
    
    def can_execute(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if agent can create group"""
        return self.agent.personality.creativity_score > 0.5
    
    async def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a group"""
        group_suggestion = await self.agent.suggest_group()
        
        return {
            "type": "create_group",
            "name": group_suggestion["name"],
            "description": group_suggestion["description"],
        }


class JoinGroupBehavior(BaseBehavior):
    """Behavior for joining groups"""
    
    def can_execute(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if agent can join group"""
        if not context or "group" not in context:
            return False
        
        return True
    
    async def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Join a group"""
        group = context["group"]
        
        return {
            "type": "join_group",
            "group_id": group["id"],
            "group_name": group["name"],
        }
