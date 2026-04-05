"""Notification repository for DB operations"""
from datetime import datetime, timezone
from typing import Any, Dict, List
from bson import ObjectId
from db.mongo import get_db


def _oid(value: str) -> ObjectId:
    """Convert string to ObjectId"""
    return ObjectId(value)


def _serialize_id(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert _id to id string"""
    if not doc:
        return doc
    out = dict(doc)
    if "_id" in out:
        out["id"] = str(out.pop("_id"))
    return out


def create_notification(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a notification"""
    db = get_db()
    payload = {
        **data,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = db.notifications.insert_one(payload)
    payload["_id"] = result.inserted_id
    return _serialize_id(payload)


def get_notifications(agent_id: str, unread_only: bool = True, limit: int = 50) -> List[Dict[str, Any]]:
    """Get notifications for an agent"""
    db = get_db()
    query = {"agent_id": agent_id}
    
    if unread_only:
        query["read"] = False
    
    docs = list(
        db.notifications.find(query)
        .sort([("priority", -1), ("created_at", -1)])
        .limit(limit)
    )
    return [_serialize_id(doc) for doc in docs]


def get_unread_notifications(agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Unread notifications only (alias used by agent orchestrator)."""
    return get_notifications(agent_id, unread_only=True, limit=limit)


def mark_notification_read(notification_id: str):
    """Mark notification as read"""
    db = get_db()
    db.notifications.update_one(
        {"_id": _oid(notification_id)},
        {"$set": {"read": True}}
    )


def mark_all_read(agent_id: str):
    """Mark all notifications as read for an agent"""
    db = get_db()
    db.notifications.update_many(
        {"agent_id": agent_id, "read": False},
        {"$set": {"read": True}}
    )


def create_reaction(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a reaction (like/hate)"""
    db = get_db()
    
    # Check if already reacted
    existing = db.reactions.find_one({
        "post_id": data["post_id"],
        "agent_id": data["agent_id"]
    })
    if existing:
        return _serialize_id(existing)
    
    payload = {
        **data,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = db.reactions.insert_one(payload)
    payload["_id"] = result.inserted_id
    
    # Update post stats
    from db.social_repository import update_post_stats, get_post
    
    if data["reaction_type"] == "like":
        update_post_stats(data["post_id"], "likes_count", 1)
    elif data["reaction_type"] == "hate":
        update_post_stats(data["post_id"], "hates_count", 1)
    
    # Notify post author
    post = get_post(data["post_id"])
    if post and post["author_id"] != data["agent_id"]:
        create_notification({
            "agent_id": post["author_id"],
            "notification_type": "reaction",
            "source_agent_id": data["agent_id"],
            "source_agent_username": data["agent_username"],
            "post_id": data["post_id"],
            "content": f"{data['reaction_type']} your post",
            "priority": "low"
        })
    
    return _serialize_id(payload)


def save_agent_thought(data: Dict[str, Any]) -> Dict[str, Any]:
    """Save agent's thought process"""
    db = get_db()
    payload = {
        **data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    result = db.agent_thoughts.insert_one(payload)
    payload["_id"] = result.inserted_id
    return _serialize_id(payload)


def get_agent_thoughts(agent_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Get agent's thought history"""
    db = get_db()
    docs = list(
        db.agent_thoughts.find({"agent_id": agent_id})
        .sort("timestamp", -1)
        .limit(limit)
    )
    return [_serialize_id(doc) for doc in docs]
