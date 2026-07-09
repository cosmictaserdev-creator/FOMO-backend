from __future__ import annotations

import traceback
from typing import Any

import backend_path  # noqa: F401 -- must run before backend imports below

import collector
import config
import filter as filter_module

import mcp_config
import secrets_store
from ktor_manager import KtorManager, pipeline_trigger_env
from scheduler import Scheduler, log_buffer as _scheduler_log_buffer

_ktor = KtorManager(port=8080)
scheduler = Scheduler()


class ApiBridge:
    """Exposed to the webview's JS as `window.pywebview.api.*`."""

    # -- Setup screen --------------------------------------------------

    def get_env_status(self) -> dict[str, Any]:
        env = secrets_store.load_env()
        missing = [k for k in secrets_store.REQUIRED_KEYS if not env.get(k, "").strip()]
        return {"saved": len(missing) == 0, "values": env}

    def save_env(self, data: dict[str, str]) -> dict[str, Any]:
        missing = secrets_store.save_env(data)
        if missing:
            return {"ok": False, "error": f"Missing: {', '.join(missing)}"}
        return {"ok": True}

    def run_collector(self) -> dict[str, Any]:
        try:
            return {"ok": True, "result": collector.run()}
        except Exception as e:
            return {"ok": False, "error": str(e), "trace": traceback.format_exc()}

    def run_filter(self) -> dict[str, Any]:
        try:
            return {"ok": True, "result": filter_module.run()}
        except Exception as e:
            return {"ok": False, "error": str(e), "trace": traceback.format_exc()}

    # -- Settings screen (direct Supabase reads/writes, same tables Ktor/MCP use) ----

    def get_settings(self) -> dict[str, Any]:
        return {
            "threshold": config.load_relevance_threshold(),
            "retention_days": config.load_retention_days(),
            "viral_keep_count": config.load_viral_keep_count(),
            "schedule_time": config.get_setting("SCHEDULE_TIME", "06:00"),
            "schedule_timezone": config.get_setting("SCHEDULE_TIMEZONE", "UTC"),
            "topics": config.load_active_topics(),
            "sources": config.list_all_sources(),
        }

    def set_relevance_threshold(self, value: int) -> dict[str, Any]:
        return {"ok": True, "message": config.set_relevance_threshold(int(value))}

    def set_retention_days(self, days: int) -> dict[str, Any]:
        return {"ok": True, "message": config.set_retention_days(int(days))}

    def set_schedule(self, time_str: str, tz: str) -> dict[str, Any]:
        return {"ok": True, "message": config.set_schedule(time_str, tz)}

    def add_topic(self, name: str) -> dict[str, Any]:
        return {"ok": True, "message": config.add_topic(name)}

    def remove_topic(self, name: str) -> dict[str, Any]:
        return {"ok": True, "message": config.remove_topic(name)}

    def toggle_source(self, source_name: str, enabled: bool) -> dict[str, Any]:
        return {"ok": True, "message": config.toggle_source(source_name, bool(enabled))}

    # -- Dashboard: Ktor server lifecycle -------------------------------

    def start_server(self) -> dict[str, Any]:
        env = secrets_store.load_env()
        missing = [k for k in secrets_store.REQUIRED_KEYS if not env.get(k, "").strip()]
        if missing:
            return {"ok": False, "error": f"Save API keys first (missing: {', '.join(missing)})"}
        run_env = {
            "SUPABASE_URL": env["SUPABASE_URL"],
            "SUPABASE_KEY": env["SUPABASE_KEY"],
            "GROQ_API_KEY": env["GROQ_API_KEY"],
            "API_AUTH_TOKEN": secrets_store.get_or_create_api_auth_token(),
            **pipeline_trigger_env(),
        }
        return _ktor.start(run_env)

    def stop_server(self) -> dict[str, Any]:
        return _ktor.stop()

    def server_status(self) -> dict[str, Any]:
        return _ktor.status()

    def server_logs(self) -> list[str]:
        return _ktor.logs()

    # -- Pipeline: manual run + scheduler log tail ----------------------

    def run_pipeline_now(self) -> dict[str, Any]:
        scheduler.run_now()
        return {"ok": True}

    def pipeline_logs(self) -> list[str]:
        return list(_scheduler_log_buffer)[-200:]

    # -- MCP tab: ready-to-paste Claude Desktop config -------------------

    def get_mcp_config(self) -> dict[str, Any]:
        return {
            "config_json": mcp_config.build_claude_desktop_config_json(),
            "tools": [
                "get_settings", "list_topics", "list_sources",
                "add_topic", "remove_topic", "toggle_source", "update_source_params",
                "set_relevance_threshold", "set_retention_days", "set_schedule",
                "get_today_summary",
            ],
        }
