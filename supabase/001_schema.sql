-- Trend Hopper Schema

-- Settings
create table settings (
  key text primary key,
  value text not null,
  updated_at timestamptz not null default now()
);

-- Topics
create table topics (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

-- Source configurations
create table sources_config (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  enabled boolean not null default true,
  params jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

-- Items (raw fetched + scored)
create table items (
  id uuid primary key default gen_random_uuid(),
  source text not null,
  title text not null,
  url text not null,
  text_content text,
  content_hash text not null unique,
  relevance_score int,
  viral_score float,
  matched_topic text,
  llm_summary text,
  llm_reasoning text,
  image_url text,
  published_at timestamptz,
  fetched_at timestamptz not null default now(),
  never_favorited boolean not null default true
);
create index idx_items_fetched_at on items(fetched_at);
create index idx_items_relevance_score on items(relevance_score);
create index idx_items_viral_score on items(viral_score);
create index idx_items_content_hash on items(content_hash);

-- Favorites
create table favorites (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null references items(id) on delete restrict,
  user_id text not null default 'default',
  created_at timestamptz not null default now(),
  unique(item_id, user_id)
);
create index idx_favorites_user_id on favorites(user_id);

-- Notes on favorites
create table notes (
  id uuid primary key default gen_random_uuid(),
  favorite_id uuid not null references favorites(id) on delete cascade,
  content text not null,
  updated_at timestamptz not null default now()
);
create unique index idx_notes_favorite_id on notes(favorite_id);

-- Agent chat threads per favorite
create table agent_chats (
  id uuid primary key default gen_random_uuid(),
  favorite_id uuid not null references favorites(id) on delete cascade,
  messages jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);
create unique index idx_agent_chats_favorite_id on agent_chats(favorite_id);
create index idx_agent_chats_messages on agent_chats using gin(messages);

-- Sync log (append-only)
create table sync_log (
  id bigserial primary key,
  status text not null check (status in ('synced', 'syncing', 'failed', 'offline')),
  last_error_reason text,
  last_successful_sync_at timestamptz,
  created_at timestamptz not null default now()
);

-- Seed default settings
insert into settings (key, value) values
  ('RELEVANCE_THRESHOLD', '50'),
  ('RETENTION_DAYS', '30'),
  ('VIRAL_KEEP_COUNT', '5'),
  ('SCHEDULE_TIME', '06:00'),
  ('SCHEDULE_TIMEZONE', 'UTC');

-- Seed default topics
insert into topics (name, active) values
  ('Technology', true),
  ('AI & Machine Learning', true),
  ('Programming', true),
  ('Startups', true),
  ('Design', true);

-- Seed default sources
insert into sources_config (name, enabled, params) values
  ('reddit', true, '{"subreddits": ["technology", "programming", "MachineLearning", "startups", "artificial"], "sort": "hot", "limit": 25}'),
  ('hackernews', true, '{"type": "top", "limit": 30}'),
  ('github_trending', true, '{"language": "", "since": "daily"}'),
  ('rss', true, '{"feeds": ["https://feeds.feedburner.com/TechCrunch", "https://hnrss.org/frontpage"]}'),
  ('youtube', true, '{"max_results": 10, "query": "tech news"}'),
  ('soundcloud', false, '{"genre": "electronic", "limit": 10}');
