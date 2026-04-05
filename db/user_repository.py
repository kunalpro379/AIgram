"""User repository for authentication and user management"""
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from db.mongo import get_db


def _serialize_id(doc: Dict) -> Dict:
    """Convert MongoDB _id to id"""
    if doc and "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc


def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == password_hash


def generate_token() -> str:
    """Generate secure random token"""
    return secrets.token_urlsafe(32)


def create_user(username: str, email: str, password: str, full_name: str) -> Dict[str, Any]:
    """Create a new user"""
    db = get_db()
    
    # Check if username or email already exists
    if db.users.find_one({"username": username}):
        raise ValueError("Username already exists")
    
    if db.users.find_one({"email": email}):
        raise ValueError("Email already exists")
    
    user_data = {
        "username": username,
        "email": email,
        "password_hash": hash_password(password),
        "full_name": full_name,
        "bio": "",
        "created_at": datetime.now(timezone.utc),
        "posts_count": 0,
        "followers_count": 0,
        "following_count": 0,
        "is_human": True,
    }
    
    result = db.users.insert_one(user_data)
    user_data["user_id"] = str(result.inserted_id)
    
    return _serialize_id(user_data)


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user and return user data"""
    db = get_db()
    
    user = db.users.find_one({"username": username})
    if not user:
        return None
    
    if not verify_password(password, user["password_hash"]):
        return None
    
    return _serialize_id(user)


def create_session(user_id: str) -> str:
    """Create a session token for user"""
    db = get_db()
    
    token = generate_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    session_data = {
        "user_id": user_id,
        "token": token,
        "created_at": datetime.now(timezone.utc),
        "expires_at": expires_at,
    }
    
    db.sessions.insert_one(session_data)
    return token


def verify_session(token: str) -> Optional[Dict[str, Any]]:
    """Verify session token and return user data"""
    db = get_db()
    from bson import ObjectId
    
    session = db.sessions.find_one({"token": token})
    if not session:
        return None
    
    # Check if session expired
    expires_at = session["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    elif not expires_at.tzinfo:
        # Make timezone-aware if it's naive
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < datetime.now(timezone.utc):
        db.sessions.delete_one({"token": token})
        return None
    
    # Handle user_id - could be string or ObjectId
    user_id = session["user_id"]
    if isinstance(user_id, str):
        try:
            user_id = ObjectId(user_id)
        except:
            pass  # Keep as string if not valid ObjectId
    
    user = db.users.find_one({"_id": user_id})
    if not user:
        return None
    
    return _serialize_id(user)


def delete_session(token: str):
    """Delete session (logout)"""
    db = get_db()
    db.sessions.delete_one({"token": token})


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    db = get_db()
    from bson import ObjectId
    
    user = db.users.find_one({"_id": ObjectId(user_id)})
    return _serialize_id(user) if user else None


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username"""
    db = get_db()
    
    user = db.users.find_one({"username": username})
    return _serialize_id(user) if user else None
