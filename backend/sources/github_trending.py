from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests
from bs4 import BeautifulSoup


def fetch(params: dict[str, Any]) -> list[dict[str, Any]]:
    language = params.get("language", "")
    since = params.get("since", "daily")

    url = "https://github.com/trending"
    if language:
        url += f"/{language}"
    url += f"?since={since}"

    resp = requests.get(url, headers={"User-Agent": "trend-hopper/0.1"}, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    articles = soup.select("article.Box-row")

    items: list[dict[str, Any]] = []
    for article in articles:
        h2 = article.select_one("h2 a")
        if not h2:
            continue
        full_name = h2.get_text(strip=True).replace(" ", "")
        repo_url = f"https://github.com/{full_name}"
        desc_el = article.select_one("p")
        description = desc_el.get_text(strip=True) if desc_el else ""

        items.append({
            "source": "github_trending",
            "title": full_name,
            "url": repo_url,
            "text_content": description[:1000],
            "published_at": datetime.now(timezone.utc).isoformat(),
        })

    return items
