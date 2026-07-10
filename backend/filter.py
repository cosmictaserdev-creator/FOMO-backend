from __future__ import annotations

import json
import os
import sys
from typing import Any

from groq import Groq

import config
import db


BATCH_SIZE = 20

PROMPT_TEMPLATE = """You are a relevance and virality scoring assistant for a tech news aggregator.

Active topics (user's interests):
{topics}

For each item below, return a JSON array of objects with these fields:
- "index": int (0-based)
- "relevance_score": int 0-100 (how relevant to the user's topics)
- "viral_score": float 0.0-1.0 (how likely to go viral/be popular)
- "matched_topic": string or null (which topic it best matches, or null if none)
- "llm_summary": string (one-sentence summary, max 20 words)

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


def _score_batch(
    client: Groq,
    batch: list[dict[str, Any]],
    topics: list[str],
) -> list[dict[str, Any]]:
    topic_str = ", ".join(topics)
    items_str = json.dumps([
        {"index": i, "title": item["title"], "text": (item.get("text_content") or "")[:500]}
        for i, item in enumerate(batch)
    ], indent=2)

    prompt = PROMPT_TEMPLATE.format(topics=topic_str, items=items_str)

    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    content = resp.choices[0].message.content
    data = json.loads(content)
    scores = data.get("scores", data.get("items", []))
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
        summary = (score.get("llm_summary") or "")[:300]

        supa.table("items").update({
            "relevance_score": relevance,
            "viral_score": viral,
            "matched_topic": matched_topic,
            "llm_summary": summary,
        }).eq("id", item_id).execute()

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
