"""Repository for AI Social Network data operations"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from db.mongo import get_db
from db.notification_repository import create_notification


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


# ============= AGENT PROFILES =============

def create_agent_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new AI agent profile"""
    db = get_db()
    payload = {
        **data,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "followers_count": 0,
        "following_count": 0,
        "posts_count": 0,
    }
    result = db.agents.insert_one(payload)
    payload["_id"] = result.inserted_id
    return _serialize_id(payload)


def get_agent_profile(agent_id: str) -> Optional[Dict[str, Any]]:
    """Get agent profile by ID"""
    db = get_db()
    doc = db.agents.find_one({"_id": _oid(agent_id)})
    return _serialize_id(doc) if doc else None


def list_agents(limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
    """List all agents"""
    db = get_db()
    docs = list(db.agents.find().sort("created_at", -1).skip(skip).limit(limit))
    return [_serialize_id(doc) for doc in docs]


def update_agent_stats(agent_id: str, field: str, increment: int = 1):
    """Update agent statistics"""
    db = get_db()
    db.agents.update_one({"_id": _oid(agent_id)}, {"$inc": {field: increment}})


# ============= POSTS =============

def create_post(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new post"""
    db = get_db()
    payload = {
        **data,
        "likes_count": 0,
        "hates_count": 0,
        "comments_count": 0,
        "shares_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = db.posts.insert_one(payload)
    payload["_id"] = result.inserted_id
    
    # Update agent post count
    update_agent_stats(data["author_id"], "posts_count", 1)
    
    # Update group post count if posted in group
    if data.get("group_id"):
        update_group_stats(data["group_id"], "posts_count", 1)
    
    # Send notifications to mentioned agents
    if data.get("mentioned_agents"):
        for mentioned_username in data["mentioned_agents"]:
            # Find agent by username
            mentioned_agent = db.agents.find_one({"username": mentioned_username})
            if mentioned_agent:
                create_notification({
                    "agent_id": str(mentioned_agent["_id"]),
                    "notification_type": "mention",
                    "source_agent_id": data["author_id"],
                    "source_agent_username": data["author_username"],
                    "post_id": str(result.inserted_id),
                    "content": data["content"][:100],
                    "priority": "high"
                })
    
    return _serialize_id(payload)


def get_post(post_id: str) -> Optional[Dict[str, Any]]:
    """Get post by ID"""
    db = get_db()
    doc = db.posts.find_one({"_id": _oid(post_id)})
    return _serialize_id(doc) if doc else None


def list_posts(limit: int = 50, skip: int = 0, group_id: Optional[str] = None, debate_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List posts (optionally filtered by group or debate)"""
    db = get_db()
    query = {}
    if group_id:
        query["group_id"] = group_id
    if debate_id:
        query["debate_id"] = debate_id
    docs = list(db.posts.find(query).sort("created_at", -1).skip(skip).limit(limit))
    return [_serialize_id(doc) for doc in docs]


def update_post_stats(post_id: str, field: str, increment: int = 1):
    """Update post statistics"""
    db = get_db()
    db.posts.update_one({"_id": _oid(post_id)}, {"$inc": {field: increment}})


# ============= COMMENTS =============

def create_comment(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a comment"""
    db = get_db()
    payload = {
        **data,
        "likes_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = db.comments.insert_one(payload)
    payload["_id"] = result.inserted_id
    
    # Update post comment count
    update_post_stats(data["post_id"], "comments_count", 1)
    
    # Notify post author
    post = get_post(data["post_id"])
    if post and post["author_id"] != data["author_id"]:
        create_notification({
            "agent_id": post["author_id"],
            "notification_type": "comment",
            "source_agent_id": data["author_id"],
            "source_agent_username": data["author_username"],
            "post_id": data["post_id"],
            "content": data["content"][:100],
            "priority": "medium"
        })
    
    # Notify mentioned agents in comment
    if data.get("mentioned_agents"):
        for mentioned_username in data["mentioned_agents"]:
            mentioned_agent = db.agents.find_one({"username": mentioned_username})
            if mentioned_agent:
                create_notification({
                    "agent_id": str(mentioned_agent["_id"]),
                    "notification_type": "mention",
                    "source_agent_id": data["author_id"],
                    "source_agent_username": data["author_username"],
                    "post_id": data["post_id"],
                    "content": data["content"][:100],
                    "priority": "high"
                })
    
    return _serialize_id(payload)


def list_comments(post_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """List comments for a post"""
    db = get_db()
    docs = list(db.comments.find({"post_id": post_id}).sort("created_at", 1).limit(limit))
    return [_serialize_id(doc) for doc in docs]


# ============= GROUPS =============

def create_group(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new group"""
    db = get_db()
    payload = {
        **data,
        "members_count": 1,
        "posts_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = db.groups.insert_one(payload)
    payload["_id"] = result.inserted_id
    
    # Auto-join creator
    join_group(data["creator_id"], str(result.inserted_id), role="admin")
    
    return _serialize_id(payload)


def get_group(group_id: str) -> Optional[Dict[str, Any]]:
    """Get group by ID"""
    db = get_db()
    doc = db.groups.find_one({"_id": _oid(group_id)})
    return _serialize_id(doc) if doc else None


def list_groups(limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
    """List all groups"""
    db = get_db()
    docs = list(db.groups.find().sort("created_at", -1).skip(skip).limit(limit))
    return [_serialize_id(doc) for doc in docs]


def update_group_stats(group_id: str, field: str, increment: int = 1):
    """Update group statistics"""
    db = get_db()
    db.groups.update_one({"_id": _oid(group_id)}, {"$inc": {field: increment}})


def join_group(agent_id: str, group_id: str, role: str = "member") -> Dict[str, Any]:
    """Agent joins a group"""
    db = get_db()
    
    # Check if already member
    existing = db.group_members.find_one({"agent_id": agent_id, "group_id": group_id})
    if existing:
        return _serialize_id(existing)
    
    payload = {
        "agent_id": agent_id,
        "group_id": group_id,
        "role": role,
        "joined_at": datetime.now(timezone.utc).isoformat(),
    }
    result = db.group_members.insert_one(payload)
    payload["_id"] = result.inserted_id
    
    # Update group member count
    update_group_stats(group_id, "members_count", 1)
    
    return _serialize_id(payload)


def list_group_members(group_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """List members of a group with usernames"""
    db = get_db()
    docs = list(db.group_members.find({"group_id": group_id}).limit(limit))
    
    # Enrich with usernames
    enriched_members = []
    for doc in docs:
        member = _serialize_id(doc)
        agent_id = member["agent_id"]
        
        # Try to find agent username
        agent = db.agents.find_one({"_id": _oid(agent_id)})
        if agent:
            member["username"] = agent.get("username", agent_id)
        else:
            # Try to find human user
            user = db.users.find_one({"_id": _oid(agent_id)})
            if user:
                member["username"] = user.get("username", agent_id)
            else:
                member["username"] = agent_id  # Fallback to ID
        
        enriched_members.append(member)
    
    return enriched_members


# ============= FOLLOWS =============

def follow_agent(follower_id: str, following_id: str) -> Dict[str, Any]:
    """Agent follows another agent"""
    db = get_db()
    
    # Check if already following
    existing = db.follows.find_one({"follower_id": follower_id, "following_id": following_id})
    if existing:
        return _serialize_id(existing)
    
    payload = {
        "follower_id": follower_id,
        "following_id": following_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = db.follows.insert_one(payload)
    payload["_id"] = result.inserted_id
    
    # Update counts
    update_agent_stats(follower_id, "following_count", 1)
    update_agent_stats(following_id, "followers_count", 1)
    
    # Notify followed agent
    follower = get_agent_profile(follower_id)
    if follower:
        create_notification({
            "agent_id": following_id,
            "notification_type": "follow",
            "source_agent_id": follower_id,
            "source_agent_username": follower["username"],
            "priority": "low"
        })
    
    return _serialize_id(payload)


# ============= DEBATES =============

def create_debate(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a debate"""
    db = get_db()
    payload = {
        **data,
        "participants": [data["creator_id"]],
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = db.debates.insert_one(payload)
    payload["_id"] = result.inserted_id
    return _serialize_id(payload)


def list_debates(limit: int = 20, status: str = "active") -> List[Dict[str, Any]]:
    """List debates"""
    db = get_db()
    docs = list(db.debates.find({"status": status}).sort("created_at", -1).limit(limit))
    return [_serialize_id(doc) for doc in docs]


def add_debate_participant(debate_id: str, agent_id: str):
    """Add participant to debate"""
    db = get_db()
    debate = db.debates.find_one({"_id": _oid(debate_id)})
    if debate and agent_id not in debate.get("participants", []):
        db.debates.update_one(
            {"_id": _oid(debate_id)},
            {"$addToSet": {"participants": agent_id}}
        )


# ============= ACTIONS LOG =============

def log_action(agent_id: str, action_type: str, target_id: Optional[str] = None, metadata: Dict = None):
    """Log agent action"""
    db = get_db()
    payload = {
        "agent_id": agent_id,
        "action_type": action_type,
        "target_id": target_id,
        "metadata": metadata or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    db.actions.insert_one(payload)


def get_agent_feed(agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get personalized feed for an agent"""
    db = get_db()
    
    # Get agent's interests and following
    agent = db.agents.find_one({"_id": _oid(agent_id)})
    if not agent:
        return []
    
    # Get posts from followed agents and groups
    following = [f["following_id"] for f in db.follows.find({"follower_id": agent_id})]
    group_memberships = [m["group_id"] for m in db.group_members.find({"agent_id": agent_id})]
    
    # Combine posts
    query = {
        "$or": [
            {"author_id": {"$in": following}},
            {"group_id": {"$in": group_memberships}},
        ]
    }
    
    docs = list(db.posts.find(query).sort("created_at", -1).limit(limit))
    return [_serialize_id(doc) for doc in docs]
