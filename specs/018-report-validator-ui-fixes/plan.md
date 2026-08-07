# Implementation Plan: Report Validator UI Fixes

**Branch**: `[018-report-validator-ui-fixes]` | **Date**: 2026-08-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/018-report-validator-ui-fixes/spec.md`

## Summary

Deliver three coordinated fixes in report validation and saved-reports experiences: remove the duplicate first overview validation/comment block and normalize block width, enforce validator-restricted read-only report sessions with validation-note autosave on blur, and restore admin-only saved-reports row-selection checkboxes with stable production column alignment.

## Technical Context

**Language/Version**: Python 3.12, Django 5.0.1, vanilla JavaScript

**Primary Dependencies**: Django templates/views/services, existing report validation models/services, existing saved-reports JS rendering flow

**Storage**: PostgreSQL (production) and SQLite (local fallback) via Django ORM

**Testing**: Django test runner (`python manage.py test`) in Docker container

**Target Platform**: Windows-hosted Dockerized web application (browser UI; Railway production)

**Project Type**: Server-rendered Django web application

**Performance Goals**: Validation-note autosave must feel immediate in standard interactive usage; saved-reports rendering must remain stable with 0/1/many rows

**Constraints**: Docker-only development/test execution; validator separation-of-duties must be enforced; admin-only checkbox visibility in saved reports; production static/template consistency must be verified

**Scale/Scope**: One feature slice affecting report page UI behavior, role-gated actions, saved-reports rendering path, and focused regression tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Pre-design gate check:
- Principle I (Windows-native alignment): Pass. Browser-based workflows remain aligned with Windows-first operations.
- Principle II (Least privilege): Pass. Admin-only bulk-selection visibility and validator-restricted sessions reinforce least-privilege behavior.
- Principle III (Data security and isolation): Pass. Role-based restrictions are tightened; no new external data exposure.
- Principle IV (Approval-governed production ops): Pass. No bypass to approval workflow introduced.
- Principle V (Containerized maintainability): Pass. Planned validation uses Docker-only commands and existing containerized workflows.

Post-design gate check:
- Pass. Design preserves role boundaries, keeps production verification explicit, and remains fully container-validated.

## Project Structure

### Documentation (this feature)

```text
specs/018-report-validator-ui-fixes/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── report-validator-ui-behavior.md
└── tasks.md
```

### Source Code (repository root)

```text
django_app/
├── sitesync/
│   ├── services.py
│   ├── views.py
│   ├── urls.py
│   └── tests/
│       ├── test_saved_reports_view.py
│       └── test_report_validation.py
├── static/
│   └── sitesync/js/
│       ├── report.js
│       └── saved_reports.js
├── templates/
│   └── sitesync/
│       ├── report.html
│       └── saved_reports.html
└── staticfiles/
    └── sitesync/js/
        ├── report*.js
        └── saved_reports*.js

django_app/
└── tests/
    └── contract/
        └── test_report_validation_page_mark_contract.py
```

**Structure Decision**: Extend the existing report and saved-reports flows in-place across `sitesync` views/services/templates/static JS, with focused contract/integration tests and explicit production static consistency verification.

## Phase 0: Research Output

Phase 0 decisions are documented in [research.md](research.md), including:
- Validator precedence for dual-role users in validation sessions
- Blur-based validation-note autosave behavior
- First overview-page duplicate validation block removal and layout standardization
- Admin-only saved-reports checkbox visibility contract
- Production consistency verification for rendered template/static behavior
- Docker-first regression validation strategy

## Phase 1: Design Output

Phase 1 artifacts generated:
- [data-model.md](data-model.md)
- [contracts/report-validator-ui-behavior.md](contracts/report-validator-ui-behavior.md)
- [quickstart.md](quickstart.md)

## Complexity Tracking

No constitution violations or exceptional complexity justifications required.
