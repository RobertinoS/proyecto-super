# Private consumption API contract

Sprint 17A defines the schema and error contract for a later authenticated
dataset consumer. It does not implement these routes, issue signed URLs, read
storage, activate a dataset, or alter dataset state.

## Sprint 17B internal pilot

The following implemented routes are distinct from the future human contract:
`/internal/private-datasets`, `/current`, `/{dataset_id}`, `/{dataset_id}/access`,
and `/{dataset_id}/audit`. They require `X-API-Key` through
`require_service_api_key`; they are for Swagger/PowerShell operators only and
must never be called by the dashboard/frontend.

`POST /internal/private-datasets/{dataset_id}/access` accepts only
`request_id`, requires the internal access feature flag, and emits a signed URL
with a maximum 300-second lifetime. The full URL is not persisted. This pilot
does not make Supabase Auth operational, add a public endpoint, activate a
dataset, or publish data.

## Authentication

All future `/private/*` routes require a verified Supabase Auth Bearer JWT.
FastAPI resolves active roles from `app_user_roles`; the browser never receives
a service role, API key, storage credential, or permanent dataset path.

## Proposed read contracts

| Future route | Minimum role | Success | Controlled failure |
| --- | --- | --- | --- |
| `GET /private/datasets/current` | `viewer` | Safe metadata for current active dataset. | 401, 403, 404, 410, 503. |
| `GET /private/datasets` | `viewer` | Paginated version metadata. | 401, 403, 503. |
| `GET /private/datasets/{dataset_id}` | `viewer` | One safe metadata record. | 401, 403, 404, 410, 503. |
| `POST /private/datasets/{dataset_id}/access` | `viewer` | Audited access decision; a later sprint may issue a 5-minute URL. | 401, 403, 404, 410, 429, 503. |

`FuturePrivateDatasetMetadata`, `FutureDatasetAccessRequest`, and
`FutureDatasetAccessResponse` are Pydantic contracts retained in the backend
source. They are not registered as active FastAPI routes in this sprint.

## Semantics reserved for later work

- `401`: missing, malformed, expired, bad issuer, bad audience, or bad
  signature token. No validation detail is returned.
- `403`: authenticated user lacks an active role.
- `404`: no current approved dataset or unknown dataset.
- `410`: dataset is revoked and cannot be accessed.
- `429`: future rate limit for access requests.
- `503`: private storage/backend is unavailable.

Each future access request must create an idempotent `dataset_access_logs`
event. A future temporary URL may live at most five minutes and must not be
stored in the audit table. Dataset activation, revocation, restoration and
actual download remain Sprint 17C/17B work.
