-- Non-destructive staging hardening. Apply only after 001 in the dedicated
-- proyecto-super-staging Supabase project.

alter table public.scrape_runs
    add column if not exists trigger_context text not null default 'manual',
    add column if not exists app_env text not null default 'staging'
        check (app_env in ('local', 'test', 'staging', 'production')),
    add column if not exists updated_at timestamptz not null default now();

comment on column public.scrape_runs.trigger_context is
    'Original API trigger label. manual_staging persists as trigger_type=manual and trigger_context=manual_staging.';

alter table public.source_health
    add column if not exists last_result text
        check (last_result in ('SUCCESS', 'FAILURE'));

create index if not exists idx_scrape_runs_status_started
    on public.scrape_runs (status, started_at desc);

create unique index if not exists uq_execution_events_idempotent
    on public.execution_events (execution_id, event_type, status);

-- Keep all application tables inaccessible to browser roles. The backend uses
-- the service role only from Render; RLS from migration 001 remains enabled.
revoke all on table public.scrape_runs from anon, authenticated;
revoke all on table public.price_observations from anon, authenticated;
revoke all on table public.publication_runs from anon, authenticated;
revoke all on table public.source_health from anon, authenticated;
revoke all on table public.execution_events from anon, authenticated;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values
    ('raw-price-snapshots', 'raw-price-snapshots', false, 10485760, array['application/json']),
    ('processed-price-datasets', 'processed-price-datasets', false, 10485760, array['text/csv', 'application/csv']),
    ('published-price-datasets', 'published-price-datasets', false, 10485760, array['text/csv', 'application/csv'])
on conflict (id) do update
set public = false,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;
