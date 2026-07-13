-- Proposal only. Review in a non-production project before applying.
create extension if not exists pgcrypto;

create table if not exists public.scrape_runs (
    id uuid primary key default gen_random_uuid(),
    execution_id text not null unique,
    source text not null,
    started_at timestamptz not null,
    finished_at timestamptz,
    status text not null check (status in ('RUNNING','SCRAPED','EMPTY','FAILED','READY_FOR_APPROVAL','QUALITY_REJECTED','PUBLISHED')),
    trigger_type text not null check (trigger_type in ('manual','github_actions','n8n','smoke_test')),
    products_read integer not null default 0 check (products_read >= 0),
    products_valid integer not null default 0 check (products_valid >= 0),
    products_invalid integer not null default 0 check (products_invalid >= 0),
    incidents integer not null default 0 check (incidents >= 0),
    extractor_version text not null,
    error_summary text,
    created_at timestamptz not null default now()
);

comment on table public.scrape_runs is 'One idempotent execution of an official source adapter.';

create table if not exists public.price_observations (
    id uuid primary key default gen_random_uuid(),
    run_id uuid not null references public.scrape_runs(id) on delete cascade,
    comercio text not null,
    sucursal text not null,
    localidad text not null,
    canal_precio text not null check (canal_precio in ('ONLINE','TIENDA_FISICA','CATALOGO','MANUAL','CONTROL')),
    producto text not null,
    marca text,
    categoria text,
    presentacion text,
    sku text,
    ean text,
    precio_regular numeric(14,2) check (precio_regular > 0),
    precio_promocional numeric(14,2) check (precio_promocional > 0),
    precio_efectivo numeric(14,2) not null check (precio_efectivo > 0),
    condicion_promocion text,
    medio_pago text,
    stock_publicado numeric,
    observed_at timestamptz not null,
    url_origen text not null,
    quality_status text not null default 'PENDING' check (quality_status in ('PENDING','OK','REVISAR','INVALIDO','DESACTUALIZADO')),
    raw_hash char(64) not null,
    created_at timestamptz not null default now(),
    unique (run_id, raw_hash)
);

comment on column public.price_observations.canal_precio is 'Prevents online prices from being represented as physical store prices.';

create table if not exists public.publication_runs (
    id uuid primary key default gen_random_uuid(),
    scrape_run_id uuid not null references public.scrape_runs(id),
    status text not null check (status in ('PENDING','DRY_RUN','PUBLISHED','REJECTED','FAILED')),
    approved_by text,
    approved_at timestamptz,
    published_at timestamptz,
    dataset_path text,
    rows_published integer not null default 0 check (rows_published >= 0),
    notes text,
    created_at timestamptz not null default now(),
    unique (scrape_run_id, status)
);

create table if not exists public.source_health (
    source text primary key,
    last_success_at timestamptz,
    last_failure_at timestamptz,
    consecutive_failures integer not null default 0 check (consecutive_failures >= 0),
    average_duration_seconds numeric(12,3),
    last_error text,
    extractor_version text not null,
    updated_at timestamptz not null default now()
);

create table if not exists public.execution_events (
    id bigint generated always as identity primary key,
    execution_id text not null,
    run_id uuid references public.scrape_runs(id) on delete cascade,
    event_type text not null,
    status text not null,
    message text,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_price_observations_source_time on public.price_observations (comercio, observed_at desc);
create index if not exists idx_price_observations_product on public.price_observations (producto);
create index if not exists idx_price_observations_raw_hash on public.price_observations (raw_hash);
create index if not exists idx_execution_events_execution_id on public.execution_events (execution_id, created_at);
create index if not exists idx_publication_runs_created_at on public.publication_runs (created_at desc);

alter table public.scrape_runs enable row level security;
alter table public.price_observations enable row level security;
alter table public.publication_runs enable row level security;
alter table public.source_health enable row level security;
alter table public.execution_events enable row level security;

-- No anonymous policies are created. The backend service role is the only writer.
