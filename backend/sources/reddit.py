from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any

import praw
import prawcore

from db import content_hash


_USER_AGENT = (
    f"Windows:FOMO-backend:v0.1.0"
    f"(by /u/{os.environ.get('REDDIT_USERNAME', 'fomo-user')}; "
    f"Personal trending-news aggregator. Non-commercial, reads only.)"
)
_MAX_RETRIES = 3
_RETRY_DELAY = 2.0


def _extract_image(post: Any) -> str | None:
    """Best-effort preview/thumbnail image for a Reddit post."""
    try:
        preview = getattr(post, "preview", None)
        if preview:
            images = preview.get("images") or []
            if images:
                src = images[0].get("source", {}).get("url")
                if src:
                    return src.replace("&amp;", "&")
    except Exception:
        pass
    thumb = getattr(post, "thumbnail", "") or ""
    if thumb.startswith("http"):
        return thumb
    url = getattr(post, "url", "") or ""
    if url.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
        return url
    return None


def fetch(params: dict[str, Any]) -> list[dict[str, Any]]:
    missing = [k for k in ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET") if not os.environ.get(k)]
    if missing:
        raise RuntimeError(f"Missing Reddit credentials: {', '.join(missing)}")

    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=_USER_AGENT,
    )

    subreddits: list[str] = params.get("subreddits", ["technology"])
    sort: str = params.get("sort", "hot")
    limit: int = min(params.get("limit", 25), 100)

    items: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()

    for sub_name in subreddits:
        for attempt in range(_MAX_RETRIES):
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
                        "image_url": _extract_image(post),
                        "published_at": published.isoformat(),
                    })
                break
            except prawcore.exceptions.Forbidden:
                raise RuntimeError(
                    f"Reddit access denied for r/{sub_name}. Reddit now requires API access approval. "
                    f"Submit a request at https://support.reddithelp.com/hc/en-us/requests/new "
                    f"(select 'API support' > 'Developer -- building a non-commercial app')."
                )
            except prawcore.exceptions.ResponseException as e:
                if e.response.status_code == 429:
                    wait = _RETRY_DELAY * (2 ** attempt)
                    time.sleep(wait)
                    continue
                if attempt == _MAX_RETRIES - 1:
                    raise
                time.sleep(_RETRY_DELAY)
            except Exception:
                if attempt == _MAX_RETRIES - 1:
                    raise
                time.sleep(_RETRY_DELAY)

    return items
