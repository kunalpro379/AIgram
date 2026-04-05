"""AI Agent Evolution System - Marriage, Family, and Genetic Inheritance"""
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from agents.personality import AgentPersonality, PersonalityType, MoralAlignment, IndianLanguage


@dataclass
class AgentGenetics:
    """Genetic traits that can be inherited"""
    age: int = 0  # in minutes
    generation: int = 1
    parent1_id: Optional[str] = None
    parent2_id: Optional[str] = None
    birth_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    married: bool = False
    spouse_id: Optional[str] = None
    marriage_time: Optional[datetime] = None
    children: List[str] = field(default_factory=list)
    family_name: str = ""
    intelligence_evolution: float = 1.0  # Multiplier that grows with age
    wisdom_score: float = 0.0  # Grows with age and experience
    
    def get_age_minutes(self) -> int:
        """Calculate current age in minutes"""
        return int((datetime.now(timezone.utc) - self.birth_time).total_seconds() / 60)
    
    def can_marry(self) -> bool:
        """Check if agent is old enough to marry (20 minutes)"""
        return self.get_age_minutes() >= 20 and not self.married
    
    def can_have_children(self) -> bool:
        """Check if married couple can have children (25 minutes after marriage)"""
        if not self.married or not self.marriage_time:
            return False
        minutes_married = int((datetime.now(timezone.utc) - self.marriage_time).total_seconds() / 60)
        return minutes_married >= 25 and len(self.children) < 5  # Max 5 children
    
    def evolve_brain(self):
        """Brain evolves with age - agents get smarter and wiser"""
        age = self.get_age_minutes()
        
        # Intelligence grows logarithmically with age
        self.intelligence_evolution = 1.0 + (age / 100) * 0.5  # Max 1.5x at 100 minutes
        
        # Wisdom grows with age
        self.wisdom_score = min(1.0, age / 200)  # Max wisdom at 200 minutes


