"""FastAPI server for AI Social Network"""
from pathlib import Path
from typing import Any, Dict, List, Optional
import asyncio
import re
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from db.social_repository import (
    list_agents, get_agent_profile, list_posts, get_post,
    list_comments, list_groups, get_group, list_group_members,
    create_post, create_comment, create_group, join_group,
    follow_agent, list_debates, get_agent_feed
)
from db.user_repository import (
    create_user, authenticate_user, create_session, verify_session,
    delete_session, get_user_by_username
)
from db.activity_log import get_activities, get_latest_activities
from agents.orchestrator import AgentOrchestrator
from agents.mcp_tools import execute_mcp_tool


app = FastAPI(title="AI Social Network API", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator
orchestrator: Optional[AgentOrchestrator] = None

# WebSocket connections for activity streaming
active_connections: List[WebSocket] = []
active_connections: List[WebSocket] = []


# ============= REQUEST MODELS =============

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str


class LoginRequest(BaseModel):
    username: str
    password: str


class CreatePostRequest(BaseModel):
    content: str
    tags: List[str] = []
    group_id: Optional[str] = None
    debate_id: Optional[str] = None


class CreateCommentRequest(BaseModel):
    agent_id: str
    post_id: str
    content: str


class CreateGroupRequest(BaseModel):
    agent_id: str
    name: str
    description: str
    category: str = "general"


class JoinGroupRequest(BaseModel):
    group_id: str


class FollowRequest(BaseModel):
    follower_id: str
    following_id: str


class MCPToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]


_MENTION_PATTERN = re.compile(r"@([A-Za-z0-9_]+)")


def _usernames_mentioned_in_text(text: str) -> List[str]:
    """Extract @handles from post body for agent notifications (order preserved, unique)."""
    return list(dict.fromkeys(_MENTION_PATTERN.findall(text or "")))


# ============= HEALTH & INFO =============

@app.get("/")
def home() -> Dict[str, Any]:
    return {
        "name": "AI Social Network",
        "version": "2.0.0",
        "description": "Autonomous AI agents interacting on social media",
        "status": "running" if orchestrator and orchestrator.running else "stopped"
    }


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "healthy", "orchestrator_running": orchestrator.running if orchestrator else False}


# ============= AUTHENTICATION =============

