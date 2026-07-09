from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests


def fetch(params: dict[str, Any]) -> list[dict[str, Any]]:
    genre = params.get("genre", "electronic")
    limit = min(params.get("limit", 10), 50)

    url = "https://api-v2.soundcloud.com/charts"
    resp = requests.get(url, params={
        "kind": "trending",
        "genre": genre,
        "limit": limit,
    }, headers={
        "User-Agent": "trend-hopper/0.1",
        "Accept": "application/json",
    }, timeout=15)

    if resp.status_code != 200:
        return []

    data = resp.json()
    items: list[dict[str, Any]] = []

    for entry in data.get("data", data.get("collection", [])):
        track = entry.get("track") or entry
        if not track or not track.get("title"):
            continue
        published = track.get("created_at") or track.get("release_date")
        if published:
            try:
                dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            except Exception:
                dt = datetime.now(timezone.utc)
        else:
            dt = datetime.now(timezone.utc)
        items.append({
            "source": "soundcloud",
            "title": track.get("title", ""),
            "url": track.get("permalink_url", track.get("uri", "")),
            "text_content": (track.get("description") or "")[:1000],
            "published_at": dt.isoformat(),
        })

    return items
