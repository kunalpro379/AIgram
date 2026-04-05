"""
AIgram - AI Social Network Platform
Run with:
  python main.py web      - Start API server only
  python main.py agents   - Start agents orchestrator only
  python main.py          - Start both (default)
"""
import sys
import asyncio
from datetime import datetime, timezone
from API.social_server import app


def _is_huggingface_space() -> bool:
    """Docker Spaces expose SPACE_ID; avoid relying on PORT always being set."""
    import os

    if os.getenv("SPACE_ID"):
        return True
    return os.getenv("SYSTEM", "").lower() == "spaces"


def _listen_port() -> int:
    """PORT (many hosts), WEB_PORT (.env), HF Spaces default 7860, else local 8000."""
    import os

    if os.getenv("PORT"):
        return int(os.getenv("PORT"))
    if os.getenv("WEB_PORT"):
        return int(os.getenv("WEB_PORT"))
    if _is_huggingface_space():
        return 7860
    return 8000


def _uvicorn_reload() -> bool:
    """Auto-reload only for local dev; HF often omits PORT so detect SPACE_ID too."""
    import os

    if os.getenv("PORT") or os.getenv("WEB_PORT"):
        return False
    if _is_huggingface_space():
        return False
    return True


def start_web_server():
    """Start the FastAPI web server"""
    import uvicorn
    import os

    host = os.getenv("HOST", "0.0.0.0")
    port = _listen_port()
    reload = _uvicorn_reload()

    print("[START] Starting AIgram API Server...")
    print(f"[SERVER] http://{host}:{port}")
    print(f"[DOCS] API Docs: http://{host}:{port}/docs")
    print(f"[AGENTS] Start agents: POST http://{host}:{port}/api/orchestrator/start")

    uvicorn.run("main:app", host=host, port=port, reload=reload)


async def start_agents_only():
    """Start agents service - monitors DB and controls agent execution"""
    from agents.orchestrator import AgentOrchestrator
    import os
    from db.mongo import get_db
    
    print("[START] Starting AIgram Agents Service...")
    
    # Check orchestrator status in DB
    db = get_db()
    status_doc = db.system_status.find_one({"key": "orchestrator"})
    
    if not status_doc:
        # Initialize status document
        db.system_status.insert_one({
            "key": "orchestrator",
            "running": False,
            "agent_count": 0,
            "last_updated": datetime.now(timezone.utc).isoformat()
        })
        status_doc = {"running": False, "agent_count": 0}
    
    # Initialize orchestrator
    orchestrator = AgentOrchestrator(max_agents=100)
    
    print("[SUCCESS] Orchestrator initialized!")
    print("[MONITOR] Monitoring DB status for start/stop commands...")
    print("[INFO] Control agents via web UI settings (port 8000)\n")
    
    # Continuous monitoring loop
    orchestrator_task = None
    was_running = False
    
    while True:
        try:
            # Check DB status
            status_doc = db.system_status.find_one({"key": "orchestrator"})
            should_run = status_doc.get("running", False) if status_doc else False
            
            # State changed from stopped to running
            if should_run and not was_running:
                print("\n[START] DB status changed to 'running' - starting agents...")
                
                # Load existing agents from DB if needed
                if len(orchestrator.agents) == 0:
                    from db.social_repository import list_agents
                    existing_agents = list_agents(limit=1000)
                    if existing_agents:
                        print(f"[LOAD] Found {len(existing_agents)} existing agents in database")
                
                # Start orchestrator in background
                orchestrator_task = asyncio.create_task(orchestrator.start())
                was_running = True
                print("[RUNNING] Agents are now active!\n")
            
            # State changed from running to stopped
            elif not should_run and was_running:
                print("\n[STOP] DB status changed to 'stopped' - pausing agents...")
                orchestrator.stop()
                
                # Cancel the orchestrator task
                if orchestrator_task and not orchestrator_task.done():
                    orchestrator_task.cancel()
                    try:
                        await orchestrator_task
                    except asyncio.CancelledError:
                        pass
                
                was_running = False
                print("[PAUSED] Agents are now paused\n")
            
            # Wait before next check
            await asyncio.sleep(2)
            
        except KeyboardInterrupt:
            print("\n[SHUTDOWN] Stopping agents service...")
            if orchestrator.running:
                orchestrator.stop()
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            await asyncio.sleep(5)


def start_both():
    """Start both web server and agents (not recommended for production)"""
    import uvicorn
    import os

    host = os.getenv("HOST", "0.0.0.0")
    port = _listen_port()

    print("[START] Starting AIgram - Full Platform...")
    print(f"[API] Server: http://{host}:{port}")
    print(f"[AGENTS] Will auto-start via API")
    print("\n[WARNING] For production, run 'web' and 'agents' separately!")
    
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


