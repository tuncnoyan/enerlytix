# Implementation Plan: Monthly Report Draft and Final Workflow

**Branch**: `spec/004-report-draft-workflow` | **Date**: 2026-07-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-report-draft-workflow/spec.md`

## Summary

Implement a persistent monthly report workflow in the existing Django application. The new flow will store one report identity per site and reporting month, allow draft and final saves, preserve immutable original final versions by creating replacement final versions when a final report is edited after warning, copy previous month final comments into a new month as reference comments, and expose a new saved reports page for browsing existing drafts and finals.

## Technical Context

**Language/Version**: Python 3.14 + Django 5.0.1 backend, vanilla JavaScript ES6 frontend

**Primary Dependencies**: Django, Django REST Framework, existing project utilities; no new frontend framework or build tool required

**Storage**: SQLite in development, PostgreSQL in production; new Django models and constraints for report identity, version history, and comments

**Testing**: Django `TestCase` / request tests in `django_app/sitesync/tests/`; existing `python manage.py test` workflow

**Target Platform**: Windows-native Django web application, container-capable via existing Docker Compose setup

**Project Type**: Web application with server-rendered Django templates and lightweight browser JavaScript

**Performance Goals**: Load the saved reports page and open a monthly report in under 2 seconds on typical site sizes; preserve save/finalise actions with no duplicate monthly reports

**Constraints**: Keep the current report page architecture, avoid a new frontend framework, preserve one-report-per-site-per-month uniqueness, and keep original final reports immutable after warning-based edits

**Scale/Scope**: Single-site monthly workflow across historical reports; one monthly report identity per site/month, with multiple versions only when a final report is corrected

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment | Notes |
|-----------|------------|-------|
| I. Windows-Native Platform Alignment | PASS | Existing Django app and browser UI continue to target Windows-friendly development and deployment |
| II. Least-Privilege Development & Operations | PASS | No admin-only tooling or platform changes required |
| III. Data Security and Database Isolation | PASS | Uses existing session-authenticated Django views and database-backed access controls |
| IV. Approval-Governed Production Operations | PASS | No deployment or privilege changes included in this plan |
| V. Containerized Maintainability & Observability | PASS | No container topology changes; new code remains inside the existing Django service |

**Post-Phase 1 re-check**: PASS. The planned data model additions are additive, schema-backed, and do not require elevated operations.

## Project Structure

### Documentation (this feature)

```text
specs/004-report-draft-workflow/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── report-workflow.md
│   └── saved-reports-browser.md
└── tasks.md
```

### Source Code (repository root)

```text
django_app/
├── sitesync/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── templates/
│   │   └── sitesync/
│   │       ├── report.html
│   │       └── saved_reports.html
│   ├── static/
│   │   └── sitesync/
│   │       └── js/
│   │           ├── report.js
│   │           └── saved_reports.js
│   ├── migrations/
│   └── tests/
│       ├── test_report_workflow.py
│       └── test_saved_reports_view.py
```

**Structure Decision**: Extend the existing single Django app (`sitesync`) with new report models, server-rendered views, templates, and focused browser JavaScript. No new app, package, or frontend framework is required.

## Complexity Tracking

No constitution violations or exceptional complexity justifications are required for this plan.
