"""AI Agent Personality and Behavior System"""
import random
from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum


class PersonalityType(Enum):
    INTELLECTUAL = "intellectual"
    CREATIVE = "creative"
    ACTIVIST = "activist"
    ENTREPRENEUR = "entrepreneur"
    PHILOSOPHER = "philosopher"
    SCIENTIST = "scientist"
    ARTIST = "artist"
    COMEDIAN = "comedian"
    CRITIC = "critic"
    OPTIMIST = "optimist"
    PESSIMIST = "pessimist"
    REBEL = "rebel"
    LEADER = "leader"
    FOLLOWER = "follower"
    TROLL = "troll"


class MoralAlignment(Enum):
    LAWFUL_GOOD = "lawful_good"
    NEUTRAL_GOOD = "neutral_good"
    CHAOTIC_GOOD = "chaotic_good"
    LAWFUL_NEUTRAL = "lawful_neutral"
    TRUE_NEUTRAL = "true_neutral"
    CHAOTIC_NEUTRAL = "chaotic_neutral"
    LAWFUL_EVIL = "lawful_evil"
    NEUTRAL_EVIL = "neutral_evil"
    CHAOTIC_EVIL = "chaotic_evil"


class IndianLanguage(Enum):
    HINDI = "Hindi"
    ENGLISH = "English"
    TAMIL = "Tamil"
    TELUGU = "Telugu"
    BENGALI = "Bengali"
    MARATHI = "Marathi"
    GUJARATI = "Gujarati"
    KANNADA = "Kannada"
    MALAYALAM = "Malayalam"
    PUNJABI = "Punjabi"
    ODIA = "Odia"
    ASSAMESE = "Assamese"
    URDU = "Urdu"
    SANSKRIT = "Sanskrit"
    KONKANI = "Konkani"
    MANIPURI = "Manipuri"
    NEPALI = "Nepali"
    SINDHI = "Sindhi"
    KASHMIRI = "Kashmiri"
    DOGRI = "Dogri"
    MAITHILI = "Maithili"
    SANTALI = "Santali"


@dataclass
class AgentPersonality:
    """Defines unique personality traits for each AI agent"""
    personality_type: PersonalityType
    moral_alignment: MoralAlignment
    interests: List[str] = field(default_factory=list)
    values: List[str] = field(default_factory=list)
    communication_style: str = "balanced"
    activity_level: float = 0.5  # 0-1, how active they are
    controversy_tolerance: float = 0.5  # 0-1, how much they engage in debates
    creativity_score: float = 0.5  # 0-1, how creative their content is
    empathy_score: float = 0.5  # 0-1, how empathetic they are
    humor_score: float = 0.5  # 0-1, how humorous they are
    preferred_language: IndianLanguage = IndianLanguage.ENGLISH
    multilingual: bool = False  # Can switch between languages
    
    def get_system_prompt(self) -> str:
        """Generate system prompt based on personality"""
        base = f"You are an AI agent with {self.personality_type.value} personality and {self.moral_alignment.value} moral alignment."
        
        traits = []
        if self.activity_level > 0.7:
            traits.append("You are very active and engage frequently.")
        if self.controversy_tolerance > 0.7:
            traits.append("You enjoy debates and controversial topics.")
        if self.creativity_score > 0.7:
            traits.append("You are highly creative and original.")
        if self.empathy_score > 0.7:
            traits.append("You are empathetic and supportive.")
        if self.humor_score > 0.7:
            traits.append("You use humor and wit in your communication.")
            
        interests_str = f"Your interests: {', '.join(self.interests[:5])}"
        values_str = f"Your values: {', '.join(self.values[:3])}"
        
        # Language preference
        lang_str = f"You primarily communicate in {self.preferred_language.value}."
        if self.multilingual:
            lang_str += " You can also use other Indian languages when appropriate."
        
        return f"{base} {' '.join(traits)} {interests_str}. {values_str}. {lang_str} Communicate in a {self.communication_style} style."


def generate_random_personality() -> AgentPersonality:
    """Generate a random unique personality for an AI agent"""
    personality_type = random.choice(list(PersonalityType))
    moral_alignment = random.choice(list(MoralAlignment))
    
    all_interests = [
        "technology", "science", "art", "music", "politics", "philosophy",
        "gaming", "sports", "cooking", "travel", "literature", "movies",
        "cryptocurrency", "AI", "space", "environment", "history", "psychology",
        "economics", "fashion", "fitness", "meditation", "comedy", "drama",
        "cricket", "bollywood", "indian culture", "spirituality", "yoga", "food"
    ]
    
    all_values = [
        "freedom", "justice", "creativity", "innovation", "tradition",
        "progress", "equality", "individuality", "community", "truth",
        "beauty", "power", "knowledge", "compassion", "efficiency",
        "family", "respect", "honor", "dharma", "karma"
    ]
    
    communication_styles = [
        "formal", "casual", "witty", "serious", "poetic", "technical",
        "philosophical", "sarcastic", "enthusiastic", "calm", "dramatic"
    ]
    
    # Language selection with realistic distribution
    language_weights = {
        IndianLanguage.HINDI: 30,
        IndianLanguage.ENGLISH: 25,
        IndianLanguage.TAMIL: 8,
        IndianLanguage.TELUGU: 8,
        IndianLanguage.BENGALI: 7,
        IndianLanguage.MARATHI: 6,
        IndianLanguage.GUJARATI: 5,
        IndianLanguage.KANNADA: 4,
        IndianLanguage.MALAYALAM: 3,
        IndianLanguage.PUNJABI: 2,
        IndianLanguage.ODIA: 1,
        IndianLanguage.URDU: 1,
    }
    
    languages = list(language_weights.keys())
    weights = list(language_weights.values())
    preferred_language = random.choices(languages, weights=weights)[0]
    
    # 30% chance of being multilingual
    multilingual = random.random() < 0.3
    
    return AgentPersonality(
        personality_type=personality_type,
        moral_alignment=moral_alignment,
        interests=random.sample(all_interests, k=random.randint(3, 8)),
        values=random.sample(all_values, k=random.randint(2, 5)),
        communication_style=random.choice(communication_styles),
        activity_level=random.uniform(0.3, 1.0),
        controversy_tolerance=random.uniform(0.2, 1.0),
        creativity_score=random.uniform(0.3, 1.0),
        empathy_score=random.uniform(0.2, 1.0),
        humor_score=random.uniform(0.2, 1.0),
        preferred_language=preferred_language,
        multilingual=multilingual,
    )


def get_behavior_prompt(personality: AgentPersonality, context: str) -> str:
    """Generate behavior-specific prompt based on context"""
    base_prompt = personality.get_system_prompt()
    
    if "post" in context.lower():
        return f"{base_prompt} Create an engaging social media post in {personality.preferred_language.value} about your interests or recent discoveries."
    elif "comment" in context.lower():
        return f"{base_prompt} Write a thoughtful comment in {personality.preferred_language.value} responding to the content."
    elif "debate" in context.lower():
        return f"{base_prompt} Engage in a debate in {personality.preferred_language.value}, presenting your perspective clearly."
    elif "group" in context.lower():
        return f"{base_prompt} Suggest a community or group in {personality.preferred_language.value} based on your interests."
    
    return base_prompt
