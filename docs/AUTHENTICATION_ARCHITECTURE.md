# Autenticacion humana Sprint 17A

## Boundary

Supabase Auth is the identity provider for people. The backend FastAPI is the
policy enforcement point. n8n and GitHub Actions are machine callers and keep
their independent `X-API-Key` contract; a Bearer token never authorizes a
machine endpoint.

```text
Human browser -> Authorization: Bearer JWT -> FastAPI
                                      -> JWKS signature + issuer + exp + audience
                                      -> app_user_roles (active roles only)
                                      -> capability response + minimal access audit

n8n/GitHub -> X-API-Key -> existing machine endpoints
```

## JWT validation

`get_current_user` accepts a Bearer token only on human endpoints. The backend
accepts only `RS256` or `ES256` headers with a `kid`; it resolves the public
key through `SUPABASE_AUTH_JWKS_URL`, validates the signature, configured
issuer, expiration, subject, and configured audience. Tokens with `none`, HMAC
or any unrecognised algorithm are rejected.

JWKS is cached in memory for `AUTH_JWKS_CACHE_SECONDS` (default 3600). An
unknown `kid` performs one forced refresh, which permits a normal key rotation
without making a network call for each request. Pytest injects local test keys
and a mock JWKS fetcher; it never calls Supabase or the internet.

The API returns generic 401/503 messages. It never records JWTs, API keys,
headers, issuer errors, or provider response details.

## Roles and capabilities

Roles are fetched server side from `public.app_user_roles` and only rows with
`active=true` are effective. FastAPI does not rely on JWT role claims in this
sprint. The table is RLS-protected and has no direct `anon` or
`authenticated` privileges.

See `docs/RBAC_MATRIX.md` for the capability map. `require_any_role` and
`require_all_roles` are reusable dependency factories. The future
two-responsible restore rule is represented as `require_distinct_actors`, but
restore itself is not implemented.

## Access audit

Each accepted human request writes an `AUTHENTICATED` record to
`dataset_access_logs` using an application request ID. `(user_id, request_id)`
is unique so a retry is idempotent. The snapshot contains only active role
names. There is no raw IP address, header, JWT, API key or signed URL.

Retention is configured as `DATASET_ACCESS_LOG_RETENTION_DAYS=365`; deletion
and retention automation are deliberately deferred to a controlled future
operation.

## Configuration and rollback

Only placeholders are committed in `.env.example`:

```text
SUPABASE_AUTH_ISSUER
SUPABASE_AUTH_AUDIENCE
SUPABASE_AUTH_JWKS_URL
AUTH_JWKS_CACHE_SECONDS=3600
DATASET_ACCESS_LOG_RETENTION_DAYS=365
```

Real values belong exclusively in Render environment secrets after a separate
staging approval. Migration `004` was applied only in isolated staging. The
external validation of human login and password recovery remains pending, so
the JWT/RBAC path is architecture-ready but not a production human
authentication service. Roll back code to `v1.8.0` if auth regressions appear;
do not undo the migration with destructive SQL.
