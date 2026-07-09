from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

import config

mcp = FastMCP("Trend Hopper")


@mcp.tool()
def get_settings() -> dict[str, str]:
    return config.load_settings()


@mcp.tool()
def list_topics() -> list[str]:
    return config.load_active_topics()


@mcp.tool()
def list_sources() -> list[dict[str, Any]]:
    return config.list_all_sources()


@mcp.tool()
def add_topic(name: str) -> str:
    return config.add_topic(name)


@mcp.tool()
def remove_topic(name: str) -> str:
    return config.remove_topic(name)


@mcp.tool()
def toggle_source(source_name: str, enabled: bool) -> str:
    return config.toggle_source(source_name, enabled)


@mcp.tool()
def update_source_params(source_name: str, params: dict[str, Any]) -> str:
    return config.update_source_params(source_name, params)


@mcp.tool()
def set_relevance_threshold(value: int) -> str:
    return config.set_relevance_threshold(value)


@mcp.tool()
def set_retention_days(days: int) -> str:
    return config.set_retention_days(days)


@mcp.tool()
def set_schedule(time: str, timezone: str) -> str:
    return config.set_schedule(time, timezone)


@mcp.tool()
def get_today_summary() -> dict[str, Any]:
    return config.get_today_summary()


if __name__ == "__main__":
    mcp.run(transport="stdio")
