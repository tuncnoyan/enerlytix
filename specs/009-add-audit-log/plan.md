# Implementation Plan: Admin Audit Log

**Branch**: `009-add-audit-log` | **Date**: 2026-07-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/009-add-audit-log/spec.md`

## Summary

Add an admin-only audit investigation capability to Enerlytix that logs all authenticated mutating actions across the app, logs denied/failed security-relevant attempts, and exposes filtered review plus CSV/XLSX export in the Admin Panel. The implementation is Django-native in the existing `sitesync` app, stores UTC timestamps with normalized action-type codes plus readable messages, and enforces retention policy with a minimum of one year. All tests must run in Docker Compose web container.

## Technical Context

**Language/Version**: Python 3.14 with Django application runtime

**Primary Dependencies**: Django ORM, Django auth/session middleware, Django templates, existing `sitesync` app modules, Docker Compose runtime

**Storage**: PostgreSQL via Docker Compose (`db` service), with existing Django ORM migrations

**Testing**: Django test runner executed inside Docker web container (`docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test ...`)

**Target Platform**: Windows-hosted, containerized Django web application on Docker

**Project Type**: Server-rendered Django web application

**Performance Goals**: Audit list/filter responses remain operationally responsive for normal admin usage (<2s for typical filtered queries) and exports complete reliably for expected admin-sized datasets

**Constraints**: Admin-only access for viewer/export; immutable historical readability even if target entities are deleted; UTC storage for timestamps; retention floor of 1 year; no non-container test path for this feature

**Scale/Scope**: Organization-level audit trail for authenticated mutating actions and security-relevant denied/failed attempts across existing app modules, with panel-based filtering and dual-format export

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment | Notes |
|-----------|------------|-------|
| I. Windows-Native Platform Alignment | PASS | Workflow remains Windows-compatible and uses current Dockerized app model |
| II. Least-Privilege Development & Operations | PASS | No admin-elevation workflow required for development/test operations |
| III. Data Security and Database Isolation | PASS | Audit viewer/export remains admin-only; denied attempts are captured for traceability |
| IV. Approval-Governed Production Operations | PASS | No change to production approval workflow; feature supports compliance evidence |
| V. Containerized Maintainability & Observability | PASS | Implementation and test execution stay within Docker Compose environment |

**Post-Phase 1 re-check**: PASS. Research, data model, contract, and quickstart preserve least-privilege and containerized operation while strengthening auditability.

## Project Structure

### Documentation (this feature)

```text
specs/009-add-audit-log/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── audit-log.md
└── tasks.md
```

### Source Code (repository root)

```text
django_app/
├── config/
│   └── urls.py
├── sitesync/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── services.py
│   ├── templates/
│   │   └── sitesync/
│   └── tests/
└── docker/
    └── docker-compose.yml

tests/
├── integration/
├── contract/
└── unit/
```

**Structure Decision**: Extend existing Django `sitesync` domain, routing, and template layers. Add audit model, query/filter logic, admin-panel views, and export handlers without introducing a new framework.

## Phase Plan

### Phase 0: Research and Decisions (Complete)

- Finalize audit event-capture strategy across success and denied/failed attempts.
- Confirm normalized action type + human-readable message pattern.
- Confirm UTC storage, retention floor, and Docker-only test execution.

### Phase 1: Domain and Interface Design (Complete)

- Define `AuditLogEntry` and related filter/export constructs in [data-model.md](data-model.md).
- Define viewer/export contract in [contracts/audit-log.md](contracts/audit-log.md).
- Define execution validation in [quickstart.md](quickstart.md) using Docker-only commands.

### Phase 2: Implementation Planning (Next)

- Add schema migration for audit entry storage.
- Add audit logging service/hooks for authenticated mutating actions and denied/failed attempts.
- Add admin-panel audit viewer route and filter handling.
- Add CSV/XLSX export endpoints reusing identical filter semantics.
- Add FR-017 threshold guard for exports (>50,000 rows) with fail-fast messaging and no partial-file generation.
- Add authorization guards and denial logging.

### Phase 3: Verification Planning (Next)

- Add integration tests for logging coverage, authorization, filtering, and export parity.
- Add explicit validation for FR-017 export threshold behavior and no-partial-file guarantees.
- Ensure all test suites for this feature execute inside Docker web container.
- Add retention-policy validation for one-year minimum compliance.

## Complexity Tracking

No constitution violations identified; complexity exceptions are not required.
