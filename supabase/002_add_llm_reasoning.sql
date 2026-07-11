-- Add llm_reasoning and image_url columns to items table
alter table items add column if not exists llm_reasoning text;
alter table items add column if not exists image_url text;
