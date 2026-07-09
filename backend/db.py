import os
import hashlib
from typing import Any
from datetime import datetime, timezone

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

_SUPABASE: Client | None = None


def get_supabase() -> Client:
    global _SUPABASE
    if _SUPABASE is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_KEY"]
        _SUPABASE = create_client(url, key)
    return _SUPABASE


def content_hash(url: str, title: str) -> str:
    raw = f"{url.strip().lower()}|{title.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def upsert_items(items: list[dict[str, Any]]) -> int:
    if not items:
        return 0
    for item in items:
        item["content_hash"] = content_hash(item["url"], item["title"])
        item["never_favorited"] = True
    data = get_supabase().table("items").upsert(
        items,
        on_conflict="content_hash",
        ignore_duplicates=True,
    ).execute()
    return len(data.data) if data.data else 0


def log_sync_status(
    status: str,
    error_reason: str | None = None,
    last_successful: datetime | None = None,
) -> None:
    if last_successful is None and status == "synced":
        last_successful = datetime.now(timezone.utc)
    get_supabase().table("sync_log").insert({
        "status": status,
        "last_error_reason": error_reason,
        "last_successful_sync_at": last_successful.isoformat() if last_successful else None,
    }).execute()
