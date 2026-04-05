"""Debate behavior"""
import random
from typing import Any, Dict, Optional
from agents.behaviors.base_behavior import BaseBehavior


class DebateBehavior(BaseBehavior):
    """Behavior for starting debates"""
    
    def can_execute(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if agent can start debate"""
        return self.agent.personality.controversy_tolerance > 0.6
    
    async def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Start a debate"""
        topic = random.choice(self.agent.personality.interests)
        
        return {
            "type": "debate",
            "title": f"Debate: The Future of {topic.title()}",
            "description": f"Let's discuss the implications and future of {topic}",
        }
