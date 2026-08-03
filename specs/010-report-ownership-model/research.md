# Research: Report Ownership Model

Feature: 010-report-ownership-model  
Date: 2026-08-03  
Status: Complete

## Decision 1: Keep all implementation and verification Docker-only

- Decision: Development validation and automated tests for this feature run only through Docker Compose web and db services.
- Rationale: The project constitution requires containerized maintainability and your explicit requirement says the application and tests must support Docker environment only.
- Alternatives considered:
  - Mixed local plus Docker execution: rejected to avoid environment drift.
  - Local Python virtualenv only: rejected due to container-first operations policy.

## Decision 2: Extend existing MonthlyReport with explicit ownership fields

- Decision: Add ownership and accountability directly to MonthlyReport using owner, created_by, last_modified_by, and last_modified_at while preserving created_at.
- Rationale: Ownership and modification metadata are report identity concerns and should be queryable on saved report listings without joining deep version history.
- Alternatives considered:
  - Store owner on MonthlyReportVersion only: rejected because ownership applies to report identity, not a single version.
  - Derive last editor only from latest version comment writer: rejected because edits can include non-comment report changes and need one canonical source.

## Decision 3: Persist write grants as first-class records

- Decision: Introduce ReportWriteGrant records for owner-managed write access to named collaborators.
- Rationale: Explicit grant records support grant/revoke lifecycle, permission checks, and accountability required by the spec.
- Alternatives considered:
  - Store CSV list of user IDs on MonthlyReport: rejected due to poor integrity and auditability.
  - Reuse only broad role assignments: rejected because feature needs report-level named-user delegation.

## Decision 4: Use an explicit team-lead approval record before fallback transfer

- Decision: Ownership fallback is triggered only by a team-lead approval workflow record, then transferred in strict order team_lead -> manager -> admin for first available candidate.
- Rationale: The clarified requirement mandates approval-gated transfer and deterministic fallback order.
- Alternatives considered:
  - Automatic inactivity timer trigger: rejected because clarification chose team-lead workflow.
  - Manual admin-only reassignment: rejected because fallback order and approval semantics would be bypassed.

## Decision 5: Resolve same scope through team assignment and site-team linkage

- Decision: Enforce same report site or organization scope by anchoring each report site to a team and selecting fallback candidates from that team context first.
- Rationale: Existing code already models Team, team_lead, manager, and user-team assignments; this feature can complete scope enforcement by binding reports to team scope.
- Alternatives considered:
  - Global role-only fallback with no site-team scope: rejected due to clarified scope requirement.
  - Free-form scope mapping per report: rejected as high complexity and inconsistent with existing team hierarchy models.

## Decision 6: Reuse existing report and panel routes with additive actions

- Decision: Keep saved reports at GET /reports/ and report editor at GET/POST /report/, adding ownership metadata projection and ownership management actions via panel endpoints.
- Rationale: Minimizes routing churn and preserves existing user flow while enabling owner/grant management features.
- Alternatives considered:
  - New standalone report ownership app and routes: rejected as unnecessary architectural expansion.
  - Ownership management only via Django admin: rejected because business workflow requires in-app operational controls.