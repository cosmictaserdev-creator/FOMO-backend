from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import feedparser


def fetch(params: dict[str, Any]) -> list[dict[str, Any]]:
    categories: list[str] = params.get("categories", ["cs.AI", "cs.LG"])
    limit = min(params.get("limit", 20), 50)

    search = "+OR+".join(f"cat:{c}" for c in categories)
    url = (
        "http://export.arxiv.org/api/query"
        f"?search_query={search}&sortBy=submittedDate&sortOrder=descending"
        f"&max_results={limit}"
    )
    parsed = feedparser.parse(url)

    items: list[dict[str, Any]] = []
    for entry in parsed.entries:
        published = entry.get("published_parsed")
        if published:
            dt = datetime(*published[:6], tzinfo=timezone.utc)
        else:
            dt = datetime.now(timezone.utc)
        items.append({
            "source": "arxiv",
            "title": entry.get("title", "").replace("\n", " "),
            "url": entry.get("link", ""),
            "text_content": entry.get("summary", "").replace("\n", " ")[:1000],
            "published_at": dt.isoformat(),
        })

    return items
