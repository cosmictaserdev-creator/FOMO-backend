from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests


def fetch(params: dict[str, Any]) -> list[dict[str, Any]]:
    limit = min(params.get("limit", 20), 50)

    resp = requests.get("https://huggingface.co/api/models",
                        params={"sort": "trendingScore", "limit": limit},
                        headers={"User-Agent": "trend-hopper/0.1"}, timeout=15)
    resp.raise_for_status()

    items: list[dict[str, Any]] = []
    for model in resp.json():
        model_id = model.get("modelId") or model.get("id")
        if not model_id:
            continue
        created = model.get("createdAt")
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now(timezone.utc)
        parts = [
            f"Trending model on Hugging Face: {model_id}.",
            f"Task: {model['pipeline_tag']}." if model.get("pipeline_tag") else "",
            f"Likes: {model.get('likes', 0)}, downloads: {model.get('downloads', 0)}.",
        ]
        items.append({
            "source": "huggingface",
            "title": model_id,
            "url": f"https://huggingface.co/{model_id}",
            "text_content": " ".join(p for p in parts if p)[:1000],
            "published_at": dt.isoformat(),
        })

    return items
