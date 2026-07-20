-- Sprint 17B. Minimal extension for backend-only internal dataset access.
-- Apply only to the isolated proyecto-super-staging project after separate
-- approval. This migration never touches the Supabase database used by n8n.

-- A service caller has no auth.users identity. Human audit rows remain valid.
alter table public.dataset_access_logs
    alter column user_id drop not null;

alter table public.dataset_access_logs
    add column if not exists actor_type text not null default 'service';

do $$
begin
    if not exists (
        select 1 from pg_constraint
        where conname = 'dataset_access_logs_actor_type_check'
          and conrelid = 'public.dataset_access_logs'::regclass
    ) then
        alter table public.dataset_access_logs
            add constraint dataset_access_logs_actor_type_check
            check (actor_type in ('service', 'human', 'system'));
    end if;
end $$;

-- Existing (user_id, request_id) uniqueness remains for human calls. The new
-- index gives service calls durable idempotency when user_id is null.
create unique index if not exists uq_dataset_access_logs_actor_request
    on public.dataset_access_logs (actor_type, request_id);
create index if not exists idx_dataset_access_logs_actor_created
    on public.dataset_access_logs (actor_type, created_at desc);

-- Preserve historical statuses. Only the backend access service permits the
-- two new statuses; PRIVATE_PUBLISHED is never retroactively exposed.
do $$
begin
    if exists (
        select 1 from pg_constraint
        where conname = 'private_datasets_status_check'
          and conrelid = 'public.private_datasets'::regclass
    ) then
        alter table public.private_datasets
            drop constraint private_datasets_status_check;
    end if;
end $$;

alter table public.private_datasets
    add constraint private_datasets_status_check
    check (status in (
        'PRIVATE_DRY_RUN', 'PRIVATE_PUBLISHED', 'PUBLISHED_PRIVATE', 'ACTIVE', 'REVOKED'
    ));

comment on column public.dataset_access_logs.actor_type is
    'Origin category only: service, human, or system. Never store API keys or JWTs.';
comment on constraint private_datasets_status_check on public.private_datasets is
    'Historical statuses are retained; only PUBLISHED_PRIVATE and ACTIVE are eligible for internal access.';

alter table public.dataset_access_logs enable row level security;
revoke all on table public.dataset_access_logs from anon, authenticated;
