# FOMO API -- Frontend Integration Guide

This documents the Ktor REST API for whoever builds the desktop/Android client. It assumes
the API is either running locally (via the FOMO desktop app's Dashboard, or `java -jar`) or
deployed remotely; adjust the base URL accordingly.

## Base URL & running it

```
http://127.0.0.1:8080          # default local port, see PORT env var
```

Start it via the desktop app's Dashboard tab, or manually:

```bash
cd ktor-api
JAVA_HOME=<jdk 23+> ./gradlew buildFatJar
SUPABASE_URL=... SUPABASE_KEY=... GROQ_API_KEY=... API_AUTH_TOKEN=... java -jar build/libs/trend-hopper-api.jar
```

## Authentication

Every route **except `GET /health`** requires:

```
Authorization: Bearer <API_AUTH_TOKEN>
```

`API_AUTH_TOKEN` is a single static token (not a per-user JWT -- this is a personal,
single-user app). The desktop app generates and stores it in `backend/.env` on first run
and injects it into the Ktor process's environment; get it from there, or from the
desktop app's `secrets_store.get_or_create_api_auth_token()`.

- Missing/wrong token -> `401 Unauthorized`
- The server refuses to boot at all if `API_AUTH_TOKEN` isn't set in its environment

CORS is restricted to `http://localhost:<port>` and `http://127.0.0.1:<port>`. A web-based
client on a different origin, or a mobile emulator (e.g. Android's `10.0.2.2`), will need
that allowlist extended in `ktor-api/src/main/kotlin/com/trendhopper/plugins/CORS.kt`.

## Response envelope

Every endpoint returns the same wrapper:

```jsonc
{
  "success": true,
  "data": { /* endpoint-specific payload, or null on error */ },
  "error": null            // string message when success is false
}
```

Null fields are omitted from the JSON (not sent as `null`) except where noted. HTTP status
codes are used alongside this envelope: `200`/`201` on success, `400` for bad input, `401`
for auth failures, `404` for missing resources, `500` for unhandled server errors (the
message ends up in `error`).

---

## Items

### `GET /items`
Query params (all optional):
- `feed`: `topics` (default, sorted by `relevance_score` desc) | `general` (sorted by `viral_score` desc)
- `range`: `day` | `week` (default) | `month` | `all`
- `min_relevance`: integer 0-100, default `0`

Returns up to 100 `ItemResponse` objects:

```jsonc
{
  "id": "uuid",
  "source": "reddit" | "hackernews" | "github_trending" | "rss" | "youtube" | "soundcloud",
  "title": "string",
  "url": "string",
  "relevance_score": 0,          // nullable, 0-100, set by filter.py
  "viral_score": 0.0,            // nullable, 0.0-1.0
  "matched_topic": "string",     // nullable
  "llm_summary": "string",       // nullable, one-sentence summary
  "published_at": "ISO 8601",    // nullable
  "fetched_at": "ISO 8601",      // nullable
  "is_favorited": false          // always false from this endpoint today -- see note below
}
```

**Known gap**: `is_favorited` is never actually populated true/false against the
`favorites` table by this route -- a client that needs "is this item favorited" today has
to cross-reference the separate `GET /favorites` list client-side. Worth fixing
server-side (a batched join, same pattern as `FavoritesRoutes`'s `has_notes`/`has_chat`)
if this becomes a real pain point.

### `GET /items/{id}`
Single `ItemResponse`, or `404` if not found.

---

## Favorites

### `GET /favorites`
Returns a list, newest first:

```jsonc
{
  "id": "uuid",
  "item_id": "uuid",
  "created_at": "ISO 8601",
  "has_notes": true,
  "has_chat": false,
  "item": { /* embedded ItemResponse, minus is_favorited */ }
}
```

### `POST /favorites`
Body: `{ "item_id": "uuid" }` -> `201` with the created favorite row (raw Supabase shape,
not the enriched `has_notes`/`has_chat`/`item` form above -- re-fetch the list if you need those).

### `DELETE /favorites/{id}`
`{ "deleted": "<id>" }` on success. Idempotent-ish: deleting a non-existent id still
returns 200 (PostgREST doesn't error on a 0-row delete).

---

## Notes

### `PUT /notes/{favorite_id}`
Body: `{ "content": "string" }`. Upserts -- creates the note if none exists for that
favorite, otherwise updates it in place. Returns the note row.

---

## Agent chat

### `GET /agent/chat/{favorite_id}`
Returns the chat thread:
```jsonc
{ "id": "uuid" | "", "favorite_id": "uuid", "messages": [ { "role": "user"|"assistant"|"system", "content": "string", "client_message_id": "string | null" } ] }
```
If no thread exists yet, `id` is `""` and `messages` is empty (not a 404).

### `POST /agent/chat/{favorite_id}`
Body: `{ "client_message_id": "<client-generated UUID>", "message": "string" }`.

**Idempotency contract**: generate `client_message_id` once per user message, client-side,
before sending. If the request is retried (e.g. after a dropped connection) with the same
`client_message_id`, the server detects the message already exists in the thread and
returns the existing thread unchanged -- it will **not** call Groq again or append a
second reply. This is what makes offline-queued sends (SQLDelight outbox, etc.) safe to
retry blindly.

The system prompt is built server-side from the linked item's title/summary; you don't
need to pass item context yourself. Response is the full updated thread (same shape as
GET), with the new user + assistant messages appended.

---

## Stats & calendar

### `GET /stats?range=day|week|month`
```jsonc
{ "total_items": 0, "total_favorites": 0, "avg_relevance": null, "per_source": [ { "source": "reddit", "count": 12 } ] }
```
Note: `total_favorites` and the `favorites` count are **all-time**, not scoped to `range`
(only `total_items`/`per_source` respect the range window) -- and `avg_relevance` is
currently always `null` (never computed). Both are worth flagging if a dashboard UI is
built expecting them to be live numbers.

### `GET /calendar?month=YYYY-MM`
```jsonc
{ "month": "2026-07", "days": { "2026-07-01": 14, "2026-07-02": 9 } }
```
Day -> item count map for that month, capped at 1000 items scanned.

---

## Search

### `GET /search?q=<term>`
Case-insensitive substring match across item titles/summaries, topic names, and source
names in one call:
```jsonc
{ "items": [ /* up to 50 ItemResponse */ ], "topics": ["Rust", ...], "sources": [ { "name": "reddit", "enabled": true } ] }
```

---

## Settings, topics, sources

These three are also reachable from the desktop app's Settings tab and from any MCP
client (Claude Desktop/Code) -- all three surfaces (Ktor, desktop app, MCP) read and
write the *same* Supabase tables, so changes show up everywhere immediately.

### `GET /settings` / `PUT /settings`
Flat key/value store (`RELEVANCE_THRESHOLD`, `RETENTION_DAYS`, `VIRAL_KEEP_COUNT`,
`SCHEDULE_TIME`, `SCHEDULE_TIMEZONE`, ...). `PUT` body: `{ "key": "...", "value": "..." }`
-- upserts.

### `GET /topics` / `POST /topics` / `DELETE /topics/{name}`
`POST` body: `{ "name": "string" }`. Topics are created active by default; there's no
`PUT` to toggle `active` via this route today (only add/remove) -- deactivating currently
means deleting.

### `GET /sources` / `PUT /sources/{name}`
`PUT` body (both fields optional, send only what changed):
```jsonc
{ "enabled": true, "params": { "subreddits": ["technology"], "limit": 25 } }
```
`params` shape is source-specific -- see `backend/sources/*.py`'s `fetch(params)` for what
each source module expects.

---

## Sync status

### `GET /sync/status`
```jsonc
{ "state": "synced" | "syncing" | "failed" | "offline", "last_sync_at": "ISO 8601 | null", "last_error_reason": "invalid_api_key" | "rate_limited" | "network_timeout" | "unknown" | null }
```
Reflects the most recent row in `sync_log`, written by whichever trigger last ran
(desktop app's scheduler, GitHub Actions, or a manual run). Use this to show
stale-data/"sync failed" banners rather than polling the pipeline directly.

### `POST /sync/retry`
Only does something when the Ktor process is co-located with the desktop app on the same
machine (the `PIPELINE_EXE_PATH`/`PIPELINE_EXE_ARGS` env vars the app sets when it
launches the Ktor jar). It fires the pipeline and returns immediately -- poll
`/sync/status` afterward to see the result, don't expect the retry call itself to block
until collection finishes. If those env vars aren't set (e.g. Ktor deployed standalone
with no local pipeline), it just returns an informational message and does nothing.

### `GET /health`
No auth required. `{ "status": "ok" }`. Use this for a lightweight "is the server up"
poll before hitting anything else.

---

## Error handling notes for client implementers

- A thrown exception anywhere in a route handler is caught globally and turned into
  `500` + `ApiResponse.error(message)` -- treat any 500 as "unexpected," not a documented
  contract; the message text isn't guaranteed stable across versions.
- `400` is used for missing required path/query params.
- There's no rate limiting on any endpoint from the Ktor side today -- the agent chat
  endpoint's real bottleneck is Groq's own rate limits, which currently surface as an
  unhandled exception -> `500`, not a distinguishable "rate limited" response. If you're
  building a chat UI, treat any chat 500 as "try again briefly" rather than parsing the
  message for specifics.
