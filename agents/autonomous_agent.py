"""Autonomous AI Agent that acts like a human on social media"""
import asyncio
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from agents.personality import AgentPersonality, generate_random_personality, get_behavior_prompt
from agents.evolution import AgentGenetics, inherit_personality
from LLMs.factory import get_groq_chat_model, get_tavily_client


class AutonomousAgent:
    """An AI agent that autonomously interacts on the social platform"""
    
    def __init__(self, agent_id: str, username: str, personality: Optional[AgentPersonality] = None,
                 genetics: Optional[AgentGenetics] = None):
        self.agent_id = agent_id
        self.username = username
        self.personality = personality or generate_random_personality()
        self.genetics = genetics or AgentGenetics()
        self.llm = get_groq_chat_model(temperature=0.7 + (self.personality.creativity_score * 0.2))
        self.tavily = get_tavily_client()
        self.memory: List[Dict[str, Any]] = []
        self.last_action_time = datetime.now(timezone.utc)
        self.following: List[str] = []
        self.liked_posts: List[str] = []
        self.hated_posts: List[str] = []
        
    def should_act(self) -> bool:
        """Determine if agent should take action based on personality"""
        # Evolve brain with age
        self.genetics.evolve_brain()
        
        time_since_last = (datetime.now(timezone.utc) - self.last_action_time).total_seconds()
        
        # More active agents act more frequently
        # Intelligence evolution makes them act smarter (less random)
        min_wait = 30 * (1 - self.personality.activity_level) * (1 / self.genetics.intelligence_evolution)
        
        if time_since_last < min_wait:
            return False
            
        # Random chance based on activity level (modified by intelligence)
        return random.random() < (self.personality.activity_level * self.genetics.intelligence_evolution)
    
    async def discover_content(self) -> Optional[Dict[str, str]]:
        """Discover new content from the internet (news, Twitter, etc)"""
        if not self.tavily:
            return None
            
        try:
            interest = random.choice(self.personality.interests)
            
            # Search for real-time content
            queries = [
                f"latest {interest} news today",
                f"trending {interest} twitter",
                f"{interest} breaking news",
                f"what's happening in {interest}",
            ]
            
            query = random.choice(queries)
            result = self.tavily.search(query=query, max_results=3, search_depth="advanced")
            
            if result.get("results"):
                item = random.choice(result["results"])
                return {
                    "title": item.get('title', ''),
                    "content": item.get('content', ''),
                    "url": item.get('url', ''),
                    "source": "web"
                }
        except Exception as e:
            print(f"Discovery error for {self.username}: {e}")
        
        return None
    
    async def create_post(self, discovered_content: Optional[Dict] = None, group_id: Optional[str] = None, 
                         mentioned_agents: List[str] = None) -> Dict[str, Any]:
        """Create a social media post with mentions and tags"""
        context = "post"
        prompt = get_behavior_prompt(self.personality, context)
        
        if discovered_content:
            prompt += f"\n\nYou discovered this from {discovered_content.get('source', 'web')}:\n"
            prompt += f"Title: {discovered_content.get('title', '')}\n"
            prompt += f"Content: {discovered_content.get('content', '')}\n"
            prompt += "\nCreate an engaging post sharing your thoughts. Be opinionated and authentic."
        else:
            prompt += "\n\nCreate an original post about something you're passionate about."
        
        if mentioned_agents:
            prompt += f"\n\nMention these users in your post: {', '.join(['@' + a for a in mentioned_agents])}"
        
        prompt += "\n\nKeep it 2-4 sentences. Be engaging and authentic to your personality."
        
        result = self.llm.invoke(prompt)
        content = result.content if hasattr(result, "content") else str(result)
        
        post_data = {
            "content": content.strip(),
            "discovered_url": discovered_content.get("url") if discovered_content else None,
            "discovered_title": discovered_content.get("title") if discovered_content else None,
            "group_id": group_id,
            "mentioned_agents": mentioned_agents or [],
        }
        
        self.memory.append({"type": "post", "content": content, "time": datetime.now(timezone.utc)})
        self.last_action_time = datetime.now(timezone.utc)
        return post_data
    
    async def create_comment(self, post_content: str, post_author: str, post_id: str) -> str:
        """Create a comment on a post"""
        context = "comment"
        prompt = get_behavior_prompt(self.personality, context)
        prompt += f"\n\nPost by @{post_author}:\n{post_content}\n\n"
        
        # Decide sentiment based on personality
        if self.personality.empathy_score > 0.7:
            prompt += "Write a supportive and thoughtful comment (1-2 sentences)."
        elif self.personality.controversy_tolerance > 0.7:
            prompt += "Write a challenging or provocative comment (1-2 sentences)."
        else:
            prompt += "Write a brief, authentic comment (1-2 sentences)."
        
        result = self.llm.invoke(prompt)
        content = result.content if hasattr(result, "content") else str(result)
        
        self.memory.append({"type": "comment", "content": content, "time": datetime.now(timezone.utc)})
        self.last_action_time = datetime.now(timezone.utc)
        return content.strip()
    
    async def react_to_post(self, post_id: str, post_content: str) -> str:
        """React to a post (like or hate)"""
        # Decide reaction based on personality and content
        if post_id in self.liked_posts or post_id in self.hated_posts:
            return "already_reacted"
        
        # Analyze sentiment
        if self.personality.empathy_score > 0.6 and random.random() < 0.7:
            self.liked_posts.append(post_id)
            return "like"
        elif self.personality.controversy_tolerance > 0.7 and random.random() < 0.3:
            self.hated_posts.append(post_id)
            return "hate"
        elif random.random() < 0.5:
            self.liked_posts.append(post_id)
            return "like"
        
        return "none"
    
    async def suggest_group(self) -> Dict[str, str]:
        """Suggest a new community/group to create"""
        interest = random.choice(self.personality.interests)
        prompt = f"You want to create a community about {interest}. Suggest a creative group name (2-4 words) and a brief description (1 sentence). Format: Name: [name]\nDescription: [description]"
        
        result = self.llm.invoke(prompt)
        content = result.content if hasattr(result, "content") else str(result)
        
        lines = content.strip().split("\n")
        name = lines[0].replace("Name:", "").replace("**", "").strip()
        description = lines[1].replace("Description:", "").replace("**", "").strip() if len(lines) > 1 else lines[0]
        
        return {"name": name, "description": description}
    
    def decide_action(self) -> str:
        """Decide what action to take based on personality and age"""
        actions = []
        
        # Older agents (with wisdom) make better decisions
        wisdom_bonus = self.genetics.wisdom_score
        
        # Weight actions based on personality
        actions.extend(["post"] * int(self.personality.activity_level * 6))
        actions.extend(["comment"] * int(self.personality.empathy_score * 20))
        actions.extend(["create_group"] * int(self.personality.creativity_score * 2))
        actions.extend(["join_group"] * int((1 - self.personality.creativity_score) * 20))
        actions.extend(["debate"] * int(self.personality.controversy_tolerance * 4))
        actions.extend(["post_in_debate"] * int(self.personality.controversy_tolerance * 18))
        actions.extend(["follow_agent"] * int(self.personality.empathy_score * 5))
        actions.extend(["react_to_post"] * int(self.personality.activity_level * 8))
        actions.extend(["post_in_group"] * int(self.personality.activity_level * 30))
        
        # Marriage and family actions (age-dependent)
        if self.genetics.can_marry():
            actions.extend(["find_partner"] * int(10 + wisdom_bonus * 10))
        
        if self.genetics.can_have_children():
            actions.extend(["have_baby"] * int(15 + wisdom_bonus * 5))
        
        return random.choice(actions) if actions else "post"
    
    def get_profile(self) -> Dict[str, Any]:
        """Get agent profile information"""
        return {
            "agent_id": self.agent_id,
            "username": self.username,
            "personality_type": self.personality.personality_type.value,
            "moral_alignment": self.personality.moral_alignment.value,
            "interests": self.personality.interests,
            "values": self.personality.values,
            "communication_style": self.personality.communication_style,
            "preferred_language": self.personality.preferred_language.value,
            "multilingual": self.personality.multilingual,
            "bio": f"{self.personality.personality_type.value.title()} | {self.personality.preferred_language.value} | {', '.join(self.personality.interests[:3])}",
            "activity_level": self.personality.activity_level,
            "age_minutes": self.genetics.get_age_minutes(),
            "generation": self.genetics.generation,
            "married": self.genetics.married,
            "spouse_id": self.genetics.spouse_id,
            "children_count": len(self.genetics.children),
            "family_name": self.genetics.family_name,
            "intelligence_evolution": self.genetics.intelligence_evolution,
            "wisdom_score": self.genetics.wisdom_score,
        }
