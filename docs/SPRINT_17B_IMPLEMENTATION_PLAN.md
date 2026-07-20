# Sprint 17B - Internal private dataset access

## Objective

Provide a backend-only pilot for controlled consumption of approved private
datasets. Internal operators use the existing `X-API-Key` through Swagger or
PowerShell. This is not human authentication, a browser feature, public
publication, or a deployment instruction.

## Git base decision

This branch starts at Sprint 17A commit `2c48d41`, not directly at `main`.
Sprint 17A remains separate and unmerged, while its applied staging migration
`004` supplies the access-audit table required by this pilot. No merge is
implied by this dependency chain.

## Scope

- `/internal/private-datasets` metadata and audit endpoints protected only by
  `require_service_api_key`.
- Five-minute signed access URL generated server side when explicitly enabled.
- Durable idempotent service audit using `request_id`.
- Storage privacy/object checks before access.
- Additive migration `005` only because 004 cannot represent a service actor
  and its legacy status constraint does not contain `PUBLISHED_PRIVATE` or
  `ACTIVE`.

Out of scope: Supabase Auth validation in staging, login UI, dashboard admin,
public datasets, scraping, schedules, role administration, activation,
revocation, restore, and external deployment.

## Safety model

`ENABLE_INTERNAL_DATASET_ACCESS=false` is the default. Metadata may be read by
the internal service, but a signed URL is blocked unless a separate approved
staging test enables this one flag. All existing publication flags stay false.
The API key remains server/operator-only and is never sent to frontend code.

Only `PUBLISHED_PRIVATE` and `ACTIVE` datasets with an APPROVED associated
approval, a checksum, a private bucket, and an existing object can obtain a
temporary URL. `REVOKED` returns 410; other states return 409. Legacy
`PRIVATE_PUBLISHED` is retained for history but is not eligible.

## Migration 005

The migration preserves all rows and prior constraints except for an additive
extension of the status check. It makes `user_id` nullable solely for
machine-originated audit rows, adds `actor_type`, and adds unique
`(actor_type, request_id)` idempotency. Human audit rows remain supported and
are labelled `human` by the Sprint 17A service.

## Rollback and cut-off

Rollback is code rollback to `v1.8.0` or the 17A checkpoint, with all flags
false. Do not reverse 005 destructively. Stop before a checkpoint if a URL is
persisted, a permanent URL leaks, storage is public, an API key reaches the
dashboard, n8n protection changes, a revoked/non-approved dataset is served,
or any test regresses.

## Acceptance criteria

- All internal routes require `X-API-Key`.
- No frontend, public route, dataset activation, or publication path changes.
- Same request ID cannot issue multiple temporary URLs in a process window.
- The signed URL is capped at 300 seconds and never written to the audit row.
- Tests use fakes only; no Supabase/network call occurs.
