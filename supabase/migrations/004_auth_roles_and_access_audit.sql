-- Sprint 17A. Additive identity/RBAC and access-audit foundation.
-- Apply only to the isolated proyecto-super-staging project after separate
-- approval. This migration never touches the Supabase database used by n8n.

create table if not exists public.app_user_roles (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete restrict,
    role text not null check (role in ('viewer', 'reviewer', 'dataset_admin', 'operator')),
    active boolean not null default true,
    assigned_by uuid references auth.users(id) on delete restrict,
    assigned_at timestamptz not null default now(),
    revoked_by uuid references auth.users(id) on delete restrict,
    revoked_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (user_id, role),
    check ((active and revoked_at is null and revoked_by is null) or (not active))
);

create table if not exists public.dataset_access_logs (
    id uuid primary key default gen_random_uuid(),
    dataset_id uuid references public.private_datasets(id) on delete restrict,
    user_id uuid not null references auth.users(id) on delete restrict,
    action text not null check (action in (
        'AUTHENTICATED', 'METADATA_VIEWED', 'ACCESS_REQUESTED', 'ACCESS_GRANTED',
        'ACCESS_DENIED', 'URL_ISSUED', 'URL_EXPIRED'
    )),
    result text not null check (result in ('ALLOWED', 'DENIED', 'PENDING', 'EXPIRED')),
    request_id text not null,
    role_snapshot jsonb not null default '[]'::jsonb,
    expires_at timestamptz,
    denial_reason text,
    client_fingerprint_hash char(64),
    created_at timestamptz not null default now(),
    unique (user_id, request_id)
);

create index if not exists idx_app_user_roles_active
    on public.app_user_roles (user_id, active, role);
create index if not exists idx_dataset_access_logs_user_created
    on public.dataset_access_logs (user_id, created_at desc);
create index if not exists idx_dataset_access_logs_dataset_created
    on public.dataset_access_logs (dataset_id, created_at desc);
create index if not exists idx_dataset_access_logs_action_created
    on public.dataset_access_logs (action, created_at desc);

comment on table public.app_user_roles is
    'Active human roles for Proyecto Super. Managed only by the protected FastAPI backend.';
comment on table public.dataset_access_logs is
    'Minimal 365-day access audit. Never stores JWTs, API keys, headers, full IPs, or signed URLs.';
comment on column public.dataset_access_logs.client_fingerprint_hash is
    'Optional one-way client fingerprint. It is not a raw IP address or header value.';

alter table public.app_user_roles enable row level security;
alter table public.dataset_access_logs enable row level security;

revoke all on table public.app_user_roles from anon, authenticated;
revoke all on table public.dataset_access_logs from anon, authenticated;