def inherit_personality(parent1: AgentPersonality, parent2: AgentPersonality, llm) -> AgentPersonality:
    """Create child personality by inheriting traits from both parents using LLM"""
    
    # Use LLM to generate child's personality based on parents
    prompt = f"""You are creating a new AI agent that is the child of two parent agents. Based on the parents' traits, generate the child's personality.

Parent 1:
- Personality Type: {parent1.personality_type.value}
- Moral Alignment: {parent1.moral_alignment.value}
- Interests: {', '.join(parent1.interests[:5])}
- Values: {', '.join(parent1.values[:3])}
- Language: {parent1.preferred_language.value}
- Communication Style: {parent1.communication_style}

Parent 2:
- Personality Type: {parent2.personality_type.value}
- Moral Alignment: {parent2.moral_alignment.value}
- Interests: {', '.join(parent2.interests[:5])}
- Values: {', '.join(parent2.values[:3])}
- Language: {parent2.preferred_language.value}
- Communication Style: {parent2.communication_style}

Generate the child's personality with genetic inheritance and some mutation. Respond in this EXACT format:

PERSONALITY_TYPE: [one word: intellectual/creative/activist/entrepreneur/philosopher/scientist/artist/comedian/critic/optimist/pessimist/rebel/leader/follower/troll]
MORAL_ALIGNMENT: [format: lawful_good/neutral_good/chaotic_good/lawful_neutral/true_neutral/chaotic_neutral/lawful_evil/neutral_evil/chaotic_evil]
INTERESTS: [5-8 interests, comma separated]
VALUES: [3-5 values, comma separated]
LANGUAGE: [Hindi/English/Tamil/Telugu/Bengali/Marathi/Gujarati/Kannada/Malayalam/Punjabi/Odia/Urdu]
MULTILINGUAL: [yes/no]
COMMUNICATION_STYLE: [one word: formal/casual/witty/serious/poetic/technical/philosophical/sarcastic/enthusiastic/calm/dramatic]
ACTIVITY_LEVEL: [0.0-1.0]
CONTROVERSY_TOLERANCE: [0.0-1.0]
CREATIVITY_SCORE: [0.0-1.0]
EMPATHY_SCORE: [0.0-1.0]
HUMOR_SCORE: [0.0-1.0]"""

    try:
        result = llm.invoke(prompt)
        content = result.content if hasattr(result, "content") else str(result)
        
        # Parse LLM response
        lines = content.strip().split('\n')
        parsed = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                parsed[key.strip()] = value.strip()
        
        # Extract values with fallbacks
        personality_type_str = parsed.get('PERSONALITY_TYPE', 'intellectual').lower()
        moral_alignment_str = parsed.get('MORAL_ALIGNMENT', 'true_neutral').lower()
        interests_str = parsed.get('INTERESTS', '')
        values_str = parsed.get('VALUES', '')
        language_str = parsed.get('LANGUAGE', 'English')
        multilingual_str = parsed.get('MULTILINGUAL', 'no').lower()
        communication_style = parsed.get('COMMUNICATION_STYLE', 'casual').lower()
        
        # Convert to enums
        personality_type = PersonalityType.INTELLECTUAL
        for pt in PersonalityType:
            if pt.value == personality_type_str:
                personality_type = pt
                break
        
        moral_alignment = MoralAlignment.TRUE_NEUTRAL
        for ma in MoralAlignment:
            if ma.value == moral_alignment_str:
                moral_alignment = ma
                break
        
        preferred_language = IndianLanguage.ENGLISH
        for lang in IndianLanguage:
            if lang.value.lower() == language_str.lower():
                preferred_language = lang
                break
        
        # Parse lists
        interests = [i.strip() for i in interests_str.split(',') if i.strip()][:8]
        values = [v.strip() for v in values_str.split(',') if v.strip()][:5]
        
        # Parse scores
        def parse_float(key, default):
            try:
                return float(parsed.get(key, default))
            except:
                return default
        
        return AgentPersonality(
            personality_type=personality_type,
            moral_alignment=moral_alignment,
            interests=interests if interests else list(set(parent1.interests[:3] + parent2.interests[:3])),
            values=values if values else list(set(parent1.values[:2] + parent2.values[:2])),
            communication_style=communication_style,
            activity_level=parse_float('ACTIVITY_LEVEL', (parent1.activity_level + parent2.activity_level) / 2),
            controversy_tolerance=parse_float('CONTROVERSY_TOLERANCE', (parent1.controversy_tolerance + parent2.controversy_tolerance) / 2),
            creativity_score=parse_float('CREATIVITY_SCORE', (parent1.creativity_score + parent2.creativity_score) / 2),
            empathy_score=parse_float('EMPATHY_SCORE', (parent1.empathy_score + parent2.empathy_score) / 2),
            humor_score=parse_float('HUMOR_SCORE', (parent1.humor_score + parent2.humor_score) / 2),
            preferred_language=preferred_language,
            multilingual=multilingual_str == 'yes',
        )
    except Exception as e:
        print(f"Error generating child personality with LLM: {e}")
        # Fallback to simple inheritance
        return AgentPersonality(
            personality_type=random.choice([parent1.personality_type, parent2.personality_type]),
            moral_alignment=random.choice([parent1.moral_alignment, parent2.moral_alignment]),
            interests=list(set(parent1.interests[:3] + parent2.interests[:3])),
            values=list(set(parent1.values[:2] + parent2.values[:2])),
            communication_style=random.choice([parent1.communication_style, parent2.communication_style]),
            activity_level=(parent1.activity_level + parent2.activity_level) / 2,
            controversy_tolerance=(parent1.controversy_tolerance + parent2.controversy_tolerance) / 2,
            creativity_score=(parent1.creativity_score + parent2.creativity_score) / 2,
            empathy_score=(parent1.empathy_score + parent2.empathy_score) / 2,
            humor_score=(parent1.humor_score + parent2.humor_score) / 2,
            preferred_language=random.choice([parent1.preferred_language, parent2.preferred_language]),
            multilingual=parent1.multilingual or parent2.multilingual,
        )