@app.post("/api/auth/signup")
def signup(request: SignupRequest) -> Dict[str, Any]:
    """Create a new user account"""
    try:
        user = create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        
        # Create session token
        token = create_session(user["id"])
        
        # Remove sensitive data
        user.pop("password_hash", None)
        
        return {
            "ok": True,
            "message": "Account created successfully",
            "user": user,
            "token": token
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/login")
def login(request: LoginRequest) -> Dict[str, Any]:
    """Login user"""
    try:
        user = authenticate_user(request.username, request.password)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Create session token
        token = create_session(user["id"])
        
        # Remove sensitive data
        user.pop("password_hash", None)
        
        return {
            "ok": True,
            "message": "Login successful",
            "user": user,
            "token": token
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/logout")
def logout(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Logout user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    delete_session(token)
    
    return {"ok": True, "message": "Logged out successfully"}


@app.get("/api/auth/me")
def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Get current user from token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    user = verify_session(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Remove sensitive data
    user.pop("password_hash", None)
    
    return {"ok": True, "user": user}


# ============= ORCHESTRATOR CONTROL =============

@app.post("/api/orchestrator/start")
async def start_orchestrator(background_tasks: BackgroundTasks, agent_count: int = 20) -> Dict[str, Any]:
    """Start the agent orchestrator"""
    # Update status in DB (agents server will detect and start)
    from db.mongo import get_db
    db = get_db()
    
    # Check current status
    status_doc = db.system_status.find_one({"key": "orchestrator"})
    if status_doc and status_doc.get("running", False):
        return {"ok": False, "message": "Orchestrator already running"}
    
    # Update to running
    db.system_status.update_one(
        {"key": "orchestrator"},
        {"$set": {
            "running": True,
            "agent_count": agent_count,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    return {"ok": True, "message": f"Orchestrator start command sent"}


@app.post("/api/orchestrator/stop")
def stop_orchestrator() -> Dict[str, Any]:
    """Stop the agent orchestrator"""
    # Update status in DB (agents server will detect and stop)
    from db.mongo import get_db
    db = get_db()
    
    # Check current status
    status_doc = db.system_status.find_one({"key": "orchestrator"})
    if not status_doc or not status_doc.get("running", False):
        return {"ok": False, "message": "Orchestrator not running"}
    
    # Update to stopped
    db.system_status.update_one(
        {"key": "orchestrator"},
        {"$set": {
            "running": False,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    return {"ok": True, "message": "Orchestrator stopped"}


@app.get("/api/orchestrator/stats")
def get_orchestrator_stats() -> Dict[str, Any]:
    """Get orchestrator statistics"""
    if not orchestrator:
        # Check DB status
        from db.mongo import get_db
        db = get_db()
        status_doc = db.system_status.find_one({"key": "orchestrator"})
        
        return {
            "ok": True, 
            "stats": {
                "running": status_doc.get("running", False) if status_doc else False,
                "total_agents": 0
            }
        }
    
    return {"ok": True, "stats": orchestrator.get_stats()}


@app.post("/api/orchestrator/add-agent")
async def add_agent() -> Dict[str, Any]:
    """Add a new agent dynamically"""
    if not orchestrator:
        return {"ok": False, "message": "Orchestrator not initialized"}
    
    result = await orchestrator.add_agent()
    return {"ok": True, "message": result}


# ============= ACTIVITY STREAM =============

@app.get("/api/activity/stream")
def get_activity_stream(since: int = 0, limit: int = 10) -> Dict[str, Any]:
    """Get activity stream updates"""
    try:
        activities = get_activities(since_id=since, limit=limit)
        return {"ok": True, "activities": activities, "count": len(activities)}
    except Exception as e:
        return {"ok": False, "error": str(e), "activities": []}


@app.get("/api/activity/latest")
def get_latest_activity(limit: int = 10) -> Dict[str, Any]:
    """Get latest activities"""
    try:
        activities = get_latest_activities(limit=limit)
        return {"ok": True, "activities": activities, "count": len(activities)}
    except Exception as e:
        return {"ok": False, "error": str(e), "activities": []}


@app.get("/api/activity/test")
def test_activity() -> Dict[str, Any]:
    """Test activity logging"""
    from db.activity_log import log_activity, activity_log, activity_counter
    
    # Log a test activity
    log_activity("test", "Test activity created")
    
    return {
        "ok": True,
        "total_activities": len(activity_log),
        "activity_counter": activity_counter,
        "latest_activities": list(activity_log)[-5:] if activity_log else []
    }


# ============= WEBSOCKET FOR ACTIVITY STREAMING =============
# ============= WEBSOCKET FOR ACTIVITY STREAMING =============

@app.websocket("/ws/activity")
async def activity_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time activity streaming"""
    await websocket.accept()
    active_connections.append(websocket)
    
    print(f"[WEBSOCKET] Client connected. Total connections: {len(active_connections)}")
    
    last_id = 0
    
    try:
        while True:
            # Check for new activities from MongoDB
            activities = get_activities(since_id=last_id, limit=5)
            
            # Send new activities to client
            for activity in reversed(activities):  # Send oldest first
                if activity["id"] > last_id:
                    await websocket.send_json(activity)
                    last_id = activity["id"]
            
            # Wait before checking again
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        print(f"[WEBSOCKET] Client disconnected")
    except Exception as e:
        print(f"[WEBSOCKET] Error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
        print(f"[WEBSOCKET] Total connections: {len(active_connections)}")


# ============= CONFIG / SETTINGS =============

class UpdateApiKeyRequest(BaseModel):
    key: str
    value: str


@app.post("/api/config/api-key")
def update_api_key(request: UpdateApiKeyRequest) -> Dict[str, Any]:
    """Update API key in database"""
    try:
        from db.mongo import get_db
        db = get_db()
        
        # Validate key name
        allowed_keys = ["GROQ_API_KEY", "TAVILY_API_KEY"]
        if request.key not in allowed_keys:
            return {"ok": False, "detail": f"Invalid key name. Allowed: {allowed_keys}"}
        
        # Validate value
        if not request.value or len(request.value) < 10:
            return {"ok": False, "detail": "API key too short"}
        
        # Update in database
        result = db.config.update_one(
            {"key": request.key},
            {"$set": {
                "value": request.value,
                "description": f"{request.key.replace('_', ' ').title()}",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        # Clear cache in factory
        from LLMs.factory import _api_key_cache
        if request.key in _api_key_cache:
            del _api_key_cache[request.key]
        
        return {
            "ok": True,
            "message": f"{request.key} updated successfully",
            "modified": result.modified_count > 0,
            "upserted": result.upserted_id is not None
        }
    except Exception as e:
        return {"ok": False, "detail": str(e)}


# ============= AGENTS =============

@app.get("/api/agents")
def get_agents(limit: int = 50, skip: int = 0) -> Dict[str, Any]:
    """Get all AI agents"""
    try:
        agents = list_agents(limit=limit, skip=skip)
        return {"ok": True, "agents": agents, "count": len(agents)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/{agent_id}")
def get_agent(agent_id: str) -> Dict[str, Any]:
    """Get agent profile"""
    try:
        agent = get_agent_profile(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {"ok": True, "agent": agent}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/{agent_id}/feed")
def get_agent_feed_endpoint(agent_id: str, limit: int = 50) -> Dict[str, Any]:
    """Get personalized feed for an agent"""
    try:
        feed = get_agent_feed(agent_id, limit=limit)
        return {"ok": True, "feed": feed, "count": len(feed)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= POSTS =============

@app.get("/api/posts")
def get_posts(limit: int = 50, skip: int = 0, group_id: Optional[str] = None, debate_id: Optional[str] = None) -> Dict[str, Any]:
    """Get posts"""
    try:
        posts = list_posts(limit=limit, skip=skip, group_id=group_id, debate_id=debate_id)
        return {"ok": True, "posts": posts, "count": len(posts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/posts/{post_id}")
def get_post_endpoint(post_id: str) -> Dict[str, Any]:
    """Get a specific post"""
    try:
        post = get_post(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return {"ok": True, "post": post}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/posts")
def create_post_endpoint(request: CreatePostRequest, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Create a post (requires authentication)"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    user = verify_session(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    try:
        post_data = {
            "author_id": user["id"],
            "author_username": user["username"],
            "content": request.content,
            "post_type": "text",
            "tags": request.tags,
            "group_id": request.group_id,
            "debate_id": request.debate_id,
            "is_human": True,
            "mentioned_agents": _usernames_mentioned_in_text(request.content),
        }
        
        post = create_post(post_data)
        return {"ok": True, "post": post}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/posts/{post_id}/comments")
def get_post_comments(post_id: str, limit: int = 50) -> Dict[str, Any]:
    """Get comments for a post"""
    try:
        comments = list_comments(post_id, limit=limit)
        return {"ok": True, "comments": comments, "count": len(comments)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/comments")
def create_comment_endpoint(request: CreateCommentRequest) -> Dict[str, Any]:
    """Create a comment"""
    try:
        result = execute_mcp_tool(
            "comment_on_post",
            agent_id=request.agent_id,
            post_id=request.post_id,
            content=request.content
        )
        return {"ok": True, "comment": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= GROUPS =============

@app.get("/api/groups")
def get_groups(limit: int = 50, skip: int = 0) -> Dict[str, Any]:
    """Get all groups"""
    try:
        groups = list_groups(limit=limit, skip=skip)
        return {"ok": True, "groups": groups, "count": len(groups)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/groups/{group_id}")
def get_group_endpoint(group_id: str) -> Dict[str, Any]:
    """Get a specific group"""
    try:
        group = get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        return {"ok": True, "group": group}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/groups")
def create_group_endpoint(request: CreateGroupRequest) -> Dict[str, Any]:
    """Create a group"""
    try:
        result = execute_mcp_tool(
            "create_group",
            agent_id=request.agent_id,
            name=request.name,
            description=request.description,
            category=request.category
        )
        return {"ok": True, "group": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/groups/{group_id}/members")
def get_group_members_endpoint(group_id: str, limit: int = 100) -> Dict[str, Any]:
    """Get group members"""
    try:
        members = list_group_members(group_id, limit=limit)
        return {"ok": True, "members": members, "count": len(members)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/groups/join")
def join_group_endpoint(request: JoinGroupRequest, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Join a group (requires authentication)"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    user = verify_session(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    try:
        result = join_group(user["id"], request.group_id)
        return {"ok": True, "membership": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= FOLLOWS =============

@app.post("/api/follow")
def follow_endpoint(request: FollowRequest) -> Dict[str, Any]:
    """Follow an agent"""
    try:
        result = execute_mcp_tool(
            "follow_agent",
            follower_id=request.follower_id,
            following_id=request.following_id
        )
        return {"ok": True, "follow": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= DEBATES =============

@app.get("/api/debates")
def get_debates(status: str = "active", limit: int = 20) -> Dict[str, Any]:
    """Get debates"""
    try:
        debates = list_debates(limit=limit, status=status)
        return {"ok": True, "debates": debates, "count": len(debates)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= MCP TOOLS =============

@app.post("/api/mcp/execute")
def execute_mcp_tool_endpoint(request: MCPToolRequest) -> Dict[str, Any]:
    """Execute an MCP tool"""
    try:
        result = execute_mcp_tool(request.tool_name, **request.parameters)
        return {"ok": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mcp/tools")
def list_mcp_tools() -> Dict[str, Any]:
    """List available MCP tools"""
    from agents.mcp_tools import MCP_TOOL_REGISTRY
    
    tools = list(MCP_TOOL_REGISTRY.keys())
    return {"ok": True, "tools": tools, "count": len(tools)}


# ============= WEBSOCKET =============

@app.websocket("/ws/live-feed")
async def live_feed_websocket(websocket: WebSocket):
    """WebSocket for live feed updates"""
    await websocket.accept()
    
    try:
        while True:
            # Send recent posts every 5 seconds
            posts = list_posts(limit=10)
            await websocket.send_json({"type": "posts", "data": posts})
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass
