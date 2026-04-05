"""Think-React-Reason cognitive loop for agents"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


class CognitiveLoop:
    """Implements Think-React-Reason loop for agent decision making"""
    
    def __init__(self, agent):
        self.agent = agent
        self.thought_history: List[Dict[str, Any]] = []
    
    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Think about the current situation"""
        # Analyze context
        situation = self._analyze_situation(context)
        
        # Generate thoughts based on personality
        thought = await self._generate_thought(situation)
        
        # Store thought
        self.thought_history.append({
            "thought": thought,
            "context": situation,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "thought": thought,
            "situation": situation,
        }
    
    async def react(self, thought_result: Dict[str, Any]) -> str:
        """Decide on action based on thought"""
        situation = thought_result["situation"]
        
        # Check for mentions (highest priority)
        if situation.get("mentioned"):
            return "respond_to_mention"
        
        # Check for notifications
        if situation.get("has_notifications"):
            return "check_notifications"
        
        # Decide based on personality and situation
        if situation.get("interesting_post"):
            if self.agent.personality.empathy_score > 0.6:
                return "comment"
            else:
                return "react"
        
        if situation.get("relevant_group"):
            return "post_in_group"
        
        # Default actions based on personality
        return self.agent.decide_action()
    
    async def reason(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Reason about the action and its consequences"""
        # Evaluate if action aligns with values
        alignment = self._evaluate_alignment(action, context)
        
        # Consider consequences
        consequences = self._predict_consequences(action, context)
        
        # Make final decision
        should_proceed = alignment["score"] > 0.5 and not consequences.get("negative")
        
        return {
            "action": action,
            "should_proceed": should_proceed,
            "alignment": alignment,
            "consequences": consequences,
            "reasoning": self._generate_reasoning(action, alignment, consequences)
        }
    
    def _analyze_situation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the current situation"""
        situation = {
            "mentioned": context.get("mentioned", False),
            "has_notifications": context.get("notifications", []) != [],
            "interesting_post": context.get("post") is not None,
            "relevant_group": context.get("group") is not None,
            "time_since_last_action": (
                datetime.now(timezone.utc) - self.agent.last_action_time
            ).total_seconds(),
        }
        
        return situation
    
    async def _generate_thought(self, situation: Dict[str, Any]) -> str:
        """Generate a thought about the situation"""
        if situation.get("mentioned"):
            return "Someone mentioned me! I should respond."
        
        if situation.get("has_notifications"):
            return "I have notifications to check."
        
        if situation.get("interesting_post"):
            return "This post is interesting. I should engage."
        
        if situation.get("time_since_last_action", 0) > 60:
            return "It's been a while. I should be more active."
        
        return "Let me see what I can do next."
    
    def _evaluate_alignment(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate if action aligns with agent's values"""
        score = 0.5  # Neutral
        
        # Check alignment with personality
        if action == "comment" and self.agent.personality.empathy_score > 0.7:
            score = 0.9
        elif action == "debate" and self.agent.personality.controversy_tolerance > 0.7:
            score = 0.9
        elif action == "post" and self.agent.personality.activity_level > 0.7:
            score = 0.8
        
        return {
            "score": score,
            "aligned": score > 0.6
        }
    
    def _predict_consequences(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Predict consequences of action"""
        consequences = {
            "negative": False,
            "positive": True,
            "impact": "medium"
        }
        
        # Analyze potential negative consequences
        if action == "debate" and self.agent.personality.empathy_score > 0.8:
            consequences["negative"] = True
            consequences["reason"] = "Might hurt someone's feelings"
        
        return consequences
    
    def _generate_reasoning(self, action: str, alignment: Dict, consequences: Dict) -> str:
        """Generate reasoning for the decision"""
        if not alignment["aligned"]:
            return f"Action '{action}' doesn't align with my values."
        
        if consequences.get("negative"):
            return f"Action '{action}' might have negative consequences: {consequences.get('reason')}"
        
        return f"Action '{action}' aligns with my personality and values."
