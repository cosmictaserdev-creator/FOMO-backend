# Trend Hopper — API Documentation

> Generated: 2026-07-10 | Updated: 2026-07-13
> Ktor API @ `localhost:8081` | Proxy @ `localhost:8080`
> Auth: `Authorization: Bearer <API_AUTH_TOKEN>` (except `/health` and proxy-only endpoints)
>
> **Changes (2026-07-10):** Added `text_content` (full article body for in-app reading), `image_url` (OG thumbnail), and `llm_reasoning` (why the item was matched). The LLM now reads the full article before scoring.
>
> **Changes (2026-07-13):** Added reverse proxy (`serve.py`) with AI formatting and direct chat endpoints. Default `min_relevance` raised from 0 to 20. Article media support (YouTube embeds, image extraction, social video links).

---

## Table of Contents

1. [Health](#1-get-health)
2. [Items](#2-get-items)
3. [Item Detail](#3-get-itemsid)
4. [Favorites](#4-get-favorites)
5. [Stats](#5-get-stats)
6. [Calendar](#6-get-calendarmonth)
7. [Search](#7-get-search)
8. [Topics](#8-get-topics)
9. [Sources](#9-get-sources)
10. [Settings](#10-get-settings)
11. [Sync Status](#11-get-syncstatus)

---

## 1. GET /health

**Public endpoint** — no auth required.

```json
{
  "status": "ok"
}
```

---

## 2. GET /items

**Query params:** `feed=topics`, `range=week`, `min_relevance=0`

Returns paginated, scored items from all sources.

```json
{
  "success": true,
  "data": [
    {
      "id": "756e7ae4-f13a-43f9-8def-2249a094252a",
      "source": "hackernews",
      "title": "Separating signal from noise in coding evaluations",
      "url": "https://openai.com/index/separating-signal-from-noise-coding-evaluations/",
      "text_content": "OpenAI has published a new evaluation framework... (full article text for in-app reading, no redirect needed)",
      "image_url": "https://openai.com/images/og-image.png",
      "relevance_score": 70,
      "viral_score": 0.5,
      "matched_topic": "Programming",
      "llm_summary": "OpenAI published a new framework for separating signal from noise in coding evaluations, focusing on measuring real developer ability rather than test-taking skill. The approach uses targeted prompt perturbations to reveal genuine understanding.",
      "llm_reasoning": "This item is matched to Programming because it directly discusses coding evaluation methodology and developer assessment tools.",
      "published_at": "2026-07-08T21:03:51+00:00",
      "fetched_at": "2026-07-09T10:18:43.74474+00:00",
      "is_favorited": false
    },
    {
      "id": "addd8f59-a215-4756-9824-523a703c11ea",
      "source": "hackernews",
      "title": "Show HN: Getting GLM 5.2 running on my slow computer",
      "url": "https://github.com/JustVugg/colibri",
      "relevance_score": 80,
      "viral_score": 0.8,
      "matched_topic": "AI & Machine Learning",
      "llm_summary": "GLM 5.2 running",
      "published_at": "2026-07-09T08:05:04+00:00",
      "fetched_at": "2026-07-10T03:49:50.396652+00:00",
      "is_favorited": false
    },
    {
      "id": "9e5cfc9c-4e6c-4d27-97ef-949a7508b7df",
      "source": "hackernews",
      "title": "TypeScript 7",
      "url": "https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/",
      "relevance_score": 80,
      "viral_score": 0.6,
      "matched_topic": "Programming",
      "llm_summary": "TypeScript 7 release",
      "published_at": "2026-07-08T16:06:35+00:00",
      "fetched_at": "2026-07-09T10:18:43.74474+00:00",
      "is_favorited": false
    },
    {
      "id": "d1108911-c707-4b2e-866a-b70d1a2f3f3b",
      "source": "hackernews",
      "title": "Rewriting Bun in Rust",
      "url": "https://bun.com/blog/bun-in-rust",
      "relevance_score": 80,
      "viral_score": 0.7,
      "matched_topic": "Programming",
      "llm_summary": "Rewriting Bun in Rust",
      "published_at": "2026-07-08T21:49:59+00:00",
      "fetched_at": "2026-07-09T10:18:43.74474+00:00",
      "is_favorited": false
    },
    {
      "id": "79a69786-9ece-4a56-8c5e-b27fd19400db",
      "source": "hackernews",
      "title": "Why developers are ditching GitHub for Codeberg and self-hosting alternatives",
      "url": "https://www.howtogeek.com/why-developers-are-ditching-github-for-codeberg-and-self-hosting-alternatives/",
      "relevance_score": 80,
      "viral_score": 0.8,
      "matched_topic": "Startups",
      "llm_summary": "Developers ditch GitHub",
      "published_at": "2026-07-09T08:22:52+00:00",
      "fetched_at": "2026-07-09T10:18:43.74474+00:00",
      "is_favorited": false
    },
    {
      "id": "8a61b9f1-b09b-487f-97da-772fb0d9908b",
      "source": "hackernews",
      "title": "Cargo-nextest: 3x faster than cargo test, per-test isolation, first-class CI",
      "url": "https://nexte.st/",
      "relevance_score": 80,
      "viral_score": 0.7,
      "matched_topic": "Programming",
      "llm_summary": "Cargo-nextest released",
      "published_at": "2026-07-06T04:19:30+00:00",
      "fetched_at": "2026-07-09T10:18:43.74474+00:00",
      "is_favorited": false
    },
    {
      "id": "5bd65ae6-53ef-4071-aa48-28dfdef20d0e",
      "source": "hackernews",
      "title": "Unicode's transliteration rules are Turing-complete",
      "url": "https://seriot.ch/computation/uts35/",
      "relevance_score": 80,
      "viral_score": 0.6,
      "matched_topic": "Programming",
      "llm_summary": "Unicode rules are Turing-complete",
      "published_at": "2026-07-08T09:44:20+00:00",
      "fetched_at": "2026-07-09T10:18:43.74474+00:00",
      "is_favorited": false
    },
    {
      "id": "5dcbb1cf-59c2-472d-8c1b-11faf5426eba",
      "source": "hackernews",
      "title": "Decoding the obfuscated bash script on a Uniqlo t-shirt",
      "url": "https://tris.sherliker.net/blog/obfuscated-self-evaluating-bash-script-by-cdn-akamai-being-supplied-to-consumers-via-retail-stores/",
      "relevance_score": 75,
      "viral_score": 0.55,
      "matched_topic": "Programming",
      "llm_summary": "Decoding obfuscated bash",
      "published_at": "2026-07-08T08:46:06+00:00",
      "fetched_at": "2026-07-09T10:18:43.74474+00:00",
      "is_favorited": false
    },
    {
      "id": "be756edd-882c-4de3-8d29-b48caf33adca",
      "source": "hackernews",
      "title": "Interview with Mitchell Hashimoto about Ghostty and Zig",
      "url": "https://alexalejandre.com/programming/interview-with-mitchell-hashimoto/",
      "relevance_score": 60,
      "viral_score": 0.6,
      "matched_topic": "Programming",
      "llm_summary": "Interview with Mitchell",
      "published_at": "2026-07-09T17:17:16+00:00",
      "fetched_at": "2026-07-10T03:49:50.396652+00:00",
      "is_favorited": false
    },
    {
      "id": "964dd450-7dfe-4482-a8a3-fcbf9f43907e",
      "source": "hackernews",
      "title": "Apple Silicon Exec Explains Mac Mini AI Demand and On-Device Future",
      "url": "https://www.macrumors.com/2026/07/06/apple-silicon-exec-explains-mac-mini-ai-demand/",
      "relevance_score": 60,
      "viral_score": 0.6,
      "matched_topic": "Technology",
      "llm_summary": "Apple Silicon Exec",
      "published_at": "2026-07-06T14:59:21+00:00",
      "fetched_at": "2026-07-10T03:49:50.396652+00:00",
      "is_favorited": false
    },
    {
      "id": "a8b3e2a3-d2b6-496c-ae8c-292488a5a2de",
      "source": "hackernews",
      "title": "A road to Lisp: Why Lisp",
      "url": "https://scotto.me/blog/2026-07-09-why-lisp/",
      "relevance_score": 40,
      "viral_score": 0.4,
      "matched_topic": "Programming",
      "llm_summary": "Road to Lisp",
      "published_at": "2026-07-09T13:06:04+00:00",
      "fetched_at": "2026-07-10T03:49:50.396652+00:00",
      "is_favorited": false
    }
  ]
}
```

> **Note:** The real response contains ~40 items. Truncated for readability.

---

## 3. GET /items/{id}

**Path param:** `id` (UUID)

```json
{
  "success": true,
  "data": {
    "id": "756e7ae4-f13a-43f9-8def-2249a094252a",
    "source": "hackernews",
    "title": "Separating signal from noise in coding evaluations",
    "url": "https://openai.com/index/separating-signal-from-noise-coding-evaluations/",
    "text_content": "OpenAI has published a new evaluation framework... (full article text for in-app reading)",
    "image_url": "https://openai.com/images/og-image.png",
    "relevance_score": 70,
    "viral_score": 0.5,
    "matched_topic": "Programming",
    "llm_summary": "OpenAI published a new framework for separating signal from noise in coding evaluations, focusing on measuring real developer ability rather than test-taking skill.",
    "llm_reasoning": "This item is matched to Programming because it directly discusses coding evaluation methodology.",
    "published_at": "2026-07-08T21:03:51+00:00",
    "fetched_at": "2026-07-09T10:18:43.74474+00:00",
    "is_favorited": false
  }
}
```

---

## 4. GET /favorites

Returns all favorited items with enriched `has_notes` / `has_chat` flags and nested `item` object.

```json
{
  "success": true,
  "data": [
    {
      "id": "abc-123",
      "item_id": "756e7ae4-f13a-43f9-8def-2249a094252a",
      "created_at": "2026-07-10T10:15:00Z",
      "has_notes": true,
      "has_chat": false,
      "item": {
        "id": "756e7ae4-f13a-43f9-8def-2249a094252a",
        "source": "hackernews",
        "title": "Separating signal from noise in coding evaluations",
        "url": "https://openai.com/index/separating-signal-from-noise-coding-evaluations/",
        "text_content": "OpenAI has published a new evaluation framework... (full article text for in-app reading)",
        "image_url": "https://openai.com/images/og-image.png",
        "relevance_score": 70,
        "viral_score": 0.5,
        "matched_topic": "Programming",
        "llm_summary": "OpenAI published a new framework...",
        "llm_reasoning": "Matches Programming topic because...",
        "published_at": "2026-07-08T21:03:51+00:00",
        "fetched_at": "2026-07-09T10:18:43.74474+00:00",
        "is_favorited": true
      }
    }
  ]
}
```

### POST /favorites

**Body:** `{ "item_id": "756e7ae4-f13a-43f9-8def-2249a094252a" }`

### DELETE /favorites/{id}

---

## 5. GET /stats

**Query param:** `range=week`

```json
{
  "success": true,
  "data": {
    "total_items": 142,
    "total_favorites": 1,
    "avg_relevance": 80.5,
    "per_source": [
      { "source": "hackernews", "count": 24 },
      { "source": "github_trending", "count": 32 },
      { "source": "youtube", "count": 18 },
      { "source": "rss", "count": 68 }
    ]
  }
}
```

---

## 6. GET /calendar?month=2026-07

Returns a heatmap map: day → item count fetched on that day.

```json
{
  "success": true,
  "data": {
    "month": "2026-07",
    "days": {
      "2026-07-09": 108,
      "2026-07-10": 34
    }
  }
}
```

---

## 7. GET /search?q=typescript

Full-text search across items.

```json
{
  "success": true,
  "data": [
    {
      "id": "9e5cfc9c-4e6c-4d27-97ef-949a7508b7df",
      "source": "hackernews",
      "title": "TypeScript 7",
      "url": "https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/",
      "text_content": "Microsoft announced TypeScript 7.0... (full article text)",
      "image_url": "https://devblogs.microsoft.com/typescript/images/ts7.png",
      "relevance_score": 80,
      "viral_score": 0.6,
      "matched_topic": "Programming",
      "llm_summary": "TypeScript 7.0 brings significant performance improvements...",
      "llm_reasoning": "Directly about a programming language update...",
      "published_at": "2026-07-08T16:06:35+00:00",
      "fetched_at": "2026-07-09T10:18:43.74474+00:00",
      "is_favorited": false
    }
  ]
}
```

---

## 8. GET /topics

```json
{
  "success": true,
  "data": [
    { "name": "AI & Machine Learning", "active": true },
    { "name": "Programming", "active": true },
    { "name": "Startups", "active": true },
    { "name": "Technology", "active": true },
    { "name": "Design", "active": true },
    { "name": "Android Development", "active": false }
  ]
}
```

### POST /topics
**Body:** `{ "name": "New Topic" }`

### DELETE /topics/{name}

---

## 9. GET /sources

```json
{
  "success": true,
  "data": [
    {
      "name": "reddit",
      "enabled": true,
      "params": { "subreddits": ["technology"], "sort": "hot", "limit": 25 }
    },
    {
      "name": "hackernews",
      "enabled": true,
      "params": { "type": "top", "limit": 30 }
    },
    {
      "name": "github_trending",
      "enabled": true,
      "params": { "language": "", "since": "daily" }
    },
    {
      "name": "rss",
      "enabled": true,
      "params": {
        "feeds": [
          "https://techncruncher.blogspot.com/feeds/posts/default",
          "https://hnrss.org/frontpage",
          "https://hnrss.org/newest?points=100"
        ],
        "limit": 20
      }
    },
    {
      "name": "youtube",
      "enabled": true,
      "params": { "query": "tech news", "max_results": 10 }
    },
    {
      "name": "soundcloud",
      "enabled": true,
      "params": { "genre": "electronic", "limit": 10 }
    }
  ]
}
```

### PUT /sources/{name}
**Body:** `{ "enabled": false }` or `{ "params": { "limit": 50 } }`

---

## 10. GET /settings

```json
{
  "success": true,
  "data": {
    "RELEVANCE_THRESHOLD": "50",
    "VIRAL_KEEP_COUNT": "5",
    "RETENTION_DAYS": "30",
    "SCHEDULE_TIME": "06:00",
    "SCHEDULE_TIMEZONE": "UTC"
  }
}
```

### PUT /settings
**Body:** `{ "key": "RELEVANCE_THRESHOLD", "value": "60" }`

---

## 11. GET /sync/status

```json
{
  "success": true,
  "data": {
    "state": "synced",
    "last_sync_at": "2026-07-10T05:12:18.976Z",
    "last_error_reason": null
  }
}
```

### POST /sync/retry
Triggers a pipeline run locally (if `PIPELINE_EXE_PATH` is set).

---

## 12. Proxy-Only Endpoints (serve.py)

These endpoints are handled by the Python reverse proxy (`serve.py` on port 8080) and bypass Ktor entirely. They talk directly to Supabase and Groq.

### `POST /api/format-article`

Reformats raw article text into clean, Medium-style HTML using Groq.

**Body:** `{ "text": "raw article text", "title": "Article Title" }`

**Response:**
```json
{
  "success": true,
  "data": {
    "formatted": "<h1>Title</h1><p>Formatted article...</p>"
  }
}
```

**Formatting rules:**
- Uses `<h1>` for main title, `<h2>` for sections, `<h3>` for subsections
- Proper paragraph spacing with drop caps
- `<blockquote>` for quotes
- `<pre><code>` for code blocks
- Clean list handling
- Preserves original text accurately

### `GET /api/agent/chat/{favorite_id}`

Reads chat history from Supabase directly (bypasses Ktor's double-encoding bug).

**Response:** Same shape as Ktor's `GET /agent/chat/{favorite_id}`:
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "favorite_id": "uuid",
    "messages": [
      { "role": "user", "content": "...", "client_message_id": "uuid" },
      { "role": "assistant", "content": "..." }
    ]
  }
}
```

### `POST /api/agent/chat/{favorite_id}`

Sends a chat message via Groq and persists to Supabase directly (bypasses Ktor's double-encoding bug where `JsonArray.toString()` gets re-encoded as a JSON string instead of a JSON array).

**Body:** `{ "client_message_id": "uuid", "message": "user message" }`

**Response:** Full updated thread with new user + assistant messages appended.

**Idempotency:** Same contract as Ktor — duplicate `client_message_id` returns existing thread without calling Groq again.

---

## Mutation Endpoints Summary

| Method | Path | Body |
|--------|------|------|
| POST | `/favorites` | `{ "item_id": "uuid" }` |
| DELETE | `/favorites/{id}` | — |
| PUT | `/notes/{favorite_id}` | `{ "content": "..." }` |
| GET | `/agent/chat/{favorite_id}` | — |
| POST | `/agent/chat/{favorite_id}` | `{ "client_message_id": "uuid", "message": "..." }` |
| POST | `/topics` | `{ "name": "..." }` |
| DELETE | `/topics/{name}` | — |
| PUT | `/sources/{name}` | `{ "enabled": bool, "params": {...} }` |
| GET | `/settings` | — |
| PUT | `/settings` | `{ "key": "...", "value": "..." }` |
| POST | `/sync/retry` | — |

---

## In-App Article Reading

The `text_content` field on every item contains the **full article body** (extracted by the pipeline, up to 8000 chars). This allows the desktop app to render the article content directly — no redirect, no ads, no popups.

- `text_content` — Full extracted article text (may contain HTML tags)
- `image_url` — Open Graph / thumbnail image (if available)
- `llm_summary` — AI-generated 2-4 sentence summary
- `llm_reasoning` — AI explanation of why the item was matched to this topic

### Media in articles

The `text_content` field may contain:

- **`<img>` tags** — extract `src` attributes for inline article images
- **Bare image URLs** — `.jpg`, `.png`, `.webp`, `.gif`, `.avif` URLs in the text
- **YouTube URLs** — `youtube.com/watch?v=ID`, `youtu.be/ID`, `youtube.com/embed/ID`
- **Social video URLs** — Twitter/X, TikTok, Instagram post URLs
- **Other video URLs** — Vimeo, Dailymotion, Streamable

The test UI (`test-ui.html`) handles all of these:
- YouTube URLs are embedded as 16:9 iframes in both the detail header and article body
- Article images are shown in a clickable grid (up to 8) in the detail header
- Social video URLs get styled link cards
- The AI Format button can reformat raw HTML into clean Medium-style HTML

## Response Envelope

All endpoints (except `/health`) wrap responses in a standard envelope:

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

Errors:

```json
{
  "success": false,
  "data": null,
  "error": "Item not found"
}
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Desktop App (app/                       │
│            Setup | Dashboard | Settings | MCP Config)           │
└──────────────────────┬──────────────────────┬───────────────────┘
                       │ HTTP/JSON            │ MCP/stdio
                       ▼                      ▼
┌──────────────────────────────┐   ┌──────────────────────────────┐
│      Ktor REST API           │   │     MCP Server               │
│  GET /items, /favorites,     │   │  get_settings, list_topics,  │
│  /stats, /search, /topics    │   │  add_topic, toggle_source,   │
│  POST /favorites, /chat      │   │  set_relevance_threshold     │
│  PUT /notes, /sources        │   │                              │
│  DELETE /favorites, /topics  │   │                              │
└──────────┬───────────────────┘   └──────────────────────────────┘
           │ HTTP (PostgREST)
           ▼
┌──────────────────────────────────────────────────────────────┐
│                       Supabase (Postgres)                    │
│  Tables: settings, topics, sources_config, items, favorites, │
│          notes, agent_chats, sync_log                        │
└──────────┬───────────────────────────────────────────────────┘
           │ Database triggers
           ▼
┌──────────────────────────────────────────────────────────────┐
│                    Python Service Layer                       │
│  collector.py → sources/* → db.upsert_items()                │
│  filter.py → Groq scoring                                    │
│  run_daily.py / scheduler.py (local trigger)                 │
│  GitHub Actions (cloud trigger)                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Sources Overview

| Source | Type | API Key Needed |
|--------|------|---------------|
| Reddit | PRAW (OAuth) | REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET |
| Hacker News | Firebase REST | None |
| GitHub Trending | BeautifulSoup scrape | None |
| RSS | feedparser | None |
| YouTube | YouTube Data v3 | YOUTUBE_API_KEY |
| SoundCloud | Charts API | None |
| Lobsters | REST (`hottest.json`) | None |
| Dev.to | REST | None |
| Mastodon | REST (trending links) | None |
| arXiv | Atom feed (feedparser) | None |
| Hugging Face | REST (trending models) | None |
| Stack Exchange | REST (hot questions) | None |

---

*End of API Documentation*
