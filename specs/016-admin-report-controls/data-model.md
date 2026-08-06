# Data Model: Saved Reports Admin Controls

Feature: 016-admin-report-controls  
Date: 2026-08-06  
Status: Draft

## Overview

This feature extends existing saved-report listing behavior with admin-only bulk delete controls and server-side sortable ordering. No new persistent table is required. Existing `MonthlyReport` and `AuditLogEntry` data models are reused.

## Entities

### 1) SavedReportListRow (derived view model)

Represents one row in the saved reports table and sorting surface.

| Field | Type | Source | Rules |
|---|---|---|---|
| id | UUID string | MonthlyReport.id | Required; selection target |
| site_name | string | Site.name | Sortable text |
| reporting_month | YYYY-MM string | MonthlyReport.reporting_month | Sortable date-like month key |
| status | enum | MonthlyReport.current_status | `draft` or `final` |
| owner_name | string | owner_user.username | Sortable text |
| created_at | datetime | MonthlyReport.created_at | Sortable datetime |
| last_edited_by_name | string | last_modified_by_user.username | Sortable text |
| last_edited_at | datetime | MonthlyReport.last_modified_at | Sortable datetime |
| access_mode | enum/string | access resolution | Sortable text label |
| validator_name | string/null | validator_user.username | Sortable text with null-safe handling |
| validation_date | datetime/null | validation timestamp | Sortable datetime with null-safe handling |
| validation_status | enum | MonthlyReport.validation_status | Sortable text enum |
| open_url | string | reverse('sitesync:report') | Non-sort action link |

Validation rules:
- `id` must be unique per row.
- Returned rows remain constrained by existing visibility/access scope.

### 2) BulkDeleteRequest (command model)

Represents one admin-submitted bulk deletion command.

| Field | Type | Required | Rules |
|---|---|---|---|
| selected_report_ids | list[UUID] | Yes | At least one ID required |
| password_confirmation | string | Yes | Non-empty; must satisfy `request.user.check_password` |
| actor_user_id | user reference | Yes | Authenticated platform admin user |

Validation rules:
- Requester must be platform admin (`is_staff` or `is_superuser`).
- If any selected report is not deletable in current scope, request fails atomically.

### 3) BulkDeleteResult (operation result model)

Represents deterministic action outcome.

| Field | Type | Rules |
|---|---|---|
| outcome | enum | `success`, `denied`, or `failed` |
| deleted_count | integer | `0` on denied/failed/all-or-nothing conflict |
| blocked_report_refs | list[string] | Required when atomic failure occurs due to non-deletable rows |
| message | string | User-facing result summary |

State transitions:
- `requested` -> `denied` (non-admin or invalid password)
- `requested` -> `failed` (atomic conflict/non-deletable target)
- `requested` -> `success` (all selected reports deleted)

### 4) SortSelectionState (request/view model)

Represents active ordering control state.

| Field | Type | Required | Rules |
|---|---|---|---|
| sort_field | string | No | Must be one of allowlisted sortable field keys |
| direction | derived enum | Derived | Determined by field type defaults only |

Direction defaults:
- Date/datetime fields: descending (newest-first)
- Text fields: ascending (A-Z)
- Numeric fields: descending (high-low)

### 5) DeleteAuditEntry (persisted audit model usage)

Existing `AuditLogEntry` rows created for delete attempts.

| Field | Source | Rules |
|---|---|---|
| action_type | services constants | Distinguish bulk-delete attempt category |
| action_outcome | `AuditLogEntry.OUTCOME_*` | `SUCCESS`, `DENIED`, or `FAILED` |
| actor_user / actor_username_snapshot | authenticated request user | Required for traceability |
| target_entity_type / id / label | report context | Include report references or aggregate target |
| metadata_json | request/result details | Include selected IDs and blocked references where relevant |

## Relationships

- `SortSelectionState` and existing filter criteria jointly constrain the queryset that produces `SavedReportListRow` entries.
- `BulkDeleteRequest` operates over IDs represented by `SavedReportListRow`.
- Each `BulkDeleteRequest` produces one or more `DeleteAuditEntry` records based on outcome.

## Persistence Impact

- No new tables required.
- No migrations required unless new audit action constants are persisted through schema-constrained enums (not currently required).
