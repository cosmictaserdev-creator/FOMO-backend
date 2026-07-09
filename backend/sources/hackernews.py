from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

HN_BASE = "https://hacker-news.firebaseio.com/v0"


def fetch(params: dict[str, Any]) -> list[dict[str, Any]]:
    story_type = params.get("type", "top")
    limit = min(params.get("limit", 30), 100)

    resp = requests.get(f"{HN_BASE}/{story_type}stories.json", timeout=15)
    resp.raise_for_status()
    ids = resp.json()[:limit]

    items: list[dict[str, Any]] = []
    for item_id in ids:
        try:
            r = requests.get(f"{HN_BASE}/item/{item_id}.json", timeout=10)
            r.raise_for_status()
            data = r.json()
            if not data or data.get("type") != "story":
                continue
            published = datetime.fromtimestamp(data.get("time", 0), tz=timezone.utc)
            items.append({
                "source": "hackernews",
                "title": data.get("title", ""),
                "url": data.get("url", f"https://news.ycombinator.com/item?id={item_id}"),
                "text_content": (data.get("text") or "")[:1000],
                "published_at": published.isoformat(),
            })
        except Exception:
            continue

    return items