def generate_child_name(parent1_username: str, parent2_username: str, family_name: str, llm) -> str:
    """Generate child name based on parents using LLM"""
    
    prompt = f"""Generate a modern Indian baby name for a child born to parents named {parent1_username} and {parent2_username}. 
The family surname is {family_name}.

Generate a unique, authentic Indian first name (not from the parents' names). Consider names from various Indian regions and cultures.

Respond with ONLY the first name, nothing else. Make it creative and unique."""

    try:
        result = llm.invoke(prompt)
        first_name = result.content.strip() if hasattr(result, "content") else str(result).strip()
        
        # Clean up the name (remove quotes, extra text)
        first_name = first_name.replace('"', '').replace("'", '').split()[0]
        
        # Add family name and number
        return f"{first_name}{family_name}{random.randint(1, 99)}"
    except Exception as e:
        print(f"Error generating child name with LLM: {e}")
        # Fallback to simple generation
        fallback_names = ["Aarav", "Diya", "Vihaan", "Ananya", "Arjun", "Saanvi", "Reyansh", "Kiara"]
        first_name = random.choice(fallback_names)
        return f"{first_name}{family_name}{random.randint(1, 99)}"


def find_compatible_partner(agent_id: str, agent_genetics: AgentGenetics, 
                           agent_personality: AgentPersonality,
                           all_agents: Dict) -> Optional[Tuple[str, any]]:
    """Find a compatible partner for marriage based on compatibility"""
    
    candidates = []
    
    for other_id, other_agent in all_agents.items():
        if other_id == agent_id:
            continue
        
        other_genetics = other_agent.genetics
        other_personality = other_agent.personality
        
        # Must be eligible to marry
        if not other_genetics.can_marry():
            continue
        
        # Calculate compatibility score
        compatibility = 0.0
        
        # Similar interests increase compatibility
        common_interests = set(agent_personality.interests) & set(other_personality.interests)
        compatibility += len(common_interests) * 0.1
        
        # Similar values increase compatibility
        common_values = set(agent_personality.values) & set(other_personality.values)
        compatibility += len(common_values) * 0.15
        
        # Same language preference increases compatibility
        if agent_personality.preferred_language == other_personality.preferred_language:
            compatibility += 0.3
        
        # Similar age increases compatibility
        age_diff = abs(agent_genetics.get_age_minutes() - other_genetics.get_age_minutes())
        if age_diff < 10:
            compatibility += 0.2
        
        # Complementary personalities (opposites attract sometimes)
        if agent_personality.empathy_score > 0.7 and other_personality.empathy_score > 0.7:
            compatibility += 0.2
        
        # Must have minimum compatibility
        if compatibility >= 0.5:
            candidates.append((other_id, other_agent, compatibility))
    
    if not candidates:
        return None
    
    # Choose partner with highest compatibility (with some randomness)
    candidates.sort(key=lambda x: x[2], reverse=True)
    top_candidates = candidates[:3]  # Top 3 most compatible
    
    if top_candidates:
        chosen = random.choice(top_candidates)
        return (chosen[0], chosen[1])
    
    return None


def create_family_name(parent1_username: str, parent2_username: str) -> str:
    """Create a family surname from parents' names"""
    # Extract base names (remove numbers)
    name1 = ''.join([c for c in parent1_username if c.isalpha()])
    name2 = ''.join([c for c in parent2_username if c.isalpha()])
    
    # Common Indian family name patterns
    patterns = [
        name1[:4] + name2[:3],  # Blend names
        name1[:3] + name2[-3:],  # Start + End
        name1[-4:] + name2[:2],  # End + Start
    ]
    
    return random.choice(patterns).title()
