# Implementation Plan: Average Capacity Integration

**Branch**: `[not-set]` | **Date**: 2026-07-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-available-capacity-upload/spec.md`

## Summary

Add manual `.xlsx` Average Capacity upload to Settings, validate required columns and row quality, persist normalized capacity reference data keyed by eSight Meter Code, apply partial-import semantics for invalid rows, and surface these values in electricity load factor output with unit label updated to `Available Capacity (kVA)`.

## Technical Context

**Language/Version**: Python 3.14 + Django 5.0.1 backend, vanilla JavaScript ES6 frontend

**Primary Dependencies**: Django, Django REST Framework, `openpyxl` for `.xlsx` parsing

**Storage**: Existing relational DB (SQLite dev / PostgreSQL prod) with additive Django model(s) and migration for capacity reference records and upload run results

**Testing**: Django `TestCase` suite under `django_app/sitesync/tests/` plus focused view/model/service tests for upload and load-factor resolution

**Target Platform**: Windows-native Django web application, container-capable via current Docker setup

**Project Type**: Server-rendered Django web app with template-based UI and lightweight frontend JS

**Performance Goals**: Typical upload files (<5k rows) process and return summary in under 10 seconds; report load endpoints remain within existing interactive tolerance (<2s typical page render)

**Constraints**: `.xlsx` only, partial import for row-level validation errors, eSight Meter Code-only matching, no new frontend framework, preserve existing settings workflow and report architecture

**Scale/Scope**: Single-tenant operations workflow; periodic manual uploads and read-time lookup across all electricity supplies in report generation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment | Notes |
|-----------|------------|-------|
| I. Windows-Native Platform Alignment | PASS | No platform shifts; keeps existing Windows-friendly Django operations |
| II. Least-Privilege Development & Operations | PASS | Upload and processing run within app permissions, no admin-level host operations |
| III. Data Security and Database Isolation | PASS | Data remains in app DB and existing access controls; no external write path added |
| IV. Approval-Governed Production Operations | PASS | No deployment/privilege workflow changes in feature scope |
| V. Containerized Maintainability & Observability | PASS | Additive app logic only; remains container-compatible with existing service topology |

**Post-Phase 1 re-check**: PASS. Design remains additive and within existing security/operations boundaries; no constitution violations introduced.

## Project Structure

### Documentation (this feature)

```text
specs/005-available-capacity-upload/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── settings-capacity-upload.md
│   └── report-capacity-resolution.md
└── tasks.md
```

### Source Code (repository root)

```text
django_app/
├── sitesync/
│   ├── models.py
│   ├── forms.py
│   ├── services.py
│   ├── views.py
│   ├── urls.py
│   ├── migrations/
│   └── tests/
│       ├── test_settings_view.py
│       ├── test_settings_model.py
│       ├── test_report_drafts.py
│       └── (new) test_capacity_upload.py
├── templates/
│   └── sitesync/
│       ├── settings_panel.html
│       └── report.html
└── static/
    └── sitesync/
        └── js/
            └── report.js
```

**Structure Decision**: Extend the existing `sitesync` Django app and current templates/static assets. Use additive models/migrations and focused settings/report integrations, avoiding new apps or framework-level architectural changes.

## Complexity Tracking

No constitution violations or exceptional complexity justifications are required for this plan.
