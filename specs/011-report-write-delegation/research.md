# Research: Report Write Delegation

Feature: 011-report-write-delegation  
Date: 2026-08-03  
Status: Complete

## Decision 1: Keep implementation and test execution Docker-only

- Decision: Build, migrate, and run automated tests for this feature only through Docker Compose services in django_app/docker/docker-compose.yml.
- Rationale: The project constitution is container-first and your explicit instruction requires test execution in the containerized environment.
- Alternatives considered:
  - Mixed local virtualenv and Docker runs: rejected to avoid environment drift.
  - Local-only execution: rejected because it violates containerized workflow requirements.

## Decision 2: Build delegation on top of report ownership without changing ownership semantics

- Decision: Preserve single report owner semantics and add delegation as an independent write-access layer.
- Rationale: The specification requires write collaboration without ownership transfer for overload and temporary coverage scenarios.
- Alternatives considered:
  - Temporary ownership reassignment for collaboration: rejected because it changes accountability and ownership meaning.
  - Team-wide default write access: rejected because delegation must be explicit and auditable.

## Decision 3: Use role-scoped delegation authority with report/organisation boundaries

- Decision: Apply three grant authorities: report owner (same-team delegates), team lead (organisation-wide), manager (organisation-wide).
- Rationale: This directly matches FR-002, FR-004, FR-005, FR-007, and clarified revocation behavior.
- Alternatives considered:
  - Owner-only delegation: rejected because lead/manager emergency coverage is a core scenario.
  - Global admin-like delegation for all roles: rejected for least-privilege reasons.

## Decision 4: Persist immutable delegation events plus active-state records

- Decision: Keep active delegation state queryable while also preserving append-only audit events for grant/revoke actions.
- Rationale: The spec requires real-time permission checks and auditable history, including concurrent conflict traceability.
- Alternatives considered:
  - Active-only records with no event trail: rejected because FR-013 and FR-014 require audit reconstruction.
  - Event-sourcing only with no current-state projection: rejected due to higher implementation complexity for frequent access checks.

## Decision 5: Enforce submit-time permission checks with deterministic conflict resolution

- Decision: Evaluate effective write access at report save submission time and resolve concurrent grant/revoke by last-write-wins using server commit timestamp.
- Rationale: This was explicitly clarified and supports deterministic behavior under concurrency.
- Alternatives considered:
  - Revoke-always-wins: rejected because clarification selected deterministic timestamp order.
  - Reject-both-on-conflict: rejected due to operational friction for urgent handover use cases.

## Decision 6: Expose delegation visibility to report readers

- Decision: Users with read access can view active delegated writers and grantors for that report.
- Rationale: Clarification explicitly selected read-access visibility, supporting collaboration transparency.
- Alternatives considered:
  - Owner/lead-only visibility: rejected due to lower operational transparency.
  - Admin-only visibility: rejected because it blocks ordinary collaboration context.
