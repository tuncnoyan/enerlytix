# Implementation Plan: Report Ownership Model

**Branch**: `010-report-ownership-model` | **Date**: 2026-08-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from /specs/010-report-ownership-model/spec.md

## Summary

Implement report-level ownership, metadata accountability, owner-managed write grants, and approved fallback ownership transfer for unavailable owners. The technical approach extends existing Django report, team, and role models in sitesync with explicit ownership entities and transfer workflow records, while preserving current report editor and saved reports routes. Per user directive, all implementation verification and test execution for this feature is Docker-only.

## Technical Context

**Language/Version**: Python 3.12 with Django web application runtime

**Primary Dependencies**: Django ORM, Django auth, Django templates, existing sitesync services and views, Docker Compose runtime

**Storage**: PostgreSQL via Docker Compose db service

**Testing**: Django test runner invoked only inside Docker web container (docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test ...)

**Target Platform**: Windows-hosted, Docker-containerized web application

**Project Type**: Server-rendered Django web application

**Performance Goals**: Saved reports listing with ownership metadata remains responsive for normal admin and user operations (target under 2 seconds for common filtered list views)

**Constraints**: Docker-only execution path for feature development validation and tests; strict ownership fallback order team lead then manager then system admin; fallback requires team-lead approval workflow; non-owners read-only by default unless explicitly granted write access

**Scale/Scope**: Organization-level report ownership and collaboration control across existing monthly report flows and saved report browsing

## Constitution Check

GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.

| Principle | Assessment | Notes |
|---|---|---|
| I. Windows-Native Platform Alignment | PASS | Workflow remains Windows-compatible and uses existing Docker deployment model |
| II. Least-Privilege Development and Operations | PASS | No privileged host operations required; standard Docker user workflow |
| III. Data Security and Database Isolation | PASS | Ownership/write checks enforce least privilege at report level with auditable transfer events |
| IV. Approval-Governed Production Operations | PASS | Ownership fallback requires explicit team-lead approval workflow |
| V. Containerized Maintainability and Observability | PASS | Design and validation are Docker-only and align with containerized operations |

Post-Phase 1 re-check: PASS. Research decisions, data model, contracts, and quickstart preserve constitution principles and Docker-only validation.

## Project Structure

### Documentation (this feature)

```text
specs/010-report-ownership-model/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── report-ownership.md
│   └── saved-reports-ownership.md
└── tasks.md
```

### Source Code (repository root)

```text
django_app/
├── sitesync/
│   ├── models.py
│   ├── services.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── templates/
│   │   └── sitesync/
│   ├── tests/
│   └── migrations/
└── docker/
    ├── docker-compose.yml
    └── Dockerfile

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Extend existing sitesync domain and reporting flow; no new app or service boundary. Implement ownership and grant logic in current report model and view/service layers with additive migration and Docker-only verification.

## Phase Plan

### Phase 0: Research and Decisions (Complete)

- Confirmed Docker-only validation and test strategy.
- Selected explicit report ownership and write-grant data model extensions.
- Confirmed approval-gated fallback workflow and deterministic transfer order.
- Confirmed scope enforcement strategy aligned with existing team and role constructs.

### Phase 1: Design and Contracts (Complete)

- Authored ownership domain model in [data-model.md](data-model.md).
- Authored interaction contracts in [contracts/report-ownership.md](contracts/report-ownership.md) and [contracts/saved-reports-ownership.md](contracts/saved-reports-ownership.md).
- Authored Docker-only validation scenarios in [quickstart.md](quickstart.md).
- Captured rationale and alternatives in [research.md](research.md).

### Phase 2: Implementation Planning (Next)

- Add migration for MonthlyReport ownership metadata fields and new grant/approval/transfer entities.
- Add permission resolution service for owner and active-grant checks.
- Add owner-only grant and revoke workflows.
- Add team-lead approval workflow endpoint and fallback transfer orchestration.
- Update saved reports query and template projection for required ownership metadata fields.
- Add audit event wiring for grant/revoke/transfer actions.

### Phase 3: Verification Planning (Next)

- Add integration tests for owner write, collaborator write, and non-owner read-only enforcement.
- Add integration tests for approved fallback transfer order and eligibility filtering.
- Add contract tests for ownership management actions and saved report field visibility.
- Execute all tests in Docker web container only.

## Complexity Tracking

No constitution violations identified; complexity exceptions are not required.
