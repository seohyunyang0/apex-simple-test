create extension if not exists pgcrypto;

create table if not exists public.apex_test_results (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null,
  score_total numeric(5,1) not null,
  percentile numeric(5,1) not null,
  tier_key text not null,
  tier_name text not null,
  strongest_area text,
  weakest_area text,
  part_scores jsonb not null default '{}'::jsonb,
  subscores jsonb not null default '{}'::jsonb,
  responses jsonb not null default '{}'::jsonb,
  page_url text,
  user_agent text,
  created_at_client timestamptz,
  created_at timestamptz not null default now()
);

alter table public.apex_test_results enable row level security;

drop policy if exists "public insert apex test results" on public.apex_test_results;
create policy "public insert apex test results"
on public.apex_test_results
for insert
to anon
with check (true);

drop policy if exists "public read own nothing" on public.apex_test_results;
create policy "public read own nothing"
on public.apex_test_results
for select
to anon
using (false);
