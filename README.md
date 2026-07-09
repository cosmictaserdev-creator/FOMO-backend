# Trend Hopper

Personal tech trends aggregator with three backend components:

- **Python service layer** — fetches from Reddit, HN, GitHub Trending, RSS, YouTube, SoundCloud; scores with Groq LLM
- **Ktor API** — serves desktop/Android clients with items, favorites, notes, and agent chat
- **MCP server** — exposes config (topics, sources, thresholds) as MCP tools for AI assistants

## Project structure

```
trend-hopper/
  backend/                    # Python service layer + MCP server
    collector.py              # Orchestrates all source fetchers
    filter.py                 # Groq relevance/viral scoring
    run_daily.py              # Local trigger with today-run guard
    db.py                     # Supabase client wrapper
    config.py                 # Settings/topics/sources loaders from Supabase
    mcp_server.py             # MCP tool definitions
    sources/
      reddit.py
      hackernews.py
      github_trending.py
      rss.py
      youtube.py
      soundcloud.py
    pyproject.toml
    .env.example
  ktor-api/                   # Ktor REST server
    build.gradle.kts
    src/main/kotlin/com/trendhopper/
      Application.kt
      plugins/                # Serialization, Auth, CORS, StatusPages
      routes/                 # All endpoint handlers
      models/                 # Request/response data classes
      services/               # Supabase client
  supabase/
    001_schema.sql            # Database migration
  .github/workflows/
    daily-collect.yml         # Scheduled collection pipeline
```

## Setup

### Prerequisites
- Python 3.12+, Java 21+, Supabase project
- API keys: Groq, Reddit, YouTube

### Backend
```bash
cd backend
uv sync
cp .env.example .env   # fill in your keys
uv run python collector.py
uv run python filter.py
```

### Ktor API
```bash
cd ktor-api
./gradlew build
SUPABASE_URL=... SUPABASE_KEY=... GROQ_API_KEY=... java -jar build/libs/trend-hopper-api.jar
```

### MCP server
Add to `claude_desktop_config.json` (see `backend/mcp_config_example.json`).

### Database
Run `supabase/001_schema.sql` in your Supabase SQL editor.

### GitHub Actions
Set the following secrets in your repo:
- `SUPABASE_URL`, `SUPABASE_KEY`, `GROQ_API_KEY`
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `YOUTUBE_API_KEY`

### Windows Task Scheduler
Create a task trigger "At log on" with action: `pythonw.exe path/to/backend/run_daily.py`
