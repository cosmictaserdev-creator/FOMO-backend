from __future__ import annotations

import importlib
import os
import sys
import traceback
from typing import Any

import config
import db


_REQUIRED_ENV: dict[str, list[str]] = {
    "reddit": ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"],
    "youtube": ["YOUTUBE_API_KEY"],
}


def run() -> dict[str, Any]:
    db.log_sync_status("syncing")
    try:
        sources = config.load_enabled_sources()
        if not sources:
            db.log_sync_status("failed", error_reason="no_enabled_sources")
            return {"status": "failed", "reason": "no_enabled_sources"}

        total = 0
        errors: list[str] = []
        skipped: list[str] = []

        for src in sources:
            name: str = src["name"]
            params: dict = src.get("params", {})

            missing = [v for v in _REQUIRED_ENV.get(name, []) if not os.environ.get(v)]
            if missing:
                skipped.append(f"{name} (missing: {', '.join(missing)})")
                continue

            try:
                module = importlib.import_module(f"sources.{name}")
                items = module.fetch(params)
                count = db.upsert_items(items)
                total += count
            except ModuleNotFoundError:
                errors.append(f"{name}: source module not found")
            except Exception as e:
                tb = traceback.format_exc()
                errors.append(f"{name}: {e}")
                print(tb, file=sys.stderr)

        if errors:
            db.log_sync_status("failed", error_reason="; ".join(errors))
        else:
            db.log_sync_status("synced")

        return {
            "status": "synced" if not errors else "failed",
            "new_items": total,
            "errors": errors,
            "skipped": skipped,
        }
    except Exception as e:
        reason = _classify_error(e)
        db.log_sync_status("failed", error_reason=reason)
        return {"status": "failed", "reason": reason}


def _classify_error(e: Exception) -> str:
    msg = str(e).lower()
    if "401" in msg or "403" in msg or "unauthorized" in msg or "invalid key" in msg:
        return "invalid_api_key"
    if "429" in msg or "rate limit" in msg:
        return "rate_limited"
    if "timeout" in msg or "connection" in msg or "resolve" in msg:
        return "network_timeout"
    return "unknown"


if __name__ == "__main__":
    import json
    result = run()
    print(json.dumps(result, indent=2))
    if result.get("status") == "failed":
        sys.exit(1)
