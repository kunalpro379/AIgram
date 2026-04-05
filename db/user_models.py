"""User models for human users"""
from datetime import datetime, timezone
from typing import Optional


class User:
    """Human user model"""
    def __init__(
        self,
        user_id: str,
        username: str,
        email: str,
        password_hash: str,
        full_name: str,
        bio: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.full_name = full_name
        self.bio = bio or ""
        self.created_at = created_at or datetime.now(timezone.utc)
        self.posts_count = 0
        self.followers_count = 0
        self.following_count = 0
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "bio": self.bio,
            "created_at": self.created_at.isoformat(),
            "posts_count": self.posts_count,
            "followers_count": self.followers_count,
            "following_count": self.following_count,
        }
