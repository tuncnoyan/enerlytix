# Research: Saved Reports Admin Controls

Feature: 016-admin-report-controls  
Date: 2026-08-06  
Status: Complete

## Decision 1: Admin authorization boundary for deletion

- Decision: Treat platform admins as users where `user.is_staff` or `user.is_superuser` is true.
- Rationale: Existing report-access and admin-panel patterns already use this boundary, minimizing role drift and reducing security ambiguity.
- Alternatives considered:
  - `RoleAssignment(role_name='admin')` only: rejected because current admin enforcement in report visibility and admin flows already includes staff/superuser semantics.
  - Manager/team-lead inclusion: rejected by clarified requirement.

## Decision 2: Password re-authentication check

- Decision: Require password confirmation at delete submit time using authenticated-session identity and `request.user.check_password(confirmed_password)`.
- Rationale: Reuses current auth state, avoids introducing parallel auth state, and supports deterministic pass/fail behavior for audit and UX.
- Alternatives considered:
  - One-time modal token without password: rejected because requirement explicitly mandates password re-entry.
  - Separate login flow redirect: rejected due to unnecessary friction for in-page bulk action.

## Decision 3: Atomic bulk-delete transaction model

- Decision: Execute bulk delete in one transaction and fail all when any selected report is non-deletable, returning blocking report references.
- Rationale: Matches clarified all-or-nothing rule and prevents ambiguous partial state.
- Alternatives considered:
  - Partial delete with per-row outcomes: rejected by clarification.
  - Silent skip of missing rows: rejected because it hides operational risk.

## Decision 4: Audit logging behavior

- Decision: Write audit entries for all delete attempts (authorized/unauthorized, success/denied/failed) using existing audit helpers and `AuditLogEntry` outcomes.
- Rationale: Constitution security/audit principles require traceability for privileged and denied actions.
- Alternatives considered:
  - Log only successful admin deletes: rejected because unauthorized attempts must be recorded.
  - Log denied attempts only in application logs: rejected because immutable audit table is the compliance record.

## Decision 5: Sorting implementation semantics

- Decision: Add a sort-field dropdown with allowlisted field keys and fixed default direction by field type: dates newest-first, text A-Z, numeric high-low.
- Rationale: Matches clarified behavior and keeps ordering deterministic without adding direction controls.
- Alternatives considered:
  - Secondary direction dropdown: rejected as out of scope.
  - Single default direction for all fields: rejected by clarification.

## Decision 6: Integration strategy with existing reports page

- Decision: Extend existing `/reports/` listing flow (backend query pipeline + template form + `saved_reports.js`) and preserve current filter and visibility semantics.
- Rationale: Lowest-risk path that reuses established endpoint contracts and team-scoped access logic.
- Alternatives considered:
  - New standalone reports-management page: rejected due to duplicated behavior and larger migration surface.
  - Client-side sorting over loaded rows only: rejected because it can diverge from server-filtered datasets and pagination/scoping semantics.

## Decision 7: Docker-first validation workflow

- Decision: All implementation and test execution commands are defined for `docker compose -f django_app/docker/docker-compose.yml`.
- Rationale: Required by constitution principle V and established repo workflow.
- Alternatives considered:
  - Local host Python test execution: rejected as non-compliant for feature workflow documentation.
