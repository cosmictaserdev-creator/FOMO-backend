from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests


def fetch(params: dict[str, Any]) -> list[dict[str, Any]]:
    limit = min(params.get("limit", 25), 50)

    resp = requests.get("https://lobste.rs/hottest.json",
                        headers={"User-Agent": "trend-hopper/0.1"}, timeout=15)
    resp.raise_for_status()

    items: list[dict[str, Any]] = []
    for story in resp.json()[:limit]:
        try:
            dt = datetime.fromisoformat(story["created_at"])
        except Exception:
            dt = datetime.now(timezone.utc)
        tags = ", ".join(story.get("tags", []))
        description = story.get("description_plain") or story.get("description") or ""
        items.append({
            "source": "lobsters",
            "title": story.get("title", ""),
            "url": story.get("url") or story.get("comments_url", ""),
            "text_content": (description or tags)[:1000],
            "published_at": dt.isoformat(),
        })

    return items
