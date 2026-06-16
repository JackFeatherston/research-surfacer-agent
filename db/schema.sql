-- Research Surface Tool — Supabase schema.
-- Studies and their quotes. quotes.ordinal preserves the per-study quote order
-- the pipeline relies on (analyze() indexes study["quotes"][i]).

create table studies (
  id      text primary key,
  title   text not null,
  team    text not null,
  date    date not null,
  url     text not null,
  tags    text[] not null default '{}',
  summary text not null
);

create table quotes (
  id                   bigint generated always as identity primary key,
  study_id             text not null references studies(id) on delete cascade,
  ordinal              int  not null,
  text                 text not null,
  speaker              text not null,
  timestamp_or_section text not null
);

create index on quotes (study_id, ordinal);

-- Demo: anon key + public read so the SDK can select without auth.
alter table studies enable row level security;
alter table quotes  enable row level security;
create policy "public read studies" on studies for select using (true);
create policy "public read quotes"  on quotes  for select using (true);
