# Internal private dataset access pilot

## Purpose

Sprint 17B adds a backend-only internal pilot. An authorised operator calls
FastAPI from Swagger or PowerShell with the existing `X-API-Key`. It is not a
browser login path and no API key may be copied into dashboard JavaScript,
localStorage, URLs, screenshots, or documentation examples.

Supabase Auth/JWT and RBAC from Sprint 17A remain in the codebase, but their
external login validation is still pending. They are not an operational
requirement for this pilot.

## Internal routes

All routes require `X-API-Key` and are deliberately namespaced under
`/internal`:

| Route | Function |
| --- | --- |
| `GET /internal/private-datasets` | List safe metadata for eligible datasets. |
| `GET /internal/private-datasets/current` | Return newest `ACTIVE`, then eligible `PUBLISHED_PRIVATE`. |
| `GET /internal/private-datasets/{dataset_id}` | Return safe metadata for one eligible dataset. |
| `POST /internal/private-datasets/{dataset_id}/access` | Request one temporary signed URL using `request_id`. |
| `GET /internal/private-datasets/{dataset_id}/audit` | Read sanitized access-audit events. |

Metadata omits dataset and manifest paths. Audit output omits signed URLs,
headers, keys and fingerprints.

## Access decision

An access request succeeds only when all conditions hold:

1. Dataset status is `PUBLISHED_PRIVATE` or `ACTIVE`.
2. It is not `REVOKED` and has an associated `APPROVED` approval.
3. A checksum exists.
4. `published-price-datasets` is private.
5. The storage object exists.
6. `ENABLE_INTERNAL_DATASET_ACCESS=true` was set deliberately for a controlled
   staging test.

The default is `false`, so list/metadata can be used but URL creation returns
409. A missing dataset returns 404, revoked returns 410, non-eligible returns
409, missing/invalid service key returns 401/403, and storage failure returns
503.

## Temporary URL and audit

FastAPI limits each signed URL to 300 seconds. The complete URL is held only
in process memory to answer an immediate duplicate request; it is never stored
in `dataset_access_logs`. The durable audit row records `actor_type=service`,
dataset ID, action, result, request ID, expiry and a safe denial reason.

`(actor_type, request_id)` is unique. The same request ID receives the cached
URL during its window and cannot create another signed access after that cache
is gone. Use a new request ID for a fresh, separately audited request.

## Migration 005 and rollback

`005_internal_dataset_access_audit.sql` is required because migration 004
only supports a human `user_id` and legacy dataset states. It makes `user_id`
nullable for service rows, adds `actor_type` and service idempotency, and
extends the status check without deleting history. The old
`PRIVATE_PUBLISHED` state remains ineligible by design.

Do not apply 005 outside `proyecto-super-staging`, and do not apply it during
this sprint without explicit approval. Roll back the backend to the Sprint 17A
checkpoint or `v1.8.0` and leave all access/publication flags `false` if a
regression appears. Do not delete audit evidence or reverse the migration with
destructive SQL.

## Migration to human JWT later

After Supabase Auth login is externally validated, Sprint 17C can add parallel
human routes protected by `require_authenticated_user` and roles from
`app_user_roles`. It must not repurpose the internal routes or send the service
API key to the frontend. Human access logs use `actor_type=human`; service
routes remain available only for controlled operations.
