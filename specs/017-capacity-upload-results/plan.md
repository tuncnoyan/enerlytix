# Implementation Plan: Capacity Upload Results UX

**Branch**: `[017-capacity-upload-results]` | **Date**: 2026-08-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/017-capacity-upload-results/spec.md`

## Summary

Improve Available Capacity Upload outcomes in the Settings page by removing the large inline row-error list and preserving only concise run status/summary blocks. Add a downloadable Excel results action for the latest completed upload run, with two sheets (Successes and Failures) that include row number, original upload columns, outcome, and explanation (including combined failure reasons).

## Technical Context

**Language/Version**: Python 3.12, Django 5.0.1, vanilla JavaScript

**Primary Dependencies**: Django forms/views/templates, openpyxl (existing), `sitesync.services.import_capacity_upload`, `CapacityUploadRun`

**Storage**: PostgreSQL via Django ORM; existing `CapacityUploadRun` plus new per-row result persistence for export reconstruction

**Testing**: Django test runner (`python manage.py test`) in Docker container; module-level integration and service tests

**Target Platform**: Windows-hosted Dockerized web app (browser UI)

**Project Type**: Server-rendered Django web application

**Performance Goals**: Keep settings page readable regardless of error volume; export generation must complete within normal interactive request expectations for typical upload sizes

**Constraints**: Docker-only execution; preserve existing settings access controls; export latest completed run only; workbook must contain exactly two sheets named `Successes` and `Failures`

**Scale/Scope**: One settings-section UX update, one export endpoint/action, row-result persistence and serialization, and focused tests/documentation updates

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Pre-design gate check:
- Principle I (Windows-native alignment): Pass. UI and workflows remain browser-based on current Windows-supported deployment model.
- Principle II (Least privilege): Pass. No admin-elevation or privileged host operations required.
- Principle III (Data security and isolation): Pass. Export remains access-controlled to authorized settings users and uses existing authenticated flows.
- Principle IV (Approval-governed production ops): Pass. No process bypass introduced.
- Principle V (Containerized maintainability): Pass. Validation and delivery remain Docker-first.

Post-design gate check:
- Pass. Design adds constrained export surface, retains auth boundaries, and keeps verification commands containerized.

## Project Structure

### Documentation (this feature)

```text
specs/017-capacity-upload-results/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── capacity-upload-results-export.md
└── tasks.md
```

### Source Code (repository root)

```text
django_app/
├── sitesync/
│   ├── models.py
│   ├── services.py
│   ├── forms.py
│   ├── urls.py
│   ├── views.py
│   └── tests/
│       ├── test_capacity_upload.py
│       ├── test_settings_view.py
│       └── test_capacity_upload_results_export.py
├── templates/
│   └── sitesync/
│       └── settings_panel.html
└── static/
    └── sitesync/
        └── js/
            └── settings.js
```

**Structure Decision**: Extend the existing capacity-upload path in `sitesync` (same settings view/template/service flow), adding a focused export surface and row-result persistence without introducing a new subsystem.

## Phase 0: Research Output

Phase 0 decisions are documented in [research.md](research.md), including:
- Latest-run export targeting
- Row-result persistence strategy for original columns + outcomes
- Excel workbook format and failure explanation representation
- Access control and no-data behavior for export action
- UI simplification approach for removing inline issue lists

## Phase 1: Design Output

Phase 1 artifacts generated:
- [data-model.md](data-model.md)
- [contracts/capacity-upload-results-export.md](contracts/capacity-upload-results-export.md)
- [quickstart.md](quickstart.md)

## Complexity Tracking

No constitution violations or exceptional complexity justifications required.
