from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import praw

from db import content_hash


def fetch(params: dict[str, Any]) -> list[dict[str, Any]]:
    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent="trend-hopper/0.1",
    )

    subreddits: list[str] = params.get("subreddits", ["technology"])
    sort: str = params.get("sort", "hot")
    limit: int = min(params.get("limit", 25), 100)

    items: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()

    for sub_name in subreddits:
        try:
            sub = reddit.subreddit(sub_name.strip())
            method = getattr(sub, sort, sub.hot)
            for post in method(limit=limit):
                h = content_hash(post.url or "", post.title or "")
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)
                published = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
                items.append({
                    "source": "reddit",
                    "title": post.title,
                    "url": post.url,
                    "text_content": post.selftext[:1000] if post.selftext else "",
                    "published_at": published.isoformat(),
                })
        except Exception:
            continue

    return items
