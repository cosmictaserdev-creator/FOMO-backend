from __future__ import annotations

import sys
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


def _supabase_or_none():
    supa = db.get_supabase()
    if not supa:
        print("Supabase not configured; returning empty config", file=sys.stderr)
    return supa


def load_settings() -> dict[str, str]:
    supa = _supabase_or_none()
    if not supa:
        return {}
    rows = supa.table("settings").select("*").execute()
    return {r["key"]: r["value"] for r in (rows.data or [])}


def get_setting(key: str, default: str | None = None) -> str | None:
    return load_settings().get(key, default)


def load_active_topics() -> list[str]:
    supa = _supabase_or_none()
    if not supa:
        return []
    rows = supa.table("topics").select("name").eq("active", True).execute()
    return [r["name"] for r in (rows.data or [])]


def load_enabled_sources() -> list[dict[str, Any]]:
    supa = _supabase_or_none()
    if not supa:
        return []
    rows = supa.table("sources_config").select("*").eq("enabled", True).execute()
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
    supa = _supabase_or_none()
    if not supa:
        return []
    rows = supa.table("sources_config").select("name,enabled,params").execute()
    return rows.data or []


def add_topic(name: str) -> str:
    supa = _supabase_or_none()
    if not supa:
        return "Supabase not configured; cannot add topic."
    existing = supa.table("topics").select("id").eq("name", name).execute()
    if existing.data:
        return f"Topic '{name}' already exists."
    supa.table("topics").insert({"name": name, "active": True}).execute()
    _invalidate_cache()
    return f"Topic '{name}' added."


def remove_topic(name: str) -> str:
    supa = _supabase_or_none()
    if not supa:
        return "Supabase not configured; cannot remove topic."
    supa.table("topics").delete().eq("name", name).execute()
    _invalidate_cache()
    return f"Topic '{name}' removed."


def toggle_source(source_name: str, enabled: bool) -> str:
    supa = _supabase_or_none()
    if not supa:
        return "Supabase not configured; cannot toggle source."
    supa.table("sources_config").update({"enabled": enabled}).eq("name", source_name).execute()
    _invalidate_cache()
    state = "enabled" if enabled else "disabled"
    return f"Source '{source_name}' {state}."


def update_source_params(source_name: str, params: dict[str, Any]) -> str:
    supa = _supabase_or_none()
    if not supa:
        return "Supabase not configured; cannot update source params."
    supa.table("sources_config").update({"params": params}).eq("name", source_name).execute()
    _invalidate_cache()
    return f"Source '{source_name}' params updated."


def set_relevance_threshold(value: int) -> str:
    supa = _supabase_or_none()
    if not supa:
        return "Supabase not configured; cannot set relevance threshold."
    value = max(0, min(100, value))
    supa.table("settings").update({"value": str(value)}).eq("key", "RELEVANCE_THRESHOLD").execute()
    _invalidate_cache()
    return f"Relevance threshold set to {value}."


def set_retention_days(days: int) -> str:
    supa = _supabase_or_none()
    if not supa:
        return "Supabase not configured; cannot set retention days."
    days = max(1, days)
    supa.table("settings").update({"value": str(days)}).eq("key", "RETENTION_DAYS").execute()
    _invalidate_cache()
    return f"Retention days set to {days}."


def set_schedule(time_str: str, tz: str) -> str:
    supa = _supabase_or_none()
    if not supa:
        return "Supabase not configured; cannot set schedule."
    supa.table("settings").update({"value": time_str}).eq("key", "SCHEDULE_TIME").execute()
    supa.table("settings").update({"value": tz}).eq("key", "SCHEDULE_TIMEZONE").execute()
    _invalidate_cache()
    return f"Schedule set to {time_str} {tz}."


def get_today_summary() -> dict[str, Any]:
    supa = _supabase_or_none()
    if not supa:
        return {"count": 0, "top_items": []}
    today = datetime.now(timezone.utc).date().isoformat()
    items = supa.table("items") \
        .select("id,source,title,relevance_score,viral_score,matched_topic,llm_summary") \
        .gte("fetched_at", today) \
        .order("relevance_score", desc=True) \
        .limit(10) \
        .execute()

    return {
        "count": len(items.data or []),
        "top_items": (items.data or [])[:5],
    }
