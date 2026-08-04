# Research: Report Validation Workflow

Feature: 012-report-validation-workflow  
Date: 2026-08-04  
Status: Complete

## Decision 1: Keep implementation and verification Docker-only

- Decision: Build, migrate, and run all feature tests through Docker Compose services in `django_app/docker/docker-compose.yml`.
- Rationale: Your requirement explicitly mandates Docker execution, and this aligns with the container-first constitution principle.
- Alternatives considered:
  - Local virtualenv execution for speed: rejected to avoid environment drift from the deployed container runtime.
  - Mixed local and Docker verification: rejected because inconsistent execution paths reduce confidence in release behavior.

## Decision 2: Add validation lifecycle as a separate dimension from finalization state

- Decision: Keep existing report `current_status` semantics (`draft` and `final`) and add explicit validation metadata/state to represent `draft`, `awaiting_validation`, and `validated` lifecycle for pre-final quality control.
- Rationale: Existing code paths and tests currently depend on `current_status`; introducing separate validation state reduces regression risk and keeps compatibility with existing final save/replacement-final workflow.
- Alternatives considered:
  - Replace existing `current_status` with expanded enum only: rejected because it risks broad breakage in existing ownership, delegation, and saved-report flows.
  - Infer validation state from events only: rejected due to higher query complexity for every report load.

## Decision 3: Enforce validator eligibility as same-team or supervisory-chain, never owner

- Decision: Validator must be an active user who is not the owner and is either in the owner's same team or in the owner's supervisory chain.
- Rationale: This reflects clarified requirement A2 while preserving independence and operational flexibility.
- Alternatives considered:
  - Same-team-only validator pool: rejected because it can block validation when peer availability is low.
  - Organisation-wide validator pool: rejected as too permissive for least-privilege intent.

## Decision 4: Reset validation only on business-content edits, not validation-comment edits

- Decision: Clearing page validation is triggered only when business/report page content changes; edits to dedicated validation comments do not clear validated state.
- Rationale: This was explicitly clarified and avoids excessive re-validation caused by conversational annotation updates.
- Alternatives considered:
  - Reset on any page mutation: rejected as too noisy and operationally inefficient.
  - Never auto-reset on edits: rejected because it weakens quality assurance after content change.

## Decision 5: Reset all page validations on validator reassignment

- Decision: Any validator reassignment clears all page-level validations for the report.
- Rationale: Ensures one accountable validator has reviewed the full current report state end-to-end.
- Alternatives considered:
  - Preserve already checked pages: rejected due to mixed-accountability ambiguity.
  - Partial carry-over requiring selective reconfirmation: rejected as complex and hard to audit consistently.

## Decision 6: Restrict regrant authority on final reports to owner's supervisory chain roles

- Decision: Regrant write access for already-final reports is allowed only for team lead, manager, or admin in the owner's supervisory chain.
- Rationale: Matches clarified requirement and preserves controlled reopening authority.
- Alternatives considered:
  - Admin-only reopen: rejected as unnecessarily restrictive for normal operations.
  - Any manager/admin in organisation: rejected as broader than required authority scope.

## Decision 7: Integrate with existing report save endpoint and access-control services

- Decision: Keep `POST /report/` as the single save path; enforce validation gate and state transitions in the existing report service/view path.
- Rationale: Avoids duplicate save endpoints and preserves current workflow and tests with additive checks.
- Alternatives considered:
  - New dedicated finalization endpoint: rejected to avoid route fragmentation and duplicated authorization logic.
  - Client-only enforcement for validation completion: rejected because server-side gate is required for correctness and auditability.
