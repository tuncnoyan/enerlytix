# Contract: Saved Reports Admin Controls

Feature: 016-admin-report-controls  
Date: 2026-08-06  
Status: Draft

## Scope

Defines interface behavior for saved-reports sorting and platform-admin bulk deletion with password confirmation and audit-backed outcomes.

## Interfaces

### 1) Saved reports listing and sorting

```text
GET /reports/
```

Route name: `sitesync:saved_reports`

#### Query parameters

- Existing filter parameters remain supported.
- `sort_field`: optional allowlisted field key.
- `format=json`: optional JSON mode.

#### Sort-field allowlist

- `site_name`
- `reporting_month`
- `status`
- `owner_name`
- `created_at`
- `last_edited_by_name`
- `last_edited_at`
- `access_mode`
- `validator_name`
- `validation_date`
- `validation_status`

#### Direction defaults (derived, not user-selectable)

- Date/datetime fields: newest-first
- Text fields: A-Z
- Numeric fields: high-low

#### Behavioral rules

- Sorting applies to the same authorization-scoped dataset as current saved-reports listing.
- Sorting applies after active filter criteria and does not clear/replace those criteria.
- Unknown `sort_field` values must not broaden result scope; server falls back to default ordering behavior.

### 2) Platform-admin bulk delete

```text
POST /reports/bulk-delete/
```

Route name: `sitesync:saved_reports_bulk_delete` (new)

#### Request fields

- `selected_report_ids`: repeatable UUID values (required, at least one).
- `password_confirmation`: string (required).
- Optional response mode can follow existing page conventions:
  - HTML form post for page flow.
  - JSON mode (`format=json`) for API-style tests/clients.

#### Authorization and validation

- Caller must be authenticated.
- Caller must be platform admin (`is_staff` or `is_superuser`).
- Password confirmation must match authenticated actor password.
- Request must enforce atomic delete behavior.

#### Outcome contract

- Success:
  - All selected rows deleted in one transaction.
  - Response includes deleted count summary.
  - Audit row written with `SUCCESS` outcome.
- Denied:
  - Non-admin or password mismatch.
  - Zero rows deleted.
  - Audit row written with `DENIED` or `FAILED` outcome per reason.
- Validation blocked:
  - No selected report IDs supplied.
  - Zero rows deleted.
  - Response includes `no_reports_selected` code.
- Atomic failure:
  - If any selected report is not deletable, zero rows deleted.
  - Response includes blocking report references.
  - Audit row written with `FAILED` outcome.

#### Unauthorized direct-request handling

- Direct non-admin POST attempts must be denied.
- Denied attempts must be audit-logged with actor identity and targeted report references.

## Response Shapes

### HTML mode

- Listing/sort requests render saved-reports template with persisted selected controls.
- Bulk-delete POST redirects back to saved reports with success/error message and unchanged filter/sort state when feasible.

### JSON mode

- Listing:
  - `reports`: array of sorted, filtered, scope-constrained rows.
  - `selected_filters`: existing normalized filter object.
  - `sort`: normalized sort selection payload.
- Bulk delete success:
  - `detail`: success summary.
  - `deleted_count`: integer.
- Bulk delete denied/failed:
  - `detail`: failure summary.
  - `code`: failure code (`access_denied`, `invalid_password`, `no_reports_selected`, or `atomic_delete_blocked`).
  - `blocked_report_refs`: array when atomic conflict occurs.

## Compatibility Requirements

- Existing `/reports/` filter semantics and visibility scoping remain intact.
- Existing open-report action URLs remain unchanged.
- Audit logging persistence uses existing `AuditLogEntry` model and helper services.
