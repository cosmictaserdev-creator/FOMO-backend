from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

import config
import db

mcp = FastMCP("Trend Hopper")


@mcp.tool()
def get_settings() -> dict[str, str]:
    return config.load_settings()


@mcp.tool()
def list_topics() -> list[str]:
    return config.load_active_topics()


@mcp.tool()
def list_sources() -> list[dict[str, Any]]:
    rows = db.get_supabase().table("sources_config").select("name,enabled,params").execute()
    return rows.data or []


@mcp.tool()
def add_topic(name: str) -> str:
    existing = db.get_supabase().table("topics").select("id").eq("name", name).execute()
    if existing.data:
        return f"Topic '{name}' already exists."
    db.get_supabase().table("topics").insert({"name": name, "active": True}).execute()
    config._invalidate_cache()
    return f"Topic '{name}' added."


@mcp.tool()
def remove_topic(name: str) -> str:
    db.get_supabase().table("topics").delete().eq("name", name).execute()
    config._invalidate_cache()
    return f"Topic '{name}' removed."


@mcp.tool()
def toggle_source(source_name: str, enabled: bool) -> str:
    db.get_supabase().table("sources_config").update({"enabled": enabled}).eq("name", source_name).execute()
    config._invalidate_cache()
    state = "enabled" if enabled else "disabled"
    return f"Source '{source_name}' {state}."


@mcp.tool()
def update_source_params(source_name: str, params: dict[str, Any]) -> str:
    db.get_supabase().table("sources_config").update({"params": params}).eq("name", source_name).execute()
    config._invalidate_cache()
    return f"Source '{source_name}' params updated."


@mcp.tool()
def set_relevance_threshold(value: int) -> str:
    value = max(0, min(100, value))
    db.get_supabase().table("settings").update({"value": str(value)}).eq("key", "RELEVANCE_THRESHOLD").execute()
    config._invalidate_cache()
    return f"Relevance threshold set to {value}."


@mcp.tool()
def set_retention_days(days: int) -> str:
    days = max(1, days)
    db.get_supabase().table("settings").update({"value": str(days)}).eq("key", "RETENTION_DAYS").execute()
    config._invalidate_cache()
    return f"Retention days set to {days}."


@mcp.tool()
def set_schedule(time: str, timezone: str) -> str:
    db.get_supabase().table("settings").update({"value": time}).eq("key", "SCHEDULE_TIME").execute()
    db.get_supabase().table("settings").update({"value": timezone}).eq("key", "SCHEDULE_TIMEZONE").execute()
    config._invalidate_cache()
    return f"Schedule set to {time} {timezone}."


@mcp.tool()
def get_today_summary() -> dict[str, Any]:
    today = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).date().isoformat()
    items = db.get_supabase().table("items")\
        .select("id,source,title,relevance_score,viral_score,matched_topic,llm_summary")\
        .gte("fetched_at", today)\
        .order("relevance_score", desc=True)\
        .limit(10)\
        .execute()

    return {
        "count": len(items.data or []),
        "top_items": (items.data or [])[:5],
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
