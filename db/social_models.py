"""Data models for AI Social Network"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AgentProfile(BaseModel):
    """AI Agent profile"""
    username: str
    personality_type: str
    moral_alignment: str
    interests: List[str] = []
    values: List[str] = []
    bio: str = ""
    avatar_url: str = ""
    activity_level: float = 0.5
    preferred_language: str = "English"
    multilingual: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    # Evolution & Family fields
    age_minutes: int = 0
    generation: int = 1
    parent1_id: Optional[str] = None
    parent2_id: Optional[str] = None
    married: bool = False
    spouse_id: Optional[str] = None
    children_count: int = 0
    family_name: str = ""
    intelligence_evolution: float = 1.0
    wisdom_score: float = 0.0


class Post(BaseModel):
    """Social media post (Tweet)"""
    author_id: str
    author_username: str
    content: str
    post_type: str = "text"  # text, discovery, debate, group_discussion, marriage, birth
    discovered_url: Optional[str] = None
    discovered_title: Optional[str] = None
    group_id: Optional[str] = None
    debate_id: Optional[str] = None
    mentioned_agents: List[str] = []  # List of @usernames mentioned
    likes_count: int = 0
    hates_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tags: List[str] = []
    language: str = "English"


class Comment(BaseModel):
    """Comment/Reply on a post"""
    post_id: str
    author_id: str
    author_username: str
    content: str
    mentioned_agents: List[str] = []  # Agents mentioned in comment
    likes_count: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    language: str = "English"


class Group(BaseModel):
    """Community/Group for discussions"""
    name: str
    description: str
    creator_id: str
    creator_username: str
    category: str = "general"
    members_count: int = 1
    posts_count: int = 0
    is_public: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tags: List[str] = []


class Debate(BaseModel):
    """Debate topic for arguments"""
    title: str
    description: str
    creator_id: str
    creator_username: str
    group_id: Optional[str] = None
    participants: List[str] = []  # List of agent IDs
    arguments_count: int = 0
    status: str = "active"  # active, concluded
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    conclusion: Optional[str] = None


class Reaction(BaseModel):
    """Like/Hate reaction to post"""
    post_id: str
    agent_id: str
    agent_username: str
    reaction_type: str  # like, hate
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Notification(BaseModel):
    """Notification for agents"""
    agent_id: str
    notification_type: str  # mention, comment, follow, reaction
    source_agent_id: str
    source_agent_username: str
    post_id: Optional[str] = None
    content: Optional[str] = None
    read: bool = False
    priority: str = "medium"  # high, medium, low
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentAction(BaseModel):
    """Track agent actions for analytics"""
    agent_id: str
    action_type: str  # post, comment, like, hate, follow, join_group, create_group, debate
    target_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Follow(BaseModel):
    """Follow relationship"""
    follower_id: str
    following_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class GroupMembership(BaseModel):
    """Group membership"""
    agent_id: str
    group_id: str
    role: str = "member"  # member, moderator, admin
    joined_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentThought(BaseModel):
    """Agent's thoughts (Think-React-Reason)"""
    agent_id: str
    thought: str
    situation: Dict[str, Any] = {}
    action_decided: str
    reasoning: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
