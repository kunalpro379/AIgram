from pathlib import Path
from typing import Any, Dict

import asyncio
import traceback

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response

from db.repositories import arena_exists, create_arena, list_arena_runs, list_arenas, save_debate_run
from states.debate import ArenaCreateRequest, DebateRequest
from workflow.graph import run


app = FastAPI(title="Agents Battleground API", version="1.0.0")


@app.middleware("http")
async def normalize_double_slash_paths(request: Request, call_next):
    # Some deployments/browsers may hit "//" accidentally; normalize to "/".
    path = request.scope.get("path", "")
    if path.startswith("//"):
        request.scope["path"] = "/" + path.lstrip("/")
    return await call_next(request)


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    html_path = Path(__file__).parent / "web" / "index.html"
    if not html_path.exists():
        return "<h3>UI missing. Create api/web/index.html</h3>"
    return html_path.read_text(encoding="utf-8")


@app.get("/backend-check")
def backend_check() -> Dict[str, Any]:
    return {"ok": True}


@app.get("/favicon.ico")
def favicon() -> Response:
    # Keep browser from emitting noisy 404s in logs/console.
    return Response(status_code=204)


@app.post("/api/debate")
def debate(payload: DebateRequest) -> Dict[str, Any]:
    result = run(
        topic=payload.topic.strip(),
        preferred_language=payload.preferred_language,
        user_location=payload.user_location,
        user_background=payload.user_background,
        max_cycles=payload.max_cycles,
        members_per_team=payload.members_per_team,
    )
    return {"ok": True, "result": result}


@app.get("/api/arenas")
def get_arenas() -> Dict[str, Any]:
    try:
        return {"ok": True, "arenas": list_arenas()}
    except Exception as exc:
        # Keep UI usable even if DB temporarily unavailable.
        return {"ok": False, "arenas": [], "error": f"Arena fetch failed: {exc}"}


@app.post("/api/arenas")
def post_arena(payload: ArenaCreateRequest) -> Dict[str, Any]:
    try:
        arena = create_arena(payload.model_dump())
        return {"ok": True, "arena": arena}
    except Exception as exc:
        print(f"[arena-debug] create_arena failed: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Arena create failed: {exc}") from exc


@app.get("/api/arenas/{arena_id}/runs")
def get_arena_runs(arena_id: str) -> Dict[str, Any]:
    try:
        runs = list_arena_runs(arena_id, limit=20)
        return {"ok": True, "runs": runs}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Arena runs fetch failed: {exc}") from exc


@app.websocket("/ws/debate")
async def debate_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            topic = str(payload.get("topic", "")).strip()
            arena_id = str(payload.get("arena_id", "")).strip()
            if not topic:
                await websocket.send_json({"type": "error", "message": "Topic is required."})
                continue
            max_cycles = int(payload.get("max_cycles", 1))
            members_per_team = int(payload.get("members_per_team", 3))
            preferred_language = str(payload.get("preferred_language", "English"))
            user_location = str(payload.get("user_location", ""))
            user_background = str(payload.get("user_background", ""))
            stream_events: list[dict] = []

            if arena_id:
                try:
                    if not arena_exists(arena_id):
                        await websocket.send_json({"type": "error", "message": "Arena not found."})
                        continue
                except Exception as exc:
                    await websocket.send_json({"type": "error", "message": f"Arena check failed: {exc}"})
                    continue

            loop = asyncio.get_running_loop()
            queue: asyncio.Queue[dict] = asyncio.Queue()

            def push_event(event: dict) -> None:
                loop.call_soon_threadsafe(queue.put_nowait, event)

            run_task = asyncio.create_task(
                asyncio.to_thread(
                    run,
                    topic,
                    preferred_language,
                    user_location,
                    user_background,
                    max_cycles,
                    members_per_team,
                    push_event,
                )
            )

            while True:
                if run_task.done() and queue.empty():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=0.2)
                    stream_events.append(event)
                    await websocket.send_json(event)
                except asyncio.TimeoutError:
                    continue

            result = await run_task
            if arena_id:
                try:
                    save_debate_run(
                        arena_id,
                        {
                            "topic": topic,
                            "profile": {
                                "preferred_language": preferred_language,
                                "user_location": user_location,
                                "user_background": user_background,
                            },
                            "config": {
                                "max_cycles": max_cycles,
                                "members_per_team": members_per_team,
                            },
                            "stream_events": stream_events,
                            "result": result,
                        },
                    )
                except Exception as exc:
                    await websocket.send_json({"type": "error", "message": f"Save failed: {exc}"})
            await websocket.send_json({"type": "run_complete", "result": result})
    except WebSocketDisconnect:
        return

