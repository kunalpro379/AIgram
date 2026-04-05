from datetime import datetime, timezone
from typing import Any, Dict, List

from bson import ObjectId

from db.mongo import get_db


def _oid(value: str) -> ObjectId:
    return ObjectId(value)


def _serialize_id(doc: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(doc)
    out["id"] = str(out.pop("_id"))
    return out


def list_arenas() -> List[Dict[str, Any]]:
    db = get_db()
    rows = list(db.arenas.find().sort("created_at", -1))
    return [_serialize_id(row) for row in rows]


def create_arena(data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    payload = {
        "name": data["name"],
        "creator_name": data["creator_name"],
        "description": data.get("description", ""),
        "image_url": data.get("image_url", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = db.arenas.insert_one(payload)
    payload["_id"] = result.inserted_id
    return _serialize_id(payload)


def arena_exists(arena_id: str) -> bool:
    db = get_db()
    return db.arenas.count_documents({"_id": _oid(arena_id)}, limit=1) > 0


def save_debate_run(arena_id: str, run_doc: Dict[str, Any]) -> str:
    db = get_db()
    payload = dict(run_doc)
    payload["arena_id"] = _oid(arena_id)
    payload["created_at"] = datetime.now(timezone.utc).isoformat()
    result = db.debate_runs.insert_one(payload)
    return str(result.inserted_id)


def list_arena_runs(arena_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    db = get_db()
    rows = list(
        db.debate_runs.find({"arena_id": _oid(arena_id)}).sort("created_at", -1).limit(limit)
    )
    output: List[Dict[str, Any]] = []
    for row in rows:
        row = _serialize_id(row)
        row["arena_id"] = str(row["arena_id"])
        output.append(row)
    return output

