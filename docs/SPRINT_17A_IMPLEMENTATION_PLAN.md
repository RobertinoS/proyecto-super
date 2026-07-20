# Sprint 17A - Auth contracts and RBAC

## Objective

Add the minimum human identity boundary for private dataset consumption without
enabling downloads, dataset activation, revocation, live collection, schedule,
or any publication path. Supabase Auth issues human JWTs; FastAPI verifies
them, resolves active roles from the isolated Proyecto Super staging database,
and writes a minimised audit event.

## Scope

Allowed changes are additive FastAPI security code, Supabase migration `004`,
static migration validation, tests, dependency metadata, and documentation.
Machine endpoints retain `X-API-Key` authentication. No existing n8n endpoint
is converted to Bearer authentication.

Out of scope: signed URLs, downloads, dataset activation/revocation/restore,
role management UI, Auth Hook claims, dashboard changes, live scraping,
publication, schedules, external migration execution, deployment, and user
creation.

## Architecture

1. A browser sends `Authorization: Bearer <Supabase JWT>` only to human API
   endpoints.
2. FastAPI validates algorithm, signature through JWKS, issuer, expiry, and a
   configured audience when present.
3. FastAPI obtains active roles from `app_user_roles` through its server-side
   Supabase service-role connection. Browser roles have no direct table access.
4. The API derives capabilities and writes a minimal `dataset_access_logs`
   audit row keyed by user and request ID. Tokens, API keys, full headers, IP
   addresses, and signed URLs are never stored.
5. n8n and GitHub Actions remain machine callers authenticated only by
   `X-API-Key`.

## Files

Expected changes: `cloud_backend/app/`, `cloud_backend/requirements-cloud.txt`,
`.env.example`, `supabase/migrations/004_auth_roles_and_access_audit.sql`,
`scripts/13_validate_supabase_migrations.py`, `cloud_backend/tests/`, root
contract tests, and documentation.

Forbidden changes: existing migrations `001`-`003`, dashboard frontend,
production/staging infrastructure, real `.env` files, raw/processed data,
workflows, schedules, publication flags, and Supabase Auth users.

## Threat model and controls

| Threat | Control |
| --- | --- |
| Forged or stale JWT | JWKS signature, fixed asymmetric algorithms, issuer, expiry, and optional audience validation. |
| JWKS key rotation | Bounded in-memory cache refreshes once when an unknown `kid` is encountered. |
| Browser obtains service permissions | RLS plus revoked `anon`/`authenticated` table privileges; FastAPI alone uses service role. |
| Role claim tampering | Roles come from `app_user_roles`, not unverified token claims. |
| Replay/audit duplication | `dataset_access_logs` is unique on `(user_id, request_id)`. |
| Accidental machine regression | Existing endpoints retain `require_service_api_key`; Bearer JWT does not substitute it. |
| Secret leakage | No token or header persistence; placeholder-only environment configuration; static secret scan. |

## Rollback and cut-off

Rollback is a source rollback to `v1.8.0` / `7a68b0d` and deployment rollback
only after a later explicit staging deployment. Migration `004` is additive and
is not applied during this sprint. Stop before a checkpoint if tests regress,
a secret appears, JWT validation accepts an unexpected algorithm, browser roles
get direct database access, a service endpoint loses API-key protection, or any
publication flag changes from `false`.

## Acceptance criteria

- JWT validation is cryptographic and offline-testable.
- Active roles drive capabilities and can be multiple per user.
- `/auth/me` and `/auth/capabilities` expose only safe identity metadata.
- Existing n8n/GitHub Actions endpoints keep working with `X-API-Key`.
- Migration `004` is additive, RLS-protected, and audit-only.
- No signed URL, download, activation, revocation, restore, deployment, or
  external SQL execution is introduced.
