from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import feedparser


def fetch(params: dict[str, Any]) -> list[dict[str, Any]]:
    feeds: list[str] = params.get("feeds", [])
    limit: int = min(params.get("limit", 20), 50)

    items: list[dict[str, Any]] = []
    for feed_url in feeds:
        try:
            parsed = feedparser.parse(feed_url)
            for entry in parsed.entries[:limit]:
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                if published:
                    dt = datetime(*published[:6], tzinfo=timezone.utc)
                else:
                    dt = datetime.now(timezone.utc)
                items.append({
                    "source": "rss",
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "text_content": (entry.get("summary") or entry.get("description") or "")[:1000],
                    "published_at": dt.isoformat(),
                })
        except Exception:
            continue

    return items
