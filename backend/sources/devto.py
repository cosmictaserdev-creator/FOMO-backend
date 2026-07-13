from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests


def fetch(params: dict[str, Any]) -> list[dict[str, Any]]:
    limit = min(params.get("limit", 20), 100)
    tag = params.get("tag", "")

    query: dict[str, Any] = {"top": 1, "per_page": limit}
    if tag:
        query["tag"] = tag

    resp = requests.get("https://dev.to/api/articles", params=query,
                        headers={"User-Agent": "trend-hopper/0.1"}, timeout=15)
    resp.raise_for_status()

    items: list[dict[str, Any]] = []
    for article in resp.json():
        published = article.get("published_at")
        try:
            dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now(timezone.utc)
        items.append({
            "source": "devto",
            "title": article.get("title", ""),
            "url": article.get("url", ""),
            "text_content": (article.get("description") or "")[:1000],
            "image_url": article.get("cover_image"),
            "published_at": dt.isoformat(),
        })

    return items
