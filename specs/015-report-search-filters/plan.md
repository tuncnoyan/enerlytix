# Implementation Plan: Saved Reports Search and Filters

**Branch**: `[015-report-search-filters]` | **Date**: 2026-08-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/015-report-search-filters/spec.md`

## Summary

Add two saved-reports search inputs (Site and User), month-year range filters, and two status-filter checkbox groups with default-all behavior, while preserving role/team visibility rules and returning explicit empty states when criteria produce no matches. Implementation will extend the existing `/reports/` listing flow and saved-reports client rendering with Docker-native development and test execution only.

## Technical Context

**Language/Version**: Python 3.12 (Docker image baseline) with Django web stack

**Primary Dependencies**: Django, Django auth/session system, existing `sitesync` services and templates, vanilla JavaScript (`saved_reports.js`)

**Storage**: PostgreSQL in Docker Compose runtime (`db` service); existing `MonthlyReport` and related tables

**Testing**: Django test runner (`python manage.py test`) executed inside Docker `web` container

**Target Platform**: Windows-hosted containerized web app accessed in modern desktop browsers

**Project Type**: Server-rendered Django web application with route-driven HTML and optional JSON payload mode

**Performance Goals**: Maintain responsive saved-reports interactions; filtered list updates should satisfy spec success criteria (single-criterion updates under 2 seconds for typical usage volumes)

**Constraints**: Docker-only development/testing, no privilege escalation requirements, preserve authorization/team scoping semantics, preserve existing saved report open-link behavior, enforce month-year inclusive range semantics and explicit invalid-range handling

**Scale/Scope**: One existing route (`/reports/`), one template (`saved_reports.html`), one page script (`saved_reports.js`), and corresponding saved-reports tests/contracts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Principle I (Windows-native): Pass. Implementation remains in existing browser + Django stack used on Windows-hosted environments.
- Principle II (Least privilege): Pass. Docker commands and app operations run without requiring admin privilege workflows.
- Principle III (Data security): Pass. Changes reuse existing authenticated, team-scoped report visibility and do not widen data exposure.
- Principle IV (Approval-governed production ops): Pass. Planning introduces no bypass of existing review/approval processes.
- Principle V (Containerized maintainability): Pass. Development and validation are explicitly Docker-only.

No constitution violations identified.

## Project Structure

### Documentation (this feature)

```text
specs/015-report-search-filters/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── saved-reports-search-filters.md
└── tasks.md
```

### Source Code (repository root)

```text
django_app/
├── sitesync/
│   ├── views.py
│   ├── urls.py
│   ├── services.py
│   └── tests/
│       ├── test_saved_reports_view.py
│       ├── test_saved_reports_ownership_listing.py
│       └── test_saved_reports_team_context.py
├── templates/
│   └── sitesync/
│       └── saved_reports.html
└── static/
    └── sitesync/
        └── js/
            └── saved_reports.js

specs/
└── 015-report-search-filters/
    ├── spec.md
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    └── contracts/
```

**Structure Decision**: Keep all implementation changes within the existing Django `sitesync` module boundaries and saved-reports page assets, because this feature extends current list behavior rather than introducing a new subsystem.

## Phase 0: Research Output

Phase 0 decisions are documented in [research.md](research.md), including:
- Server-side filter application strategy on existing saved-reports route
- Inclusive month-year range semantics
- Permissive all-unticked status behavior with explicit empty state
- Case-insensitive contains matching
- Docker-only execution policy

## Phase 1: Design Output

Phase 1 artifacts generated:
- [data-model.md](data-model.md)
- [contracts/saved-reports-search-filters.md](contracts/saved-reports-search-filters.md)
- [quickstart.md](quickstart.md)

Post-design constitution re-check: Pass (no new violations).

## Complexity Tracking

No constitution violations or extraordinary complexity exceptions require justification.
