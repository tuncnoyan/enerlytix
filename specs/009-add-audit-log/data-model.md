# Data Model: Admin Audit Log

## Overview

This feature introduces an append-only audit domain focused on traceability, investigation, and export.

## Entities

### AuditLogEntry

Represents one immutable audit event.

**Fields**:
- `id` (PK): Unique identifier.
- `occurred_at_utc` (datetime, required): UTC timestamp of event occurrence.
- `actor_user_id` (FK/User, nullable): User who initiated action, null only if actor cannot be resolved.
- `actor_username_snapshot` (string, required): Username snapshot for historical readability.
- `source_ip` (string, required): Captured client IP address.
- `action_type` (enum string, required): Normalized action code (examples: `REPORT_CREATE`, `USER_DELETE`, `REPORT_APPROVE`, `ACCESS_DENIED`).
- `action_outcome` (enum string, required): `SUCCESS`, `DENIED`, or `FAILED`.
- `target_entity_type` (string, required): Logical entity type (for example `report`, `user`, `team`, `settings`).
- `target_entity_id` (string, nullable): Target identifier snapshot (string to support UUID/int).
- `target_entity_label` (string, nullable): Human-readable target snapshot (for example `John Smith`, `Report #456`).
- `message` (string, required): Human-readable action summary.
- `request_path` (string, nullable): Requested route for diagnostics.
- `metadata_json` (json, nullable): Structured supplemental context.
- `retention_class` (string, required): Policy key used by retention process.

**Validation rules**:
- `occurred_at_utc` must be UTC-normalized.
- `action_type` must be one of approved normalized codes.
- `action_outcome` must be one of `SUCCESS|DENIED|FAILED`.
- `message` must be non-empty and investigator-readable.
- Entry is immutable after creation except policy-safe retention bookkeeping fields if needed.

**Indexes**:
- Index on `occurred_at_utc` (range filters).
- Composite index on (`actor_user_id`, `occurred_at_utc`).
- Composite index on (`action_type`, `occurred_at_utc`).
- Index on `target_entity_type`.

### AuditFilterSet (request-level construct)

Represents active viewer/export filters.

**Fields**:
- `user_id` (optional)
- `keyword` (optional)
- `start_date_utc` (optional)
- `end_date_utc` (optional)
- `action_type` (optional)

**Validation rules**:
- If both dates exist, `start_date_utc <= end_date_utc`.
- Keyword is trimmed and bounded by max length.
- Action type must map to normalized enum.

### AuditExportRequest (derived operation)

Represents one export operation for filtered entries.

**Fields**:
- `format` (required): `csv` or `xlsx`.
- `filter_set` (required): Exact filters used at export time.
- `requested_by_user_id` (required).
- `requested_at_utc` (required).

**Validation rules**:
- `format` restricted to supported values.
- Only admin users are authorized to execute export.
- Export row set must match filtered viewer semantics.

## Relationships

- `AuditLogEntry.actor_user_id` references Django User (nullable, snapshot fields preserve readability).
- `AuditExportRequest.requested_by_user_id` references Django User.
- `AuditFilterSet` is not persisted as primary domain entity unless later optimization requires it.

## State Transitions

### AuditLogEntry Lifecycle

1. Event observed.
2. Entry validated and persisted as immutable record.
3. Entry is queryable in viewer/export.
4. Entry retained according to policy; minimum 1-year retention guaranteed.

### Export Lifecycle

1. Admin applies filters.
2. Admin requests export format.
3. System resolves matching entries.
4. File returned with rows matching filter semantics.

## Retention and Compliance

- Retention policy must never drop below 1 year.
- Deletion or mutation of target entities must not remove or invalidate existing audit entries.
- Timestamp storage remains UTC regardless of presentation timezone.
