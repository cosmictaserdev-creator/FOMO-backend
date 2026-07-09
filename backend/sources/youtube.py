from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import requests


def fetch(params: dict[str, Any]) -> list[dict[str, Any]]:
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        return []

    query = params.get("query", "tech news")
    max_results = min(params.get("max_results", 10), 50)

    url = "https://www.googleapis.com/youtube/v3/search"
    resp = requests.get(url, params={
        "part": "snippet",
        "q": query,
        "maxResults": max_results,
        "type": "video",
        "order": "date",
        "key": api_key,
    }, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    items: list[dict[str, Any]] = []
    for item in data.get("items", []):
        snippet = item.get("snippet", {})
        video_id = item.get("id", {}).get("videoId")
        if not video_id:
            continue
        published = snippet.get("publishedAt")
        if published:
            dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        else:
            dt = datetime.now(timezone.utc)
        items.append({
            "source": "youtube",
            "title": snippet.get("title", ""),
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "text_content": (snippet.get("description") or "")[:1000],
            "published_at": dt.isoformat(),
        })

    return items
