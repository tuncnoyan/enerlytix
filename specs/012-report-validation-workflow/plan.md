# Implementation Plan: Report Validation Workflow

**Branch**: `[012-report-validation-workflow]` | **Date**: 2026-08-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/012-report-validation-workflow/spec.md`

## Summary

Introduce a structured validation lifecycle before finalization by adding validator assignment, page-level validation checkboxes, dedicated validation comments, automatic validation reset on business-content edits, and a strict final-save gate that requires full validation. Preserve existing ownership and delegation behaviors, while extending report metadata and saved reports visibility for validated-by and validation timestamp details. Keep implementation and verification Docker-first.

## Technical Context

**Language/Version**: Python 3.12 with Django runtime

**Primary Dependencies**: Django ORM, Django auth, existing sitesync services/views/templates, existing report ownership and write-delegation modules

**Storage**: PostgreSQL in Docker Compose runtime (`db` service), with Django migrations for new validation fields/tables

**Testing**: Django test runner in Docker web container (`docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test ...`)

**Target Platform**: Windows-hosted, Docker-containerized web application

**Project Type**: Server-rendered Django web application

**Performance Goals**: Report open, validation toggle, and draft/final save interactions remain responsive for standard report sizes (target under 2 seconds for normal UI request/response interactions)

**Constraints**: Final save must be blocked unless full validation is complete; validator must be non-owner and in same team or owner's supervisory chain; reassignment must reset page validations; all implementation validation and test execution must run in Docker

**Scale/Scope**: Extends existing monthly report lifecycle across report editor, saved reports listing, and access-control flows for owner, contributor, validator, team lead, manager, and admin personas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment | Notes |
|---|---|---|
| I. Windows-Native Platform Alignment | PASS | Existing Windows-compatible Django and Docker workflow is preserved |
| II. Least-Privilege Development & Operations | PASS | Feature requires no elevated host privileges; normal user Docker flow remains sufficient |
| III. Data Security and Database Isolation | PASS | Role-scoped validation actions and metadata auditing extend existing controlled access patterns |
| IV. Approval-Governed Production Operations | PASS | No production bypass or approval-policy changes introduced |
| V. Containerized Maintainability & Observability | PASS | Plan and validation workflow remain container-first with test execution in Docker |

Post-Phase 1 re-check: PASS. Research decisions and design artifacts maintain constitution compliance.

## Project Structure

### Documentation (this feature)

```text
specs/012-report-validation-workflow/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── report-validation-workflow.md
│   └── saved-reports-validation-metadata.md
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

**Structure Decision**: Implement validation workflow as additive changes within existing `sitesync` domain models, services, views, and templates. Reuse current report save endpoint and saved reports listing flow, with focused new validation data structures and tests.

## Phase Plan

### Phase 0: Research and Decisions (Complete)

- Resolved validation lifecycle unknowns: eligibility scope, reset behavior, reassignment reset, and superior-chain regrant rules.
- Confirmed additive status design approach to avoid regressions in existing finalization behavior.
- Confirmed Docker-only verification path.

### Phase 1: Design and Contracts (Complete)

- Authored [research.md](research.md) with decision records and alternatives.
- Authored [data-model.md](data-model.md) with report-level and page-level validation structures.
- Authored [contracts/report-validation-workflow.md](contracts/report-validation-workflow.md) and [contracts/saved-reports-validation-metadata.md](contracts/saved-reports-validation-metadata.md).
- Authored [quickstart.md](quickstart.md) with Docker-first validation scenarios and test commands.

### Phase 2: Implementation Planning (Next)

- Add report-level validation metadata and validator assignment persistence.
- Add page-level validation state and reset-on-content-change behavior.
- Add dedicated validation comments persistence and visibility in editor context.
- Enforce final-save gate requiring full-page validation and valid status transition.
- Extend saved reports payload/template columns for validated-by and validated-at metadata, with updated column replacement.
- Add audit logging for validator assignment, page validation, reset, and finalization gate outcomes.

### Phase 3: Verification Planning (Next)

- Add integration tests for validator assignment authorization and eligibility scope.
- Add integration tests for validator-only checkbox behavior and reassignment reset.
- Add integration tests for reset-on-edit semantics excluding validation-comment-only edits.
- Add integration tests for final-save blocking when any page is unvalidated.
- Execute all feature test suites in Docker web container only.

## Complexity Tracking

No constitution violations identified; no complexity exceptions are required.
