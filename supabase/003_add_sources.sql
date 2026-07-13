-- New keyless sources: lobsters, dev.to, mastodon trending links,
-- arxiv, hugging face trending models, stack exchange hot questions
insert into sources_config (name, enabled, params) values
  ('lobsters', true, '{"limit": 25}'),
  ('devto', true, '{"limit": 20, "tag": ""}'),
  ('mastodon', true, '{"instance": "https://mastodon.social", "limit": 20}'),
  ('arxiv', true, '{"categories": ["cs.AI", "cs.LG"], "limit": 20}'),
  ('huggingface', true, '{"limit": 20}'),
  ('stackexchange', true, '{"site": "stackoverflow", "limit": 20}')
on conflict (name) do nothing;
