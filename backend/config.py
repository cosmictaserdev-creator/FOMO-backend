from __future__ import annotations

import time
from datetime import datetime, timezone
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


def list_all_sources() -> list[dict[str, Any]]:
    rows = db.get_supabase().table("sources_config").select("name,enabled,params").execute()
    return rows.data or []


def add_topic(name: str) -> str:
    existing = db.get_supabase().table("topics").select("id").eq("name", name).execute()
    if existing.data:
        return f"Topic '{name}' already exists."
    db.get_supabase().table("topics").insert({"name": name, "active": True}).execute()
    _invalidate_cache()
    return f"Topic '{name}' added."


def remove_topic(name: str) -> str:
    db.get_supabase().table("topics").delete().eq("name", name).execute()
    _invalidate_cache()
    return f"Topic '{name}' removed."


def toggle_source(source_name: str, enabled: bool) -> str:
    db.get_supabase().table("sources_config").update({"enabled": enabled}).eq("name", source_name).execute()
    _invalidate_cache()
    state = "enabled" if enabled else "disabled"
    return f"Source '{source_name}' {state}."


def update_source_params(source_name: str, params: dict[str, Any]) -> str:
    db.get_supabase().table("sources_config").update({"params": params}).eq("name", source_name).execute()
    _invalidate_cache()
    return f"Source '{source_name}' params updated."


def set_relevance_threshold(value: int) -> str:
    value = max(0, min(100, value))
    db.get_supabase().table("settings").update({"value": str(value)}).eq("key", "RELEVANCE_THRESHOLD").execute()
    _invalidate_cache()
    return f"Relevance threshold set to {value}."


def set_retention_days(days: int) -> str:
    days = max(1, days)
    db.get_supabase().table("settings").update({"value": str(days)}).eq("key", "RETENTION_DAYS").execute()
    _invalidate_cache()
    return f"Retention days set to {days}."


def set_schedule(time_str: str, tz: str) -> str:
    db.get_supabase().table("settings").update({"value": time_str}).eq("key", "SCHEDULE_TIME").execute()
    db.get_supabase().table("settings").update({"value": tz}).eq("key", "SCHEDULE_TIMEZONE").execute()
    _invalidate_cache()
    return f"Schedule set to {time_str} {tz}."


def get_today_summary() -> dict[str, Any]:
    today = datetime.now(timezone.utc).date().isoformat()
    items = db.get_supabase().table("items") \
        .select("id,source,title,relevance_score,viral_score,matched_topic,llm_summary") \
        .gte("fetched_at", today) \
        .order("relevance_score", desc=True) \
        .limit(10) \
        .execute()

    return {
        "count": len(items.data or []),
        "top_items": (items.data or [])[:5],
    }
