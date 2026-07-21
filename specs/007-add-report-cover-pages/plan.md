# Implementation Plan: Report Cover Pages

**Branch**: `[not-set]` | **Date**: 2026-07-21 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-add-report-cover-pages/spec.md`

## Summary

Add three report cover pages (front cover 1, front cover 2, back cover) to all report variants, with editable fields on the two front covers and a static back cover image. The implementation extends the existing Django report generation/export flow and existing report-page JavaScript so cover pages are included in on-screen draft/final output plus PDF and PPTX downloads. All implementation and validation remain within the current Dockerized app structure, and test execution is performed via Docker commands only.

## Technical Context

**Language/Version**: Python 3.12 container runtime with Django app, vanilla JavaScript ES6 on report page

**Primary Dependencies**: Django 5.x app stack, existing report rendering pipeline, existing PDF export stack (`html2canvas`/`jsPDF` in report page), existing PPTX export library integration from feature 006

**Storage**: PostgreSQL in Docker (`db` service) for application data; no mandatory schema migration expected for v1 if cover values remain transient per report session/export

**Testing**: Django checks/tests executed in Docker (`docker compose -f django_app/docker/docker-compose.yml exec web python manage.py test`), plus manual browser and PPTX/PDF validation runs from Docker-hosted app

**Target Platform**: Windows-native developer workflow, Docker Desktop, Django web app exposed on port 8080

**Project Type**: Containerized server-rendered Django web application with client-side report export logic

**Performance Goals**: Cover-page inclusion must not materially degrade current export UX; typical report PDF/PPTX export with covers should complete within existing acceptable desktop workflow time (target under 60 seconds for typical multi-page report)

**Constraints**: Use only existing project structure; keep Docker as the runtime and test path; preserve current report body behavior; keep back cover static; keep front-cover editable fields editable in PPTX; enforce first-cover image upload constraints (JPG/JPEG/PNG/WebP up to 10 MB); preserve fixed date format DD MMMM YYYY

**Scale/Scope**: One report workflow (`/report/`) affecting draft/final rendering plus PDF and PPTX outputs for all generated monthly site reports

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment | Notes |
|-----------|------------|-------|
| I. Windows-Native Platform Alignment | PASS | Workflow remains Windows-compatible and browser-based; Docker Desktop path is already established in project docs |
| II. Least-Privilege Development & Operations | PASS | No admin-level tooling required; implementation and tests run through existing user-level Docker/Django flow |
| III. Data Security and Database Isolation | PASS | No new external data store or secret surface introduced; asset handling remains inside authenticated app context |
| IV. Approval-Governed Production Operations | PASS | No change to deployment approval model; feature is application-level behavior enhancement |
| V. Containerized Maintainability & Observability | PASS | Implementation remains in existing containerized app and preserves current service topology |

**Post-Phase 1 re-check**: PASS. Phase artifacts specify Docker-only validation and no constitutional violations.

## Project Structure

### Documentation (this feature)

```text
specs/007-add-report-cover-pages/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── report-cover-pages.md
└── tasks.md
```

### Source Code (repository root)

```text
django_app/
├── templates/
│   └── sitesync/
│       └── report.html                 # cover page editable fields and upload controls
├── static/
│   └── sitesync/
│       ├── images/                     # default cover assets
│       └── js/
│           └── report.js               # render, PDF, PPTX inclusion and editability mapping
├── sitesync/
│   ├── views.py                        # report payload/default cover field values if needed
│   ├── services.py                     # optional report composition helpers
│   └── tests/                          # Django tests for report composition/export contracts
└── docker/
    ├── docker-compose.yml              # runtime/test orchestration (existing)
    └── Dockerfile                      # app container build (existing)

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Use the current Django application and Docker compose structure only. No alternate repository layout, no additional service, and no non-Docker test path are introduced.

## Complexity Tracking

No constitution violations or additional complexity exemptions are required.
