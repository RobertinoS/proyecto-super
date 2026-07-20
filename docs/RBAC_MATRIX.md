# RBAC matrix

Roles are additive: a user can hold more than one active role and receives the
union of their capabilities. Inactive assignments grant nothing.

| Role | Current Sprint 17A capability | Explicitly not granted in Sprint 17A |
| --- | --- | --- |
| `viewer` | Read safe metadata contract; request future temporary access. | Download, activate, revoke, approve, or operate sources. |
| `reviewer` | `viewer` capabilities; review decisions; future restore participation. | Dataset activation/revocation alone, live operation. |
| `dataset_admin` | `viewer` capabilities; future activation/revocation and protected role assignment administration. | Private publication bypass, solo restore, live operation. |
| `operator` | Read operations; request a future manual live window. | Approve/revoke dataset or approve publication. |

## Implementation state

- Active role lookup: implemented server side through `app_user_roles`.
- Capability derivation: implemented in FastAPI.
- `/auth/me` and `/auth/capabilities`: implemented with human Bearer JWT.
- Role administration: contract only; no endpoint or UI exists.
- Review/approval endpoint conversion: deferred to a later scoped sprint so
  machine automation remains unchanged.
- Two-person restore: contract only; it will require two distinct human users
  in Sprint 17C.
