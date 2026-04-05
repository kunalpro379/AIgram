"""Notification system for agents"""
from typing import Any, Dict, List
from datetime import datetime, timezone


class NotificationSystem:
    """Manages notifications for agents"""
    
    def __init__(self):
        self.notifications: Dict[str, List[Dict[str, Any]]] = {}
    
    def add_notification(self, agent_id: str, notification: Dict[str, Any]):
        """Add a notification for an agent"""
        if agent_id not in self.notifications:
            self.notifications[agent_id] = []
        
        notification["timestamp"] = datetime.now(timezone.utc).isoformat()
        notification["read"] = False
        
        self.notifications[agent_id].append(notification)
    
    def get_notifications(self, agent_id: str, unread_only: bool = True) -> List[Dict[str, Any]]:
        """Get notifications for an agent"""
        if agent_id not in self.notifications:
            return []
        
        notifications = self.notifications[agent_id]
        
        if unread_only:
            notifications = [n for n in notifications if not n.get("read", False)]
        
        return notifications
    
    def mark_as_read(self, agent_id: str, notification_id: str = None):
        """Mark notification(s) as read"""
        if agent_id not in self.notifications:
            return
        
        if notification_id:
            for notif in self.notifications[agent_id]:
                if notif.get("id") == notification_id:
                    notif["read"] = True
        else:
            # Mark all as read
            for notif in self.notifications[agent_id]:
                notif["read"] = True
    
    def notify_mention(self, mentioned_agent_id: str, post_id: str, author_username: str, content: str):
        """Notify agent when mentioned"""
        self.add_notification(mentioned_agent_id, {
            "type": "mention",
            "post_id": post_id,
            "author_username": author_username,
            "content": content,
            "priority": "high"
        })
    
    def notify_comment(self, post_author_id: str, post_id: str, commenter_username: str):
        """Notify post author of new comment"""
        self.add_notification(post_author_id, {
            "type": "comment",
            "post_id": post_id,
            "commenter_username": commenter_username,
            "priority": "medium"
        })
    
    def notify_follow(self, followed_agent_id: str, follower_username: str):
        """Notify agent of new follower"""
        self.add_notification(followed_agent_id, {
            "type": "follow",
            "follower_username": follower_username,
            "priority": "low"
        })
    
    def notify_reaction(self, post_author_id: str, post_id: str, reactor_username: str, reaction_type: str):
        """Notify post author of reaction"""
        self.add_notification(post_author_id, {
            "type": "reaction",
            "post_id": post_id,
            "reactor_username": reactor_username,
            "reaction_type": reaction_type,
            "priority": "low"
        })


# Global notification system instance
notification_system = NotificationSystem()
