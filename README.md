# FOMO Backend

Personal tech trends aggregator. Collects trending content from multiple sources, scores it against your interests using an LLM, and serves it via a REST API and AI-assistant config tools.

## Architecture

Three backend components:

- **Python service layer** -- fetches from Reddit, Hacker News, GitHub Trending, RSS, YouTube, SoundCloud; scores items with Groq (Llama 70B) for relevance and viral potential; writes to Supabase.
- **Ktor API** -- REST server for desktop/Android clients (items, favorites, notes, agent chat, search, sync status, stats).
- **MCP server** -- exposes settings (topics, sources, thresholds, schedule) as MCP tools so any MCP-compatible AI client (Claude Desktop, Claude Code) can read and modify your configuration through conversation.

## Project structure

```
backend/                    # Python service layer + MCP server
  collector.py              # Orchestrates all source fetchers
  filter.py                 # Groq relevance/viral scoring pass
  run_daily.py              # Local trigger with today-run guard
  db.py                     # Supabase client wrapper (shared by all components)
  config.py                 # Loads settings/topics/sources from Supabase tables
  mcp_server.py             # MCP tool definitions (9 tools)
  sources/
    reddit.py               # PRAW-based subreddit fetcher
    hackernews.py           # Firebase API
    github_trending.py      # BeautifulSoup scrape
    rss.py                  # Generic RSS/Atom feedparser
    youtube.py              # YouTube Data API v3
    soundcloud.py           # SoundCloud charts API
  pyproject.toml            # uv-managed Python project
  .env.example

ktor-api/                   # Ktor 3 REST server (JVM)
  build.gradle.kts          # Kotlin 2.1, Ktor 3.1, Java HttpClient
  src/main/kotlin/com/trendhopper/
    Application.kt          # Netty entry point
    plugins/                # Serialization, CORS, StatusPages, Routing
    routes/                 # Items, Favorites, Notes, Agent, Stats, Settings, Topics, Sources, Sync, Search
    models/                 # Request/response DTOs
    services/               # SupabaseClient (Java HttpClient -> PostgREST)
  src/main/resources/application.yaml

supabase/
  001_schema.sql            # Full database schema + seed data

.github/workflows/
  daily-collect.yml         # Cron schedule (6/12/18 UTC) with retention cleanup
```

## Setup

### Prerequisites

- Python 3.12+
- Java 21+ (Gradle 9.6+)
- A Supabase project
- API keys: Groq, Reddit (client ID + secret), YouTube

### Database

Run `supabase/001_schema.sql` in your Supabase SQL editor. This creates all tables (settings, topics, sources_config, items, favorites, notes, agent_chats, sync_log) with seed data for default topics and sources.

### Backend sources

```bash
cd backend
uv sync
cp .env.example .env
# Fill in SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, YOUTUBE_API_KEY
uv run python collector.py
uv run python filter.py
```

### Ktor API

```bash
cd ktor-api
export JAVA_HOME=/path/to/jdk-26+
./gradlew build
SUPABASE_URL=... SUPABASE_KEY=... GROQ_API_KEY=... java -jar build/libs/trend-hopper-api.jar
```

The API serves on port 8080 (configurable via `PORT` env var).

### MCP server

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "trend-hopper": {
      "command": "python",
      "args": ["/absolute/path/to/backend/mcp_server.py"]
    }
  }
}
```

Then restart Claude Desktop. The tools (get_settings, list_topics, list_sources, add_topic, remove_topic, toggle_source, update_source_params, set_relevance_threshold, set_retention_days, set_schedule, get_today_summary) will be available.

### GitHub Actions

Set the following repository secrets:
- `SUPABASE_URL`, `SUPABASE_KEY`, `GROQ_API_KEY`
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USERNAME`, `YOUTUBE_API_KEY`

The workflow runs at 6:00, 12:00, and 18:00 UTC and handles collection, scoring, and retention cleanup.

### Windows Task Scheduler (local trigger)

Create a task with:
- Trigger: At log on
- Action: `pythonw.exe C:\path\to\backend\run_daily.py`
- Working directory: `C:\path\to\backend`

The local run guards against duplicate execution via `last_run.txt`.

## Key design decisions

- **Single source of truth**: Supabase Postgres stores everything. The Python collector, Ktor API, and MCP server all read from and write to the same tables.
- **Dedup**: Hybrid approach -- URL hash for exact dedup, time-bounded title hash for cross-source dedup (same article on Reddit and HN).
- **Sync status**: Append-only sync_log table. Each run (local or Actions) inserts its outcome. The `GET /sync/status` endpoint returns the latest row plus `last_successful_sync_at` so the client can decide whether to show stale-data warnings.
- **Chat idempotency**: Every user message carries a client-generated UUID. The server rejects duplicate `client_message_id` values, so retries after network drops produce exactly one reply.
- **Retention**: Items that were ever favorited are preserved indefinitely. Only items never favorited and past the retention window are deleted.
