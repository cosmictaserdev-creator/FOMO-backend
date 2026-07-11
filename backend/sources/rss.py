from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import feedparser


def _extract_image(entry: Any) -> str | None:
    """Best-effort image from RSS media tags / enclosures."""
    for key in ("media_thumbnail", "media_content"):
        media = entry.get(key)
        if isinstance(media, list) and media:
            url = media[0].get("url")
            if url:
                return url
    for link in entry.get("links", []):
        if link.get("rel") == "enclosure" and str(link.get("type", "")).startswith("image"):
            if link.get("href"):
                return link["href"]
    # Some feeds embed an <img> in the summary/content HTML
    html = entry.get("summary") or entry.get("description") or ""
    match = re.search(r'<img[^>]+src="([^"]+)"', html)
    if match:
        return match.group(1)
    return None


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
                    "image_url": _extract_image(entry),
                    "published_at": dt.isoformat(),
                })
        except Exception:
            continue

    return items
