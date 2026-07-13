# FOMO Backend

Personal tech trends aggregator. Collects trending content from multiple sources, scores it against your interests using an LLM, and serves it via a REST API and AI-assistant config tools.

## Architecture

Three backend components:

- **Python service layer** -- fetches from Reddit, Hacker News, GitHub Trending, RSS, YouTube, SoundCloud, Lobsters, Dev.to, Mastodon, arXiv, Hugging Face, Stack Exchange; scores items with Groq (Llama 70B) for relevance and viral potential; writes to Supabase.
- **Ktor API** -- REST server for desktop/Android clients (items, favorites, notes, agent chat, search, sync status, stats).
- **MCP server** -- exposes settings (topics, sources, thresholds, schedule) as MCP tools so any MCP-compatible AI client (Claude Desktop, Claude Code) can read and modify your configuration through conversation.
- **Desktop control panel** (`app/`) -- a Windows GUI (system tray + window) that wraps all three: API key setup with inline instructions, Ktor server start/stop/status, a pipeline scheduler, settings, and a one-click MCP config helper. Packaged into a single installer (see below) with a bundled JRE and Python -- no separate Java/Python install needed.

## Desktop app (recommended)

Download/build `FomoSetup.exe` (see `installer/README` below) and run it -- no admin rights,
no command line. It installs to `%LOCALAPPDATA%\FOMO`, adds a Start Menu shortcut, and optionally
starts at login. First launch walks you through:

1. **Setup** -- paste in your Supabase/Groq/Reddit/YouTube keys (each field links to where to get it).
2. **Dashboard** -- start/stop the Ktor API, watch its logs, and trigger a manual collection run.
3. **Settings** -- relevance threshold, retention days, schedule, topics, and sources.
4. **MCP** -- copy-paste config for Claude Desktop, pointing at the app itself (no separate Python needed).

To build the installer yourself: `JAVA_HOME=<jdk 23+> pwsh installer/build.ps1` (requires the Ktor
JDK, `uv`, and Inno Setup 6+). It builds the Ktor fat jar, a jlink'd minimal JRE, the PyInstaller
onedir bundle, and compiles `installer/output/FomoSetup.exe`.

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
    lobsters.py             # Lobsters hottest.json
    devto.py                # Dev.to top articles
    mastodon.py             # Mastodon trending links
    arxiv.py                # arXiv cs.AI/cs.LG feed
    huggingface.py          # Hugging Face trending models
    stackexchange.py        # Stack Exchange hot questions
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

app/                         # Desktop control panel (pywebview + pystray)
  main.py                    # Entry point; also handles hidden --run-pipeline-once / --mcp-server flags
  api_bridge.py              # window.pywebview.api.* -- backs all four views
  ktor_manager.py            # Starts/stops the bundled Ktor jar, tails its logs
  scheduler.py               # Background thread firing collector->filter on a schedule
  tray.py                    # System tray icon (Open/Start/Stop/Run Now/Quit)
  secrets_store.py           # Reads/writes backend/.env, generates API_AUTH_TOKEN
  mcp_config.py              # Builds the Claude Desktop config snippet
  views/                     # setup.html, dashboard.html, settings.html, mcp.html
  pyinstaller.spec

serve.py                     # Python reverse proxy (port 8080) — see "Test UI" section
test-ui.html                 # Standalone HTML/JS/CSS test UI

installer/
  build.ps1                  # Stages jre/ + ktor/ + PyInstaller output, runs Inno Setup
  trendhopper.iss             # Inno Setup script (per-user install, no admin)

supabase/
  001_schema.sql            # Full database schema + seed data

.github/workflows/
  daily-collect.yml         # Cron schedule (6/12/18 UTC) with retention cleanup
```

## Setup (development / manual)

The desktop app above is the recommended path for normal use. The steps below are for developing
the individual components directly.

### Prerequisites

- Python 3.12+
- Java 21+ (Gradle 9.6+)
- A Supabase project
- API keys: Groq, Reddit (client ID + secret), YouTube

### Database

Run `supabase/001_schema.sql` in your Supabase SQL editor. This creates all tables (settings, topics, sources_config, items, favorites, notes, agent_chats, sync_log) with seed data for default topics and sources. Then run `supabase/002_add_llm_reasoning.sql` and `supabase/003_add_sources.sql` for the LLM reasoning column and the six keyless sources (Lobsters, Dev.to, Mastodon, arXiv, Hugging Face, Stack Exchange).

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
export JAVA_HOME=/path/to/jdk-23+
./gradlew buildFatJar
SUPABASE_URL=... SUPABASE_KEY=... GROQ_API_KEY=... API_AUTH_TOKEN=... java -jar build/libs/trend-hopper-api.jar
```

The API serves on port 8080 (configurable via `PORT` env var). All routes except `GET /health`
require `Authorization: Bearer <API_AUTH_TOKEN>` -- the server refuses to start if `API_AUTH_TOKEN`
isn't set. CORS is restricted to `localhost`/`127.0.0.1` on the configured port.

### MCP server

The desktop app's **MCP** tab generates this for you (pointing at the app itself, so Claude
Desktop doesn't need a separate Python install). To wire it up manually instead, add the
following to your `claude_desktop_config.json`:

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

## Test UI

A standalone HTML/JS/CSS test UI (`test-ui.html`) is served by a Python reverse proxy (`serve.py`). This is not a React app — it's a single-file UI for testing the API without rebuilding anything.

### Running

```bash
# Start the Ktor backend on port 8081
cd ktor-api
java -jar build/libs/trend-hopper-api.jar

# In another terminal, start the proxy on port 8080
python serve.py
# Opens at http://localhost:8080
```

### Features

- **Dashboard**: stat cards, topic pills, calendar heatmap, recent items, source list
- **Favorites**: favorited items with notes/chat indicators
- **Detail page**: full-page view with hero image, YouTube embeds, article images grid
- **Full article tab**: Medium-style formatting (drop caps, headings, blockquotes, code blocks)
- **AI Format button**: calls Groq to reformat article text into clean HTML
- **Chat with Agent**: sends messages to Groq with article context, persists history
- **Search**: full-text search across items, topics, and sources
- **Log panel**: fixed bottom-right, auto-opens on errors

### Architecture

```
Browser (localhost:8080)
  ├── GET /                    → serve.py → test-ui.html
  ├── GET /api/agent/chat/*    → serve.py → Supabase REST API
  ├── POST /api/agent/chat/*   → serve.py → Supabase + Groq
  ├── POST /api/format-article → serve.py → Groq
  └── everything else          → serve.py → Ktor (localhost:8081)
```

The proxy strips browser headers (`Origin`, `Sec-Fetch-*`, `Referer`) that cause Ktor CORS/auth errors on POST requests. Chat and formatting endpoints go directly to Supabase/Groq through the proxy, bypassing a Ktor double-encoding bug in the chat route.
