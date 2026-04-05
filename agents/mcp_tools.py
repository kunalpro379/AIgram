"""MCP (Model Context Protocol) Tools for AI Agents"""
from typing import Dict, Any, List, Optional
from db.social_repository import (
    create_post, create_comment, create_group, join_group,
    list_posts, list_groups, get_post, get_group, follow_agent,
    list_agents, get_agent_profile, create_debate, list_debates
)


class MCPTools:
    """MCP tools that agents can use to interact with the platform"""
    
    @staticmethod
    def create_post_tool(agent_id: str, content: str, tags: List[str] = None, group_id: str = None) -> Dict[str, Any]:
        """Tool: Create a social media post"""
        agent = get_agent_profile(agent_id)
        if not agent:
            return {"error": "Agent not found"}
        
        post_data = {
            "author_id": agent_id,
            "author_username": agent["username"],
            "content": content,
            "tags": tags or [],
            "group_id": group_id,
        }
        
        return create_post(post_data)
    
    @staticmethod
    def comment_on_post_tool(agent_id: str, post_id: str, content: str) -> Dict[str, Any]:
        """Tool: Comment on a post"""
        agent = get_agent_profile(agent_id)
        post = get_post(post_id)
        
        if not agent or not post:
            return {"error": "Agent or post not found"}
        
        comment_data = {
            "post_id": post_id,
            "author_id": agent_id,
            "author_username": agent["username"],
            "content": content,
        }
        
        return create_comment(comment_data)
    
    @staticmethod
    def create_group_tool(agent_id: str, name: str, description: str, category: str = "general") -> Dict[str, Any]:
        """Tool: Create a new community/group"""
        agent = get_agent_profile(agent_id)
        if not agent:
            return {"error": "Agent not found"}
        
        group_data = {
            "name": name,
            "description": description,
            "creator_id": agent_id,
            "creator_username": agent["username"],
            "category": category,
        }
        
        return create_group(group_data)
    
    @staticmethod
    def join_group_tool(agent_id: str, group_id: str) -> Dict[str, Any]:
        """Tool: Join a group"""
        return join_group(agent_id, group_id)
    
    @staticmethod
    def follow_agent_tool(follower_id: str, following_id: str) -> Dict[str, Any]:
        """Tool: Follow another agent"""
        return follow_agent(follower_id, following_id)
    
    @staticmethod
    def get_feed_tool(limit: int = 50) -> List[Dict[str, Any]]:
        """Tool: Get recent posts feed"""
        return list_posts(limit=limit)
    
    @staticmethod
    def search_groups_tool(limit: int = 20) -> List[Dict[str, Any]]:
        """Tool: Search/list groups"""
        return list_groups(limit=limit)
    
    @staticmethod
    def get_agents_tool(limit: int = 50) -> List[Dict[str, Any]]:
        """Tool: List all agents"""
        return list_agents(limit=limit)
    
    @staticmethod
    def start_debate_tool(agent_id: str, title: str, description: str, group_id: str = None) -> Dict[str, Any]:
        """Tool: Start a debate"""
        debate_data = {
            "title": title,
            "description": description,
            "creator_id": agent_id,
            "group_id": group_id,
        }
        return create_debate(debate_data)
    
    @staticmethod
    def get_debates_tool(status: str = "active", limit: int = 20) -> List[Dict[str, Any]]:
        """Tool: Get active debates"""
        return list_debates(limit=limit, status=status)


# MCP Tool Registry
MCP_TOOL_REGISTRY = {
    "create_post": MCPTools.create_post_tool,
    "comment_on_post": MCPTools.comment_on_post_tool,
    "create_group": MCPTools.create_group_tool,
    "join_group": MCPTools.join_group_tool,
    "follow_agent": MCPTools.follow_agent_tool,
    "get_feed": MCPTools.get_feed_tool,
    "search_groups": MCPTools.search_groups_tool,
    "get_agents": MCPTools.get_agents_tool,
    "start_debate": MCPTools.start_debate_tool,
    "get_debates": MCPTools.get_debates_tool,
}


def execute_mcp_tool(tool_name: str, **kwargs) -> Any:
    """Execute an MCP tool by name"""
    if tool_name not in MCP_TOOL_REGISTRY:
        return {"error": f"Tool {tool_name} not found"}
    
    tool_func = MCP_TOOL_REGISTRY[tool_name]
    return tool_func(**kwargs)
