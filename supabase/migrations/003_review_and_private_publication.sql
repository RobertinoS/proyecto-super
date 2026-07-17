-- Review, observability, and private-publication controls for the isolated
-- proyecto-super-staging project. This migration is additive and must not be
-- applied to any unrelated operational project.

create table if not exists public.review_queue (
    id uuid primary key default gen_random_uuid(),
    scrape_run_id uuid not null references public.scrape_runs(id) on delete cascade,
    observation_id uuid references public.price_observations(id) on delete set null,
    source text not null,
    review_type text not null check (review_type in (
        'PRICE_SUSPICIOUS', 'DUPLICATE', 'SOURCE_CONFLICT', 'MISSING_FIELD',
        'QUALITY_WARNING', 'OUTLIER', 'SOURCE_FAILURE'
    )),
    severity text not null check (severity in ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    status text not null default 'PENDING' check (status in (
        'PENDING', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'CORRECTED', 'DISMISSED'
    )),
    reason text not null,
    detected_value jsonb not null default '{}'::jsonb,
    suggested_action text,
    assigned_to text,
    reviewed_by text,
    reviewed_at timestamptz,
    decision text,
    decision_notes jsonb not null default '{}'::jsonb,
    idempotency_key text not null unique,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.review_decisions (
    id uuid primary key default gen_random_uuid(),
    review_id uuid not null references public.review_queue(id) on delete cascade,
    action text not null check (action in ('APPROVE', 'REJECT', 'CORRECT', 'DISMISS')),
    actor text not null,
    notes text,
    previous_value jsonb not null default '{}'::jsonb,
    corrected_value jsonb,
    idempotency_key text not null unique,
    created_at timestamptz not null default now()
);

create table if not exists public.dataset_approvals (
    id uuid primary key default gen_random_uuid(),
    scrape_run_id uuid not null unique references public.scrape_runs(id) on delete cascade,
    status text not null default 'PENDING_REVIEW' check (status in (
        'PENDING_REVIEW', 'READY_FOR_APPROVAL', 'APPROVED', 'REJECTED', 'REVOKED'
    )),
    requested_at timestamptz not null default now(),
    requested_by text,
    approved_by text,
    approved_at timestamptz,
    rejected_by text,
    rejected_at timestamptz,
    rejection_reason text,
    quality_score numeric(5,2) check (quality_score >= 0 and quality_score <= 100),
    pending_items integer not null default 0 check (pending_items >= 0),
    approved_items integer not null default 0 check (approved_items >= 0),
    rejected_items integer not null default 0 check (rejected_items >= 0),
    idempotency_key text not null unique,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.operational_alerts (
    id uuid primary key default gen_random_uuid(),
    source text,
    run_id uuid references public.scrape_runs(id) on delete set null,
    alert_type text not null,
    severity text not null check (severity in ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    status text not null default 'OPEN' check (status in ('OPEN', 'ACKNOWLEDGED', 'RESOLVED')),
    message text not null,
    metadata jsonb not null default '{}'::jsonb,
    acknowledged_by text,
    acknowledged_at timestamptz,
    idempotency_key text not null unique,
    created_at timestamptz not null default now()
);

create table if not exists public.private_datasets (
    id uuid primary key,
    scrape_run_id uuid not null references public.scrape_runs(id) on delete cascade,
    approval_id uuid not null unique references public.dataset_approvals(id) on delete restrict,
    status text not null check (status in ('PRIVATE_DRY_RUN', 'PRIVATE_PUBLISHED', 'REVOKED')),
    dataset_path text not null,
    manifest_path text not null,
    row_count integer not null check (row_count >= 0),
    checksum_sha256 char(64) not null,
    approved_by text not null,
    quality_score numeric(5,2) check (quality_score >= 0 and quality_score <= 100),
    created_at timestamptz not null default now(),
    unique (scrape_run_id, checksum_sha256)
);

create index if not exists idx_review_queue_run_status
    on public.review_queue (scrape_run_id, status, severity);
create index if not exists idx_review_queue_pending
    on public.review_queue (status, created_at desc);
create index if not exists idx_review_decisions_review
    on public.review_decisions (review_id, created_at desc);
create index if not exists idx_dataset_approvals_status
    on public.dataset_approvals (status, requested_at desc);
create index if not exists idx_operational_alerts_status
    on public.operational_alerts (status, severity, created_at desc);
create index if not exists idx_private_datasets_created
    on public.private_datasets (created_at desc);

comment on table public.review_queue is
    'Durable human-review work items. Browser roles have no direct access.';
comment on table public.dataset_approvals is
    'Idempotent run-level decision gate before a private dataset can be produced.';
comment on table public.operational_alerts is
    'Operational alerts generated by the backend or orchestrator without secret metadata.';
comment on table public.private_datasets is
    'Durable manifest index for approved private datasets. Storage stays private.';

alter table public.review_queue enable row level security;
alter table public.review_decisions enable row level security;
alter table public.dataset_approvals enable row level security;
alter table public.operational_alerts enable row level security;
alter table public.private_datasets enable row level security;

revoke all on table public.review_queue from anon, authenticated;
revoke all on table public.review_decisions from anon, authenticated;
revoke all on table public.dataset_approvals from anon, authenticated;
revoke all on table public.operational_alerts from anon, authenticated;
revoke all on table public.private_datasets from anon, authenticated;
