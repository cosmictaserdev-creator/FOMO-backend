from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests


def fetch(params: dict[str, Any]) -> list[dict[str, Any]]:
    instance = params.get("instance", "https://mastodon.social").rstrip("/")
    limit = min(params.get("limit", 20), 20)  # API max is 20

    resp = requests.get(f"{instance}/api/v1/trends/links",
                        params={"limit": limit},
                        headers={"User-Agent": "trend-hopper/0.1"}, timeout=15)
    resp.raise_for_status()

    now = datetime.now(timezone.utc).isoformat()
    items: list[dict[str, Any]] = []
    for link in resp.json():
        if not link.get("url"):
            continue
        items.append({
            "source": "mastodon",
            "title": link.get("title") or link["url"],
            "url": link["url"],
            "text_content": (link.get("description") or "")[:1000],
            "image_url": link.get("image"),
            "published_at": now,
        })

    return items
