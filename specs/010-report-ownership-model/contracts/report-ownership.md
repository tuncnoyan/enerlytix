# Contract: Report Ownership and Write Access

Feature: 010-report-ownership-model  
Date: 2026-08-03  
Status: Draft

## Report Editor Access

Route:

```text
GET /report/?site_id=<id>&end_month=<YYYY-MM>
```

Behavior:
- Owner can read and write.
- Active write-granted collaborators can read and write.
- Other authorized viewers are read-only.
- UI must expose effective access state for current user as owner, collaborator, or read-only.

## Save Report Action

Route:

```text
POST /report/
```

Required fields:
- site_id
- end_month
- save_mode
- comments

Authorization behavior:
- Request must be rejected when caller lacks write permission at submission time.
- Successful write updates last_modified_by and last_modified_at on report metadata.

Error behavior:
- 403-equivalent permission response for non-writers.
- No partial writes when permission fails.

## Ownership Grant Action

Route:

```text
POST /reports/<report_id>/ownership/grants/
```

Required fields:
- granted_user_id

Behavior:
- Only current owner can create grant.
- Duplicate active grant for same user is rejected.
- Owner cannot grant to self.

## Ownership Revoke Action

Route:

```text
POST /reports/<report_id>/ownership/grants/revoke/
```

Required fields:
- granted_user_id

Behavior:
- Only current owner can revoke grant.
- Grant becomes inactive while history remains queryable.

## Manual Ownership Transfer Action

Route:

```text
POST /reports/<report_id>/ownership/transfer/
```

Required fields:
- new_owner_user_id
- reason

Behavior:
- Current owner can transfer ownership explicitly.
- Previous owner remains write collaborator by default unless owner chooses removal in a separate action.
- Transfer event is persisted.

## Unavailability Approval Action

Route:

```text
POST /reports/<report_id>/ownership/unavailability/approve/
```

Required fields:
- owner_user_id
- reason

Behavior:
- Caller must be a team lead in the report scope.
- Creates an approved unavailability record.
- Triggers fallback transfer evaluation.

## Auto Fallback Transfer Contract

Transfer order and eligibility:
1. Team lead candidate
2. Manager candidate
3. System admin candidate

Candidate must be:
- active
- role-qualified for the fallback slot
- assigned to same site or organization scope

Post-conditions:
- MonthlyReport.owner is updated to selected candidate.
- Previous owner retains active collaborator write access.
- Ownership transfer event and metadata update are persisted.

Failure behavior:
- If no eligible candidate exists, transfer is aborted with clear actionable error.
- Existing owner remains unchanged.

## Audit and Traceability Expectations

The system records sufficient immutable events to reconstruct:
- who granted or revoked write access
- who approved owner unavailability
- who became new owner and why
- when ownership changed

Implementation may map these events into existing audit logging facilities, but contract behavior is mandatory.