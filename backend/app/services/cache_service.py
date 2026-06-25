import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional


CACHE_ROOT = Path("cache")


def make_cache_key(*parts: str) -> str:
    raw = ":".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()


def get_cache_path(namespace: str, key: str) -> Path:
    return CACHE_ROOT / namespace / f"{key}.json"


def read_json_cache(
    namespace: str,
    key: str,
    ttl_seconds: Optional[int] = None,
) -> Optional[Any]:
    path = get_cache_path(namespace, key)

    try:
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except Exception:
        return None

    if ttl_seconds is not None:
        created_at = payload.get("created_at", 0)
        if time.time() - created_at > ttl_seconds:
            return None

    return payload.get("data")


def write_json_cache(namespace: str, key: str, data: Any) -> None:
    path = get_cache_path(namespace, key)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"created_at": time.time(), "data": data}
        path.write_text(json.dumps(payload), encoding="utf-8")
    except Exception:
        pass
