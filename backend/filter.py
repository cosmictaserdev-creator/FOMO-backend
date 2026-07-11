from __future__ import annotations

import concurrent.futures
import json
import os
import re
import sys
from typing import Any

import trafilatura
from groq import Groq

import config
import db


BATCH_SIZE = 5
MAX_ARTICLE_CHARS = 8000
LLM_INPUT_CHARS = 1500

PROMPT_TEMPLATE = """You are a relevance and virality scoring assistant for a tech news aggregator. Read the full article text provided for each item — do not rely on the title alone.

Active topics (user's interests):
{topics}

For each item below, return a JSON array of objects with these fields:
- "index": int (0-based)
- "relevance_score": int 0-100 (how relevant to the user's topics)
- "viral_score": float 0.0-1.0 (how likely to go viral/be popular)
- "matched_topic": string or null (which topic it best matches, or null if none)
- "llm_summary": string (2-4 sentence summary of the actual article content — not just the title)
- "llm_reasoning": string (1-2 sentences explaining why this item matches the topic or is worth reading)

Items:
{items}
"""


def run() -> dict[str, Any]:
    try:
        groq_key = os.environ.get("GROQ_API_KEY")
        if not groq_key:
            return {"status": "skipped", "reason": "GROQ_API_KEY not configured"}

        topics = config.load_active_topics()
        threshold = config.load_relevance_threshold()
        viral_keep = config.load_viral_keep_count()

        if not topics:
            return {"status": "skipped", "reason": "no_active_topics"}

        unscored = _fetch_unscored()
        if not unscored:
            return {"status": "skipped", "reason": "no_unscored_items"}

        client = Groq(api_key=groq_key)
        total_scored = 0
        errors: list[str] = []

        for i in range(0, len(unscored), BATCH_SIZE):
            batch = unscored[i : i + BATCH_SIZE]
            try:
                scores = _score_batch(client, batch, topics)
                _apply_scores(batch, scores, threshold, viral_keep)
                total_scored += len(scores)
            except Exception as e:
                errors.append(f"batch {i // BATCH_SIZE}: {e}")
                print(f"Filter error on batch {i // BATCH_SIZE}: {e}", file=sys.stderr)

        return {
            "status": "completed",
            "scored": total_scored,
            "errors": errors,
        }
    except Exception as e:
        return {"status": "failed", "reason": str(e)}


_OG_IMAGE_RE = re.compile(
    r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)(?::src)?["\'][^>]+'
    r'content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


def _extract_og_image(html: str) -> str | None:
    if not html:
        return None
    match = _OG_IMAGE_RE.search(html)
    if match:
        url = match.group(1).strip()
        if url.startswith("http"):
            return url
    return None


def _fetch_article_meta(url: str) -> dict[str, str | None]:
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return {"text": None, "image_url": None}
        text = trafilatura.extract(downloaded)
        image_url = None
        try:
            meta = trafilatura.metadata.extract_metadata(downloaded)
            if meta and getattr(meta, "image", None):
                image_url = meta.image
        except Exception:
            pass
        if not image_url:
            image_url = _extract_og_image(downloaded)
        return {
            "text": (text[:MAX_ARTICLE_CHARS] if text else None),
            "image_url": image_url,
        }
    except Exception as e:
        print(f"  fetch failed: {url[:60]}... {e}", file=sys.stderr)
        return {"text": None, "image_url": None}


def _fetch_unscored() -> list[dict[str, Any]]:
    supa = db.get_supabase()
    if not supa:
        return []
    result = supa.table("items")\
        .select("id, title, text_content, source, url")\
        .is_("relevance_score", "null")\
        .order("fetched_at", desc=True)\
        .limit(200)\
        .execute()
    return result.data or []


def _fetch_batch_meta(batch: list[dict[str, Any]]) -> list[dict[str, str | None]]:
    urls = [item.get("url", "") for item in batch]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        return list(ex.map(_fetch_article_meta, urls))


def _score_batch(
    client: Groq,
    batch: list[dict[str, Any]],
    topics: list[str],
) -> list[dict[str, Any]]:
    topic_str = ", ".join(topics)

    # Fetch full article texts and images in parallel
    metas = _fetch_batch_meta(batch)

    items_for_llm = []
    for i, item in enumerate(batch):
        meta = metas[i]
        full_text = meta.get("text") or (item.get("text_content") or "")[:500]
        item["article_text"] = full_text
        if meta.get("image_url"):
            item["image_url"] = meta["image_url"]
        # Send truncated text to LLM to fit within token limits; full text stored in DB
        llm_text = full_text[:LLM_INPUT_CHARS] if full_text else ""
        items_for_llm.append({
            "index": i,
            "title": item["title"],
            "article_text": llm_text,
        })

    items_str = json.dumps(items_for_llm, indent=2)
    prompt = PROMPT_TEMPLATE.format(topics=topic_str, items=items_str)

    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    content = resp.choices[0].message.content
    data = json.loads(content)
    scores = data.get("scores", data.get("items", data.get("results", [])))
    if isinstance(scores, dict):
        scores = [scores]
    return scores


def _apply_scores(
    batch: list[dict[str, Any]],
    scores: list[dict[str, Any]],
    threshold: int,
    viral_keep: int,
) -> None:
    supa = db.get_supabase()
    if not supa:
        return

    for score in scores:
        idx = score.get("index")
        if idx is None or idx < 0 or idx >= len(batch):
            continue
        item = batch[idx]
        item_id = item["id"]

        relevance = max(0, min(100, int(score.get("relevance_score", 0))))
        viral = max(0.0, min(1.0, float(score.get("viral_score", 0))))
        matched_topic = score.get("matched_topic") or None
        summary = (score.get("llm_summary") or "")[:500]
        reasoning = (score.get("llm_reasoning") or "")[:500]
        article_text = (item.get("article_text") or "")[:MAX_ARTICLE_CHARS]
        image_url = item.get("image_url") or None

        update_data = {
            "relevance_score": relevance,
            "viral_score": viral,
            "matched_topic": matched_topic,
            "llm_summary": summary,
            "text_content": article_text,
        }
        if reasoning:
            update_data["llm_reasoning"] = reasoning
        if image_url:
            update_data["image_url"] = image_url

        supa.table("items").update(update_data).eq("id", item_id).execute()

    # Discard low-relevance items (below threshold) except keep top N by viral_score
    kept = set()
    viral_candidates = [
        (item["id"], float(score.get("viral_score", 0)))
        for score in scores
        for item in batch
        if score.get("index") is not None
        and batch[score["index"]]["id"] == item["id"]
        and int(score.get("relevance_score", 0)) < threshold
    ]
    viral_candidates.sort(key=lambda x: x[1], reverse=True)
    for vid, _ in viral_candidates[:viral_keep]:
        kept.add(vid)

    for score in scores:
        idx = score.get("index")
        if idx is None:
            continue
        item = batch[idx]
        relevance = int(score.get("relevance_score", 0))
        if relevance < threshold and item["id"] not in kept:
            supa.table("items").delete().eq("id", item["id"]).execute()


if __name__ == "__main__":
    import json
    result = run()
    print(json.dumps(result, indent=2))
    if result.get("status") == "failed":
        sys.exit(1)
