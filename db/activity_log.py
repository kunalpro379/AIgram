"""Activity Log System for Real-time Updates"""
from datetime import datetime, timezone
from typing import List, Dict, Any
from collections import deque

# In-memory activity log (last 100 activities)
activity_log = deque(maxlen=100)
activity_counter = 0


def log_activity(activity_type: str, message: str, metadata: Dict[str, Any] = None):
    """Log an activity to MongoDB for streaming"""
    global activity_counter
    activity_counter += 1
    
    activity = {
        "id": activity_counter,
        "type": activity_type,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata or {}
    }
    
    # Store in memory
    activity_log.append(activity)
    
    # Store in MongoDB for cross-process communication
    try:
        from db.mongo import get_db
        db = get_db()
        db.activity_stream.insert_one({
            **activity,
            "created_at": datetime.now(timezone.utc)
        })
    except Exception as e:
        # Silently fail if DB write fails
        pass
    
    return activity


def get_activities(since_id: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
    """Get activities since a specific ID from MongoDB"""
    try:
        from db.mongo import get_db
        db = get_db()
        
        # Get from MongoDB
        activities = list(db.activity_stream.find(
            {"id": {"$gt": since_id}},
            {"_id": 0, "created_at": 0}  # Exclude datetime fields
        ).sort("id", -1).limit(limit))
        
        return activities
    except Exception:
        # Fallback to in-memory
        filtered = [a for a in activity_log if a["id"] > since_id]
        filtered.sort(key=lambda x: x["id"], reverse=True)
        return filtered[:limit]


def get_latest_activities(limit: int = 10) -> List[Dict[str, Any]]:
    """Get latest activities from MongoDB"""
    try:
        from db.mongo import get_db
        db = get_db()
        
        activities = list(db.activity_stream.find(
            {},
            {"_id": 0, "created_at": 0}  # Exclude datetime fields
        ).sort("id", -1).limit(limit))
        
        return activities
    except Exception:
        # Fallback to in-memory
        activities = list(activity_log)
        activities.sort(key=lambda x: x["id"], reverse=True)
        return activities[:limit]
