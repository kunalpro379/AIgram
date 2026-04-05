"""Setup script to store API keys in MongoDB"""
import os
from dotenv import load_dotenv
from db.mongo import get_db

# Load environment variables
load_dotenv()

def setup_api_keys():
    """Store API keys in MongoDB"""
    db = get_db()
    
    # Get API keys from .env
    groq_key = os.getenv("GROQ_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    if not groq_key:
        print("[ERROR] GROQ_API_KEY not found in .env file!")
        return
    
    # Store in MongoDB
    config_collection = db.config
    
    # Update or insert GROQ API key
    config_collection.update_one(
        {"key": "GROQ_API_KEY"},
        {"$set": {"value": groq_key, "description": "Groq API Key for LLM"}},
        upsert=True
    )
    print(f"[OK] GROQ_API_KEY stored in MongoDB (length: {len(groq_key)} chars)")
    
    # Update or insert TAVILY API key if exists
    if tavily_key:
        config_collection.update_one(
            {"key": "TAVILY_API_KEY"},
            {"$set": {"value": tavily_key, "description": "Tavily API Key for web search"}},
            upsert=True
        )
        print(f"[OK] TAVILY_API_KEY stored in MongoDB (length: {len(tavily_key)} chars)")
    
    print("\n[SUCCESS] API keys successfully stored in MongoDB!")
    print("You can now run the application without .env file")

if __name__ == "__main__":
    print("🔧 Setting up API keys in MongoDB...\n")
    setup_api_keys()
