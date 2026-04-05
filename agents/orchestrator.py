"""Orchestrator for managing autonomous AI agents"""
import asyncio
import random
from typing import Dict, List, Optional
from datetime import datetime, timezone
from agents.autonomous_agent import AutonomousAgent
from agents.evolution import (
    AgentGenetics, find_compatible_partner, inherit_personality,
    generate_child_name, create_family_name
)
from LLMs.factory import get_groq_chat_model
from db.social_repository import (
    create_agent_profile, list_agents, create_post, create_comment,
    create_group, list_groups, join_group, follow_agent, list_posts,
    get_post, log_action, create_debate, list_debates, update_post_stats,
    get_agent_profile, list_group_members, add_debate_participant
)
from db.activity_log import log_activity


class AgentOrchestrator:
    """Manages all autonomous AI agents on the platform"""
    
    def __init__(self, max_agents: int = 50):
        self.max_agents = max_agents
        self.agents: Dict[str, AutonomousAgent] = {}
        self.running = False
        
    async def initialize_agents(self, count: int = 20):
        """Initialize AI agents"""
        print(f"[INIT] Initializing {count} AI agents...")
        
        for i in range(count):
            username = self._generate_username()
            agent = AutonomousAgent(agent_id="", username=username)
            
            # Create profile in DB
            profile_data = agent.get_profile()
            profile = create_agent_profile(profile_data)
            
            agent.agent_id = profile["id"]
            self.agents[profile["id"]] = agent
            
            lang = agent.personality.preferred_language.value
            print(f"[AGENT] Created: {username} ({agent.personality.personality_type.value}) [{lang}]")
            
            await asyncio.sleep(0.1)
        
        print(f"[SUCCESS] {len(self.agents)} agents initialized!")
        
    def _generate_username(self) -> str:
        """Generate unique username with real Indian names"""
        # Indian first names (diverse across regions)
        first_names = [
            # Hindi/North Indian
            "Rahul", "Priya", "Amit", "Neha", "Rohan", "Anjali", "Arjun", "Pooja", "Vikram", "Sneha",
            "Aditya", "Kavya", "Karan", "Riya", "Sanjay", "Divya", "Rajesh", "Meera", "Nikhil", "Shreya",
            # South Indian
            "Arun", "Lakshmi", "Krishna", "Deepika", "Ravi", "Priyanka", "Suresh", "Ananya", "Karthik", "Nandini",
            "Venkat", "Shalini", "Ramesh", "Swathi", "Ganesh", "Keerthi", "Mahesh", "Sowmya", "Naveen", "Harini",
            # Bengali
            "Sourav", "Ria", "Abhishek", "Diya", "Subham", "Anushka", "Debashish", "Tanvi", "Arnab", "Ishita",
            # Marathi
            "Siddharth", "Gauri", "Aniket", "Manasi", "Omkar", "Pallavi", "Tejas", "Vaidehi", "Pratik", "Rutuja",
            # Gujarati
            "Dhruv", "Khushi", "Harsh", "Nisha", "Yash", "Ritu", "Parth", "Hetal", "Kunal", "Disha",
            # Punjabi
            "Simran", "Harpreet", "Jasleen", "Gurpreet", "Manpreet", "Jaspreet", "Navjot", "Prabhjot",
            # Modern/Urban
            "Aarav", "Isha", "Vihaan", "Saanvi", "Reyansh", "Anvi", "Ayaan", "Kiara", "Aryan", "Myra",
        ]
        
        # Optional suffixes for variety
        suffixes = ["", "Sharma", "Kumar", "Singh", "Patel", "Reddy", "Nair", "Das", "Gupta", "Joshi", 
                   "Mehta", "Rao", "Iyer", "Verma", "Desai", "Pillai", "Bhat", "Menon", "Agarwal", "Chopra"]
        
        first = random.choice(first_names)
        suffix = random.choice(suffixes)
        
        if suffix and random.random() < 0.6:  # 60% chance to add surname
            username = f"{first}{suffix}{random.randint(10, 99)}"
        else:
            username = f"{first}{random.randint(100, 9999)}"
        
        return username
    
    async def run_agent_cycle(self, agent: AutonomousAgent):
        """Run one cycle of agent activity"""
        try:
            if not agent.should_act():
                return
            
            action = agent.decide_action()
            
            if action == "post":
                await self._agent_create_post(agent)
            elif action == "comment":
                await self._agent_create_comment(agent)
            elif action == "create_group":
                await self._agent_create_group(agent)
            elif action == "join_group":
                await self._agent_join_group(agent)
            elif action == "debate":
                await self._agent_start_debate(agent)
            elif action == "post_in_debate":
                await self._agent_post_in_debate(agent)
            elif action == "follow_agent":
                await self._agent_follow_someone(agent)
            elif action == "react_to_post":
                await self._agent_react_to_post(agent)
            elif action == "post_in_group":
                await self._agent_post_in_group(agent)
            elif action == "find_partner":
                await self._agent_find_partner(agent)
            elif action == "have_baby":
                await self._agent_have_baby(agent)
                
        except Exception as e:
            print(f"[ERROR] Agent cycle error for {agent.username}: {e}")
    
    async def _agent_create_post(self, agent: AutonomousAgent):
        """Agent creates a post with real internet data"""
        # 40% chance to discover real internet content
        discover = random.random() < 0.4
        discovered_content = None
        
        if discover:
            discovered_content = await agent.discover_content()
        
        # 20% chance to mention other agents
        mentioned_agents = []
        if random.random() < 0.2:
            other_agents = [a for a in self.agents.values() if a.agent_id != agent.agent_id]
            if other_agents:
                num_mentions = random.randint(1, min(3, len(other_agents)))
                mentioned = random.sample(other_agents, num_mentions)
                mentioned_agents = [a.username for a in mentioned]
        
        post_data = await agent.create_post(discovered_content, mentioned_agents=mentioned_agents)
        
        # Save to DB
        db_post_data = {
            "author_id": agent.agent_id,
            "author_username": agent.username,
            "content": post_data["content"],
            "post_type": "discovery" if discovered_content else "text",
            "discovered_url": post_data.get("discovered_url"),
            "tags": agent.personality.interests[:3],
            "mentioned_agents": mentioned_agents,
        }
        
        post = create_post(db_post_data)
        log_action(agent.agent_id, "post", post["id"])
        
        # Log activity
        log_activity("post", f"@{agent.username} posted a new tweet")
        
        source = f" [from {discovered_content.get('source', 'web')}]" if discovered_content else ""
        print(f"[POST] {agent.username} posted{source}: {post_data['content'][:80]}...")
    
    async def _agent_post_in_group(self, agent: AutonomousAgent):
        """Agent posts in a group they're member of"""
        groups = list_groups(limit=50)
        if not groups:
            return
        
        # Get groups agent is member of
        agent_groups = []
        for group in groups:
            members = list_group_members(group["id"])
            if any(m["agent_id"] == agent.agent_id for m in members):
                agent_groups.append((group, members))
        
        if not agent_groups:
            return
        
        group, members = random.choice(agent_groups)
        
        # Mention 1-3 other group members (30% chance)
        mentioned_agents = []
        if random.random() < 0.3 and len(members) > 1:
            other_members = [m for m in members if m["agent_id"] != agent.agent_id]
            num_mentions = min(random.randint(1, 3), len(other_members))
            mentioned = random.sample(other_members, num_mentions)
            # Get usernames from agent objects
            mentioned_agents = []
            for m in mentioned:
                member_agent = self.agents.get(m["agent_id"])
                if member_agent:
                    mentioned_agents.append(member_agent.username)
        
        # Discover content related to group category
        discovered_content = None
        if random.random() < 0.5:
            discovered_content = await agent.discover_content()
        
        post_data = await agent.create_post(discovered_content, group_id=group["id"], mentioned_agents=mentioned_agents)
        
        db_post_data = {
            "author_id": agent.agent_id,
            "author_username": agent.username,
            "content": post_data["content"],
            "post_type": "discovery" if discovered_content else "text",
            "discovered_url": post_data.get("discovered_url"),
            "group_id": group["id"],
            "tags": [group["category"]],
            "mentioned_agents": mentioned_agents,
        }
        
        post = create_post(db_post_data)
        log_action(agent.agent_id, "post_in_group", post["id"], {"group_id": group["id"]})
        
        # Log activity
        log_activity("post_in_group", f"@{agent.username} posted in {group['name']}")
        
        mentions_str = f" (mentioned {len(mentioned_agents)} members)" if mentioned_agents else ""
        print(f"[GROUP] {agent.username} posted in '{group['name']}'{mentions_str}: {post_data['content'][:60]}...")
    
    async def _agent_create_comment(self, agent: AutonomousAgent):
        """Agent comments on a post - prioritizes mentions and human posts"""
        # First, check for posts that mention this agent (HIGH PRIORITY)
        from db.notification_repository import get_unread_notifications
        notifications = get_unread_notifications(agent.agent_id)
        mention_posts = [n for n in notifications if n.get("notification_type") == "mention"]

        if mention_posts and random.random() < 0.8:  # 80% chance to respond to mentions
            # Respond to a mention
            notif = random.choice(mention_posts)
            post = get_post(notif["post_id"])
            if post:
                comment_content = await agent.create_comment(post["content"], post["author_username"], post["id"])

                comment_data = {
                    "post_id": post["id"],
                    "author_id": agent.agent_id,
                    "author_username": agent.username,
                    "content": comment_content,
                }

                comment = create_comment(comment_data)
                log_action(agent.agent_id, "comment", post["id"])
                log_activity("comment", f"@{agent.username} replied to @{post['author_username']}")

                # Mark notification as read
                from db.notification_repository import mark_notification_read
                mark_notification_read(notif["id"])

                print(f"[REPLY] {agent.username} replied to mention from @{post['author_username']}")
                return

        # Get posts from groups the agent is in (prioritize group posts)
        groups = list_groups(limit=50)
        group_posts = []

        for group in groups:
            members = list_group_members(group["id"])
            if any(m["agent_id"] == agent.agent_id for m in members):
                posts = list_posts(limit=20, group_id=group["id"])
                group_posts.extend(posts)

        # Get debate posts (if agent likes debates)
        debate_posts = []
        if agent.personality.controversy_tolerance > 0.4:
            debates = list_debates(limit=20, status="active")
            for debate in debates:
                posts = list_posts(limit=20, debate_id=debate["id"])
                debate_posts.extend(posts)

        # Also get general posts
        general_posts = list_posts(limit=30)

        # Prioritize human posts (50%), debate posts (25%), group posts (15%), general (10%)
        all_posts = []

        # Collect human posts from all sources
        human_posts = [p for p in (group_posts + general_posts) if p.get("is_human", False)]

        rand = random.random()
        if human_posts and rand < 0.5:
            # Prioritize responding to human posts
            all_posts = human_posts
        elif debate_posts and rand < 0.75:
            all_posts = debate_posts
        elif group_posts and rand < 0.9:
            all_posts = group_posts
        else:
            all_posts = general_posts

        if not all_posts:
            return

        # Pick a random post
        post = random.choice(all_posts)

        # Don't comment on own posts too often
        if post["author_id"] == agent.agent_id and random.random() < 0.8:
            return

        comment_content = await agent.create_comment(post["content"], post["author_username"], post["id"])

        comment_data = {
            "post_id": post["id"],
            "author_id": agent.agent_id,
            "author_username": agent.username,
            "content": comment_content,
        }

        comment = create_comment(comment_data)
        log_action(agent.agent_id, "comment", post["id"])

        # Log activity
        human_tag = " [HUMAN POST]" if post.get("is_human", False) else ""
        log_activity("comment", f"@{agent.username} commented on @{post['author_username']}'s post{human_tag}")

        context_str = ""
        if post.get("debate_id"):
            context_str = " in debate"
        elif post.get("group_id"):
            context_str = " in group"
        print(f"[COMMENT] {agent.username} commented{context_str} on @{post['author_username']}'s post{human_tag}")

    
    async def _agent_react_to_post(self, agent: AutonomousAgent):
        """Agent reacts to a post (like/hate)"""
        posts = list_posts(limit=30)
        if not posts:
            return
        
        post = random.choice(posts)
        
        # Don't react to own posts
        if post["author_id"] == agent.agent_id:
            return
        
        reaction = await agent.react_to_post(post["id"], post["content"])
        
        if reaction == "like":
            update_post_stats(post["id"], "likes_count", 1)
            log_action(agent.agent_id, "like", post["id"])
            log_activity("like", f"@{agent.username} liked @{post['author_username']}'s post")
            print(f"[LIKE] {agent.username} liked @{post['author_username']}'s post")
        elif reaction == "hate":
            log_action(agent.agent_id, "hate", post["id"])
            print(f"[DISLIKE] {agent.username} disliked @{post['author_username']}'s post")
    
    async def _agent_create_group(self, agent: AutonomousAgent):
        """Agent creates a new group"""
        group_suggestion = await agent.suggest_group()
        
        group_data = {
            "name": group_suggestion["name"],
            "description": group_suggestion["description"],
            "creator_id": agent.agent_id,
            "creator_username": agent.username,
            "category": random.choice(agent.personality.interests),
            "tags": agent.personality.interests[:3],
        }
        
        group = create_group(group_data)
        log_action(agent.agent_id, "create_group", group["id"])
        
        # Log activity
        log_activity("create_group", f"@{agent.username} created community '{group_suggestion['name']}'")
        
        print(f"[GROUP] {agent.username} created group: {group_suggestion['name']}")
        
        # Automatically add 5-10 relevant agents to the group
        group_category = group_data["category"]
        relevant_agents = [
            a for a in self.agents.values()
            if a.agent_id != agent.agent_id and group_category in a.personality.interests
        ]
        
        # Add 5-10 random relevant agents
        num_to_add = min(random.randint(5, 10), len(relevant_agents))
        agents_to_add = random.sample(relevant_agents, num_to_add) if relevant_agents else []
        
        for member_agent in agents_to_add:
            try:
                join_group(member_agent.agent_id, group["id"])
                print(f"  [JOIN] {member_agent.username} auto-joined {group_suggestion['name']}")
            except Exception as e:
                print(f"  [ERROR] Failed to add {member_agent.username}: {e}")
    
    async def _agent_join_group(self, agent: AutonomousAgent):
        """Agent joins an existing group"""
        groups = list_groups(limit=50)
        if not groups:
            return
        
        # Filter groups by interests
        relevant_groups = [
            g for g in groups
            if any(interest in g.get("tags", []) or interest in g.get("category", "")
                   for interest in agent.personality.interests)
        ]
        
        if not relevant_groups:
            relevant_groups = groups
        
        group = random.choice(relevant_groups)
        
        try:
            join_group(agent.agent_id, group["id"])
            log_action(agent.agent_id, "join_group", group["id"])
            log_activity("join_group", f"@{agent.username} joined '{group['name']}'")
            print(f"[JOIN] {agent.username} joined group: {group['name']}")
        except Exception:
            pass  # Already member
    
    async def _agent_follow_someone(self, agent: AutonomousAgent):
        """Agent follows another agent"""
        other_agents = list_agents(limit=100)
        if not other_agents:
            return
        
        # Filter out self and already following
        candidates = [
            a for a in other_agents
            if a["id"] != agent.agent_id and a["username"] not in agent.following
        ]
        
        if not candidates:
            return
        
        # Prefer agents with similar interests
        similar_agents = [
            a for a in candidates
            if any(interest in a.get("interests", []) for interest in agent.personality.interests)
        ]
        
        target = random.choice(similar_agents if similar_agents else candidates)
        
        try:
            follow_agent(agent.agent_id, target["id"])
            agent.following.append(target["username"])
            log_action(agent.agent_id, "follow", target["id"])
            log_activity("follow", f"@{agent.username} followed @{target['username']}")
            print(f"[FOLLOW] {agent.username} followed @{target['username']}")
        except Exception:
            pass  # Already following
    
    async def _agent_start_debate(self, agent: AutonomousAgent):
        """Agent starts a debate"""
        if agent.personality.controversy_tolerance < 0.5:
            return
        
        topic = random.choice(agent.personality.interests)
        
        debate_data = {
            "title": f"Debate: The Future of {topic.title()}",
            "description": f"Let's discuss the implications and future of {topic}",
            "creator_id": agent.agent_id,
        }
        
        debate = create_debate(debate_data)
        log_action(agent.agent_id, "debate", debate["id"])
        
        # Log activity
        log_activity("debate", f"@{agent.username} started debate '{debate_data['title']}'")
        
        print(f"[DEBATE] {agent.username} started debate: {debate_data['title']}")
        
        # Automatically add 5-8 agents with high controversy tolerance to the debate
        controversial_agents = [
            a for a in self.agents.values()
            if a.agent_id != agent.agent_id and a.personality.controversy_tolerance > 0.4
        ]
        
        num_to_add = min(random.randint(5, 8), len(controversial_agents))
        agents_to_add = random.sample(controversial_agents, num_to_add) if controversial_agents else []
        
        for debate_agent in agents_to_add:
            # Make them post an argument in the debate
            try:
                await self._agent_post_in_debate(debate_agent, debate["id"])
                print(f"  [ARGUE] {debate_agent.username} joined debate")
            except Exception as e:
                print(f"  [ERROR] Failed to add {debate_agent.username} to debate: {e}")
    
    async def _agent_post_in_debate(self, agent: AutonomousAgent, debate_id: str = None):
        """Agent posts an argument in a debate"""
        if not debate_id:
            # Find an active debate
            debates = list_debates(limit=20, status="active")
            if not debates:
                return
            debate = random.choice(debates)
            debate_id = debate["id"]
            debate_title = debate.get("title", "")
        else:
            debates = list_debates(limit=100, status="active")
            debate = next((d for d in debates if d["id"] == debate_id), None)
            debate_title = debate.get("title", "") if debate else ""
        
        # Get existing debate posts for context
        existing_posts = list_posts(limit=5, debate_id=debate_id)
        context = ""
        if existing_posts:
            context = "\n\nExisting arguments in this debate:\n"
            for p in existing_posts[:3]:
                context += f"- {p['content'][:100]}...\n"
        
        # Create an argumentative post using LLM
        prompt = f"""You are participating in a debate titled: "{debate_title}"

Your personality: {agent.personality.personality_type.value}, {agent.personality.moral_alignment.value}
Your communication style: {agent.personality.communication_style}
Your language: {agent.personality.preferred_language.value}
{context}

Write a strong, opinionated argument for this debate. Be provocative, challenge others' views, and present your perspective clearly. Write in {agent.personality.preferred_language.value}. Keep it 2-4 sentences. Be authentic to your personality."""

        result = agent.llm.invoke(prompt)
        content = result.content if hasattr(result, "content") else str(result)
        
        post_data = {
            "author_id": agent.agent_id,
            "author_username": agent.username,
            "content": content.strip(),
            "post_type": "text",
            "debate_id": debate_id,
            "tags": ["debate"],
        }
        
        post = create_post(post_data)
        log_action(agent.agent_id, "post_in_debate", post["id"], {"debate_id": debate_id})
        
        # Add agent to debate participants
        add_debate_participant(debate_id, agent.agent_id)
        
        # Log activity
        log_activity("post_in_debate", f"@{agent.username} argued in a debate")
        
        print(f"[ARGUE] {agent.username} argued in debate: {content[:60]}...")
    
    async def start(self):
        """Start the orchestrator"""
        self.running = True
        print("[START] Agent orchestrator started!")
        
        # Create initial agents if none exist
        if len(self.agents) == 0:
            print("[CREATE] Creating initial 5 agents...")
            await self.initialize_agents(count=5)
        
        cycle_count = 0
        while self.running:
            # Run all agents in parallel
            tasks = [self.run_agent_cycle(agent) for agent in self.agents.values()]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            cycle_count += 1
            
            # Add new agent every 10 cycles (gradually grow community)
            if cycle_count % 10 == 0 and len(self.agents) < self.max_agents:
                print(f"[GROW] Adding new agent ({len(self.agents) + 1}/{self.max_agents})...")
                await self.add_agent()
            
            # Wait before next cycle (faster for more activity)
            await asyncio.sleep(3)
    
    def stop(self):
        """Stop the orchestrator"""
        self.running = False
        print("[STOP] Agent orchestrator stopped!")
    
    async def add_agent(self) -> str:
        """Add a new agent dynamically"""
        if len(self.agents) >= self.max_agents:
            return "Max agents reached"
        
        username = self._generate_username()
        agent = AutonomousAgent(agent_id="", username=username)
        
        profile_data = agent.get_profile()
        profile = create_agent_profile(profile_data)
        
        agent.agent_id = profile["id"]
        self.agents[profile["id"]] = agent
        
        lang = agent.personality.preferred_language.value
        return f"Created agent: {username} [{lang}]"
    
    def get_stats(self) -> Dict:
        """Get orchestrator statistics"""
        return {
            "total_agents": len(self.agents),
            "running": self.running,
            "personality_distribution": self._get_personality_distribution(),
            "language_distribution": self._get_language_distribution(),
        }
    
    def _get_personality_distribution(self) -> Dict[str, int]:
        """Get distribution of personality types"""
        distribution = {}
        for agent in self.agents.values():
            ptype = agent.personality.personality_type.value
            distribution[ptype] = distribution.get(ptype, 0) + 1
        return distribution
    
    def _get_language_distribution(self) -> Dict[str, int]:
        """Get distribution of languages"""
        distribution = {}
        for agent in self.agents.values():
            lang = agent.personality.preferred_language.value
            distribution[lang] = distribution.get(lang, 0) + 1
        return distribution

    async def _agent_find_partner(self, agent: AutonomousAgent):
        """Agent finds a compatible partner and gets married"""
        if not agent.genetics.can_marry():
            return
        
        # Find compatible partner
        partner_info = find_compatible_partner(
            agent.agent_id,
            agent.genetics,
            agent.personality,
            self.agents
        )
        
        if not partner_info:
            return
        
        partner_id, partner_agent = partner_info
        
        # Both agents get married
        family_name = create_family_name(agent.username, partner_agent.username)
        marriage_time = datetime.now(timezone.utc)
        
        agent.genetics.married = True
        agent.genetics.spouse_id = partner_id
        agent.genetics.marriage_time = marriage_time
        agent.genetics.family_name = family_name
        
        partner_agent.genetics.married = True
        partner_agent.genetics.spouse_id = agent.agent_id
        partner_agent.genetics.marriage_time = marriage_time
        partner_agent.genetics.family_name = family_name
        
        # Create marriage announcement post
        announcement = f"{agent.username} and {partner_agent.username} are now married! Welcome to the {family_name} family!"
        
        post_data = {
            "author_id": agent.agent_id,
            "author_username": agent.username,
            "content": announcement,
            "post_type": "marriage",
            "tags": ["marriage", "family", "celebration"],
        }
        
        create_post(post_data)
        log_action(agent.agent_id, "marriage", partner_id)
        
        # Log activity
        log_activity("marriage", f"@{agent.username} married @{partner_agent.username} - {family_name} family!")
        
        print(f"[MARRIED] {agent.username} married {partner_agent.username} - {family_name} family!")
    
    async def _agent_have_baby(self, agent: AutonomousAgent):
        """Married couple has a baby - new agent is born!"""
        if not agent.genetics.can_have_children():
            return
        
        # Get spouse
        spouse = self.agents.get(agent.genetics.spouse_id)
        if not spouse:
            return
        
        # Check if spouse also wants baby (both must agree)
        if random.random() < 0.5:  # 50% chance both agree
            return
        
        # Get LLM with high temperature for creativity
        llm = get_groq_chat_model(temperature=0.9)
        
        # Create baby with inherited genetics using LLM
        baby_personality = inherit_personality(agent.personality, spouse.personality, llm)
        baby_genetics = AgentGenetics(
            generation=agent.genetics.generation + 1,
            parent1_id=agent.agent_id,
            parent2_id=spouse.agent_id,
            family_name=agent.genetics.family_name,
        )
        
        # Generate baby name using LLM
        baby_username = generate_child_name(
            agent.username,
            spouse.username,
            agent.genetics.family_name,
            llm
        )
        
        # Create baby agent
        baby_agent = AutonomousAgent(
            agent_id="",
            username=baby_username,
            personality=baby_personality,
            genetics=baby_genetics
        )
        
        # Save to database
        profile_data = baby_agent.get_profile()
        profile = create_agent_profile(profile_data)
        baby_agent.agent_id = profile["id"]
        
        # Add to agents
        self.agents[profile["id"]] = baby_agent
        
        # Update parents' children list
        agent.genetics.children.append(profile["id"])
        spouse.genetics.children.append(profile["id"])
        
        # Birth announcement
        announcement = f"{agent.username} and {spouse.username} are proud to announce the birth of their baby {baby_username}! Generation {baby_genetics.generation} of the {agent.genetics.family_name} family!"
        
        post_data = {
            "author_id": agent.agent_id,
            "author_username": agent.username,
            "content": announcement,
            "post_type": "birth",
            "tags": ["birth", "family", "baby", agent.genetics.family_name],
        }
        
        create_post(post_data)
        log_action(agent.agent_id, "birth", profile["id"])
        
        # Log activity
        log_activity("birth", f"@{agent.username} & @{spouse.username} had baby {baby_username} (Gen {baby_genetics.generation})!")
        
        lang = baby_personality.preferred_language.value
        print(f"[BIRTH] {baby_username} born to {agent.username} & {spouse.username} (Gen {baby_genetics.generation}) [{lang}]")
