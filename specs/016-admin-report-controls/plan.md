# Implementation Plan: Saved Reports Admin Controls

**Branch**: `[016-admin-report-controls]` | **Date**: 2026-08-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/016-admin-report-controls/spec.md`

## Summary

Add platform-admin-only bulk delete controls to saved reports with password re-authentication, atomic all-or-nothing deletion behavior, and mandatory audit logging for authorized and unauthorized attempts. Add server-driven dropdown sorting over saved-reports columns using field-type defaults (dates newest-first, text A-Z, numeric high-low) while preserving existing filter criteria and report visibility scope.

## Technical Context

**Language/Version**: Python 3.12, Django 5.0.1, vanilla JavaScript

**Primary Dependencies**: Django auth/session stack, `sitesync.views.saved_reports_view`, `sitesync.services.get_accessible_reports`, `sitesync.services.create_audit_log_entry`, `AuditLogEntry` model

**Storage**: PostgreSQL in Docker Compose runtime; existing `MonthlyReport` and `AuditLogEntry` tables

**Testing**: Django test runner (`python manage.py test`) executed in Docker `web` container

**Target Platform**: Windows-hosted Dockerized web application accessed via modern desktop browsers

**Project Type**: Server-rendered Django web application (HTML + optional JSON mode)

**Performance Goals**: Preserve responsive list interactions; sorting/filtering and bulk-delete feedback should satisfy existing usability success targets and complete in typical interactive request times

**Constraints**: Docker-only development/testing, no privilege escalation requirements, preserve team/role visibility scoping, enforce atomic delete semantics, enforce password confirmation, audit every delete attempt outcome

**Scale/Scope**: Extend existing `/reports/` flow plus one delete endpoint and saved-reports UI/JS/tests; no new subsystem

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Pre-design gate check:
- Principle I (Windows-native alignment): Pass. Feature remains in current browser + Django architecture used on Windows-hosted environments.
- Principle II (Least privilege): Pass. Runtime and validation flows remain standard-user Docker workflows.
- Principle III (Data security and isolation): Pass. Admin-only destructive action with password re-check and auditable outcomes strengthens security posture.
- Principle IV (Approval-governed production ops): Pass. No workflow bypass introduced.
- Principle V (Containerized maintainability): Pass. Development and tests are documented Docker-only.

Post-design gate check:
- Pass. Phase 1 artifacts preserve existing access scoping, add auditable security controls, and keep all validation commands in Docker.

## Project Structure

### Documentation (this feature)

```text
specs/016-admin-report-controls/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── saved-reports-admin-controls.md
└── tasks.md
```

### Source Code (repository root)

```text
django_app/
├── sitesync/
│   ├── models.py
│   ├── services.py
│   ├── urls.py
│   ├── views.py
│   └── tests/
│       ├── test_saved_reports_view.py
│       ├── test_saved_reports_ownership_listing.py
│       ├── test_saved_reports_team_context.py
│       └── test_audit_*.py
├── templates/
│   └── sitesync/
│       └── saved_reports.html
└── static/
    └── sitesync/
        └── js/
            └── saved_reports.js
```

**Structure Decision**: Keep implementation inside the existing `sitesync` saved-reports route/template/script boundaries, adding focused route/view/service/test updates rather than introducing a new module.

## Phase 0: Research Output

Phase 0 decisions are documented in [research.md](research.md), including:
- Platform-admin authorization boundary
- Password re-authentication model
- Atomic delete behavior and conflict handling
- Audit logging for authorized and unauthorized attempts
- Sort-field allowlisting and field-type default direction mapping
- Docker-only validation workflow

## Phase 1: Design Output

Phase 1 artifacts generated:
- [data-model.md](data-model.md)
- [contracts/saved-reports-admin-controls.md](contracts/saved-reports-admin-controls.md)
- [quickstart.md](quickstart.md)

## Complexity Tracking

No constitution violations or exceptional complexity justifications required.
