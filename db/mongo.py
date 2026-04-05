import os
from functools import lru_cache
from pathlib import Path

from pymongo import MongoClient


def _load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    loaded_any = False
    if not env_path.exists():
        print(f"[env-debug] .env file not found at {env_path}")
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
            loaded_any = True
    print(f"[env-debug] .env file found at {env_path}; loaded_new_keys={loaded_any}")


def _log_env_presence() -> None:
    # Log only existence flags; never print secret values.
    print(
        "[env-debug] MONGODB_URI_present="
        f"{bool(os.getenv('MONGODB_URI', '').strip())}, "
        "MONGODB_DB_NAME_present="
        f"{bool(os.getenv('MONGODB_DB_NAME', '').strip())}"
    )


@lru_cache(maxsize=1)
def get_db():
    _load_env_file()
    _log_env_presence()
    uri = os.getenv("MONGODB_URI", "").strip()
    if not uri:
        raise RuntimeError("Missing MONGODB_URI in environment.")
    db_name = os.getenv("MONGODB_DB_NAME", "agents_battleground").strip()
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    return client[db_name]

