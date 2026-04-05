"""LLM factory module"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cache for API keys
_api_key_cache = {}


def _get_api_key_from_db(key_name: str) -> Optional[str]:
    """Get API key from MongoDB"""
    try:
        from db.mongo import get_db
        db = get_db()
        config = db.config.find_one({"key": key_name})
        if config and "value" in config:
            return config["value"]
    except Exception as e:
        print(f"[WARNING] Could not fetch {key_name} from database: {e}")
    return None


def _get_api_key(key_name: str) -> Optional[str]:
    """Get API key from cache, database, or environment"""
    # Check cache first
    if key_name in _api_key_cache:
        return _api_key_cache[key_name]
    
    # Try database first
    api_key = _get_api_key_from_db(key_name)
    
    # Fallback to environment variable
    if not api_key:
        api_key = os.getenv(key_name)
    
    # Cache it
    if api_key:
        _api_key_cache[key_name] = api_key
    
    return api_key


def _is_available(module_name: str) -> bool:
    try:
        __import__(module_name)
        return True
    except Exception:
        return False


def get_groq_chat_model(model: str = "llama-3.3-70b-versatile", temperature: float = 0.7):
    """
    Returns Groq's best chat model (llama-3.3-70b-versatile) for AI agents.
    
    Groq models available:
    - llama-3.3-70b-versatile (BEST - most capable)
    - llama-3.1-70b-versatile
    - mixtral-8x7b-32768
    """
    api_key = _get_api_key("GROQ_API_KEY")
    
    if not api_key:
        print("[ERROR] GROQ_API_KEY not found!")
        print("   Run: python setup_api_keys.py")
        print("   Or check your .env file")
        raise ValueError("Missing GROQ_API_KEY. Run setup_api_keys.py to store it in database.")
    
    # Check if key looks valid
    if len(api_key) < 50:
        print(f"[WARNING] GROQ_API_KEY seems too short ({len(api_key)} chars)")
        print("   Valid Groq keys are usually 70+ characters")
        print("   Get a new key from: https://console.groq.com/keys")

    base_url = "https://api.groq.com/openai/v1"

    if _is_available("langchain_groq"):
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=model,
            api_key=api_key,
            temperature=temperature,
        )

    if _is_available("langchain_openai"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
        )

    raise ImportError(
        "No supported chat backend found. Install langchain-groq or langchain-openai."
    )


def get_tavily_client():
    """
    Returns Tavily client if package + key are available.
    """
    api_key = _get_api_key("TAVILY_API_KEY")
    
    if not api_key:
        return None

    if not _is_available("tavily"):
        return None

    from tavily import TavilyClient

    return TavilyClient(api_key=api_key)
