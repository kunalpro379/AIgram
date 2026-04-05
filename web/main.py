"""
AIgram - AI Social Network Platform
Run with:
  python main.py web      - Start API server only
  python main.py agents   - Start agents orchestrator only
  python main.py          - Start both (default)
"""
import sys
import asyncio
from API.social_server import app

def start_web_server():
    """Start the FastAPI web server"""
    import uvicorn
    import os
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print("[START] Starting AIgram API Server...")
    print(f"[SERVER] Server: http://{host}:{port}")
    print(f"[DOCS] API Docs: http://{host}:{port}/docs")
    print(f"[AGENT] Start agents: POST http://{host}:{port}/api/orchestrator/start")
    
    uvicorn.run("main:app", host=host, port=port, reload=True)


async def start_agents_only():
    """Start the agents orchestrator without web server"""
    from agents.orchestrator import AgentOrchestrator
    
    print("[AGENT] Starting AIgram Agents Orchestrator...")
    print("[INIT] Initializing 30 AI agents...")
    
    orchestrator = AgentOrchestrator(max_agents=100)
    await orchestrator.initialize_agents(count=30)
    
    print("[OK] Agents initialized!")
    print("[LOOP] Starting agent activity loop...")
    
    await orchestrator.start()


def start_both():
    """Start both web server and agents (not recommended for production)"""
    import uvicorn
    import os
    from threading import Thread
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print("[START] Starting AIgram - Full Platform...")
    print(f"[SERVER] API Server: http://{host}:{port}")
    print(f"[AGENT] Agents: Will auto-start via API")
    print("\n[WARN]  For production, run 'web' and 'agents' separately!")
    
    uvicorn.run("main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "web"
    
    if mode == "web":
        start_web_server()
    elif mode == "agents":
        asyncio.run(start_agents_only())
    elif mode == "both":
        start_both()
    else:
        print("[ERROR] Invalid mode. Use: python main.py [web|agents|both]")
        print("\nExamples:")
        print("  python main.py web      - Start API server only")
        print("  python main.py agents   - Start agents orchestrator only")
        print("  python main.py both     - Start both (not recommended)")
        sys.exit(1)


