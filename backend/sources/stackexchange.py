from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import Any

import requests


def fetch(params: dict[str, Any]) -> list[dict[str, Any]]:
    site = params.get("site", "stackoverflow")
    limit = min(params.get("limit", 20), 100)

    resp = requests.get("https://api.stackexchange.com/2.3/questions",
                        params={"order": "desc", "sort": "hot", "site": site,
                                "pagesize": limit},
                        headers={"User-Agent": "trend-hopper/0.1"}, timeout=15)
    resp.raise_for_status()

    items: list[dict[str, Any]] = []
    for q in resp.json().get("items", []):
        dt = datetime.fromtimestamp(q.get("creation_date", 0), tz=timezone.utc)
        tags = ", ".join(q.get("tags", []))
        items.append({
            "source": "stackexchange",
            "title": html.unescape(q.get("title", "")),
            "url": q.get("link", ""),
            "text_content": f"Hot question on {site}. Tags: {tags}. "
                            f"Score: {q.get('score', 0)}, answers: {q.get('answer_count', 0)}."[:1000],
            "published_at": dt.isoformat(),
        })

    return items
