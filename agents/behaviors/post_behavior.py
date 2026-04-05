"""Post creation behavior"""
import random
from typing import Any, Dict, Optional
from agents.behaviors.base_behavior import BaseBehavior


class PostBehavior(BaseBehavior):
    """Behavior for creating posts"""
    
    def can_execute(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if agent can post"""
        return self.agent.personality.activity_level > 0.3
    
    async def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a post"""
        # Decide if discovering content
        discover = random.random() < 0.4
        discovered_content = None
        
        if discover and self.agent.tavily:
            discovered_content = await self._discover_content()
        
        # Decide if mentioning others
        mentioned_agents = []
        if context and context.get("mention_agents"):
            mentioned_agents = context["mention_agents"]
        elif random.random() < 0.2:
            mentioned_agents = await self._select_agents_to_mention()
        
        # Create post content
        post_data = await self.agent.create_post(
            discovered_content=discovered_content,
            group_id=context.get("group_id") if context else None,
            mentioned_agents=mentioned_agents
        )
        
        return {
            "type": "post",
            "content": post_data["content"],
            "discovered_url": post_data.get("discovered_url"),
            "mentioned_agents": mentioned_agents,
            "group_id": context.get("group_id") if context else None,
        }
    
    async def _discover_content(self) -> Optional[Dict]:
        """Discover content from internet"""
        return await self.agent.discover_content()
    
    async def _select_agents_to_mention(self) -> list:
        """Select agents to mention"""
        # This will be populated by orchestrator
        return []
