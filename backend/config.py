from __future__ import annotations

import time
from typing import Any

import db

_CACHE: dict[str, Any] = {}
_CACHE_TTL = 60


def _cached(key: str, fetcher):
    now = time.monotonic()
    if key in _CACHE:
        val, ts = _CACHE[key]
        if now - ts < _CACHE_TTL:
            return val
    val = fetcher()
    _CACHE[key] = (val, now)
    return val


def _invalidate_cache(key: str | None = None) -> None:
    if key:
        _CACHE.pop(key, None)
    else:
        _CACHE.clear()


def load_settings() -> dict[str, str]:
    rows = db.get_supabase().table("settings").select("*").execute()
    return {r["key"]: r["value"] for r in (rows.data or [])}


def get_setting(key: str, default: str | None = None) -> str | None:
    return load_settings().get(key, default)


def load_active_topics() -> list[str]:
    rows = db.get_supabase().table("topics").select("name").eq("active", True).execute()
    return [r["name"] for r in (rows.data or [])]


def load_enabled_sources() -> list[dict[str, Any]]:
    rows = db.get_supabase().table("sources_config").select("*").eq("enabled", True).execute()
    return rows.data or []


def load_relevance_threshold() -> int:
    val = get_setting("RELEVANCE_THRESHOLD", "50")
    return max(0, min(100, int(val)))


def load_viral_keep_count() -> int:
    val = get_setting("VIRAL_KEEP_COUNT", "5")
    return max(1, int(val))


def load_retention_days() -> int:
    val = get_setting("RETENTION_DAYS", "30")
    return max(1, int(val))
