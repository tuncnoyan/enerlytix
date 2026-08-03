# Contract: Report Write Delegation

Feature: 011-report-write-delegation  
Date: 2026-08-03  
Status: Draft

## Report Access View

Route:

```text
GET /report/?site_id=<id>&end_month=<YYYY-MM>
```

Behavior:
- Report owner can read and write.
- Active delegated writers can read and write.
- Other report readers are read-only.
- Response context must indicate effective mode: owner, delegated_writer, or read_only.

## Save Report Action

Route:

```text
POST /report/
```

Required fields:
- site_id
- end_month
- save_mode
- report payload fields in existing editor contract

Authorization behavior:
- Write permission is validated at submission time.
- If caller lacks effective write access, save is denied.

Error behavior:
- 403-equivalent permission error for unauthorized writes.
- No partial report mutation on authorization failure.

## Grant Delegated Write Access

Route:

```text
POST /reports/<report_id>/delegations/grant/
```

Required fields:
- delegate_user_id

Authorization behavior:
- Allowed for report owner, same-organisation team lead, same-organisation manager.
- Owner grants must target same-team active users.
- Team lead/manager grants can target active users in same organisation, including self.
- Grants outside organisation are denied.

Conflict behavior:
- Duplicate active delegation for same report/delegate is rejected.

## Revoke Delegated Write Access

Route:

```text
POST /reports/<report_id>/delegations/revoke/
```

Required fields:
- delegate_user_id

Authorization behavior:
- Allowed for report owner, original grantor, and same-organisation team lead/manager.

Conflict behavior:
- If grant/revoke operations race on the same report/delegate pair, final active state is determined by last-write-wins server commit timestamp.
- Both operations are persisted to audit history.

## Delegation Visibility

Route:

```text
GET /reports/<report_id>/delegations/
```

Behavior:
- Any user with read access to the report can view active delegated writers and grantors.
- Revoked delegations are excluded from the active list but remain auditable.

Response fields per active delegate:
- delegate_user
- granted_by_user
- granted_by_role
- granted_at
- is_active

## Audit Requirements

For each grant and revoke action, persist immutable event attributes:
- report_id
- delegate_user_id
- action (grant or revoke)
- action_by_user_id
- action_by_role
- action_at (server commit timestamp)
- conflict metadata when applicable
