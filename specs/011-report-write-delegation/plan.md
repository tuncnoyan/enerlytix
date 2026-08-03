# Implementation Plan: Report Write Delegation

**Branch**: `[011-report-write-delegation]` | **Date**: 2026-08-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from /specs/011-report-write-delegation/spec.md

## Summary

Implement report-level delegated write access that allows owners to grant same-team collaboration, while allowing team leads and managers to grant organisation-scoped write access (including self). Preserve single-owner report accountability, enforce submit-time write checks, and provide deterministic concurrent grant/revoke handling with auditable history. All implementation verification and tests run in Docker Compose environment.

## Technical Context

**Language/Version**: Python 3.12 with Django runtime

**Primary Dependencies**: Django ORM, Django auth, existing sitesync models/services/views, Docker Compose

**Storage**: PostgreSQL (postgres:16-alpine via docker-compose db service)

**Testing**: Django test runner executed inside Docker web container (`docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test ...`)

**Target Platform**: Windows-hosted, Docker-containerized web application

**Project Type**: Server-rendered Django web application

**Performance Goals**: Delegation grant/revoke and report-open authorization checks remain responsive under normal operations (target under 2 seconds end-to-end for standard report open/edit flows)

**Constraints**: Containerized execution for implementation validation and automated tests; role- and scope-restricted delegation rules; deterministic last-write-wins conflict resolution by server commit timestamp; auditable grant/revoke history retention

**Scale/Scope**: Organisation-scoped collaboration controls for existing report editor and saved report browsing flows across current user/team hierarchy

## Constitution Check

GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.

| Principle | Assessment | Notes |
|---|---|---|
| I. Windows-Native Platform Alignment | PASS | Workflow uses existing Windows-compatible Docker setup and current app paths |
| II. Least-Privilege Development and Operations | PASS | No elevation required; normal Docker user workflow for build/test |
| III. Data Security and Database Isolation | PASS | Delegation actions are role/scope constrained with submit-time enforcement and auditability |
| IV. Approval-Governed Production Operations | PASS | No production process bypass; feature is additive to existing governance model |
| V. Containerized Maintainability and Observability | PASS | Planning artifacts and verification path are explicitly Docker-first |

Post-Phase 1 re-check: PASS. Research decisions, data model, contracts, and quickstart preserve constitution compliance and containerized operation.

## Project Structure

### Documentation (this feature)

```text
specs/011-report-write-delegation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── report-write-delegation.md
│   └── saved-reports-delegation-visibility.md
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

**Structure Decision**: Extend the existing sitesync domain and report flows with additive delegation models, service-layer authorization, and route handlers. Keep current Django app boundaries and Docker configuration unchanged, with feature tests executed from the web container.

## Phase Plan

### Phase 0: Research and Decisions (Complete)

- Confirmed Docker-only build/test validation path per instruction.
- Confirmed delegation authority matrix and scope boundaries from specification clarifications.
- Chosen additive active-state plus immutable event model for auditable delegation history.
- Confirmed deterministic concurrent conflict handling strategy (last-write-wins by server commit timestamp).

### Phase 1: Design and Contracts (Complete)

- Authored data model in [data-model.md](data-model.md).
- Authored contracts in [contracts/report-write-delegation.md](contracts/report-write-delegation.md) and [contracts/saved-reports-delegation-visibility.md](contracts/saved-reports-delegation-visibility.md).
- Authored Docker-first end-to-end validation in [quickstart.md](quickstart.md).
- Captured rationale and alternatives in [research.md](research.md).

### Phase 2: Implementation Planning (Next)

- Add migrations and model definitions for delegation state and delegation events.
- Implement delegation authority resolver for owner/team lead/manager rules and organisation boundaries.
- Implement grant and revoke actions with submit-time permission enforcement.
- Implement concurrency-safe delegation updates with timestamp-based last-write-wins semantics.
- Add report access visibility endpoint/context for active delegated writers and grantor identity.
- Wire audit event persistence for all grant/revoke actions including conflict metadata.

### Phase 3: Verification Planning (Next)

- Add integration tests for owner delegation grant/revoke and same-team enforcement.
- Add integration tests for team lead/manager organisation-scoped delegation including self-grant.
- Add permission tests for unauthorized grant/revoke and save denial after revoke.
- Add concurrency tests for deterministic final state and complete audit event capture.
- Execute all relevant tests in Docker web container only.

## Complexity Tracking

No constitution violations identified; complexity exceptions are not required.
