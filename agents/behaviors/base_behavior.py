"""Base behavior class for agent actions"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseBehavior(ABC):
    """Abstract base class for agent behaviors"""
    
    def __init__(self, agent):
        self.agent = agent
    
    @abstractmethod
    async def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the behavior"""
        pass
    
    @abstractmethod
    def can_execute(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if behavior can be executed"""
        pass
