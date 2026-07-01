# Implementation Plan: Utility Usage Report Visuals Page

**Branch**: `003-report-visuals-page` | **Date**: 2026-07-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-report-visuals-page/spec.md`

## Summary

Add a Report Visuals page to Enerlytix that renders a full suite of energy usage charts and tables (electricity, gas, water) for a single site over a user-selected 12-month reporting period. The page is accessed via a new "Create Report" button on the dashboard. Users can annotate each visual with free-form comments and download the complete report as a PDF. The implementation extends the existing Django/vanilla-JS application with new Django views, a JSON API endpoint, Chart.js charts, and client-side PDF export via html2canvas + jsPDF — all without introducing a frontend framework or requiring admin privileges.

## Technical Context

**Language/Version**: Python 3.14 (Django backend) + Vanilla JavaScript ES6 (browser frontend)

**Primary Dependencies**: Django (existing), Django REST Framework (existing), Chart.js 4.x (CDN — new), html2canvas 1.x (CDN — new), jsPDF 2.x (CDN — new)

**Storage**: SQLite (development), PostgreSQL (production) — existing schema extended with two migrations: `available_capacity` nullable field on `Supply`; new `Benchmark` model

**Testing**: Django `TestCase` + DRF `APITestCase` (existing pattern in `django_app/sitesync/tests/`)

**Target Platform**: Windows-native web application, containerised via Docker Compose (existing)

**Project Type**: Web application — server-rendered Django templates + client-side chart/PDF rendering

**Performance Goals**: Report page fully rendered (all charts drawn) in < 5 seconds for a single site with up to 12 months of halfhourly data (~17 500 HH records per supply)

**Constraints**: Client-side PDF generation only (no server-side rendering); no admin privileges for installation or deployment; no new npm/node build step; all JS loaded from CDN in template

**Scale/Scope**: Single-site report; up to ~20 supplies per site; 12 months × up to 48 HH readings/day per supply

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment | Notes |
|-----------|-----------|-------|
| I. Windows-Native Platform Alignment | ✅ PASS | Django + browser JS; CDN libraries load in browser; no OS-specific runtime dependencies added |
| II. Least-Privilege Development & Operations | ✅ PASS | pip installs to user virtualenv; no system-level packages; no admin required for migrations or serving |
| III. Data Security and Database Isolation | ✅ PASS | Report endpoint served through Django session auth (existing); no new auth surface; no sensitive data exposure beyond existing access controls |
| IV. Approval-Governed Production Operations | ✅ PASS | No production deployment in this sprint; schema migrations follow existing approval workflow |
| V. Containerised Maintainability & Observability | ✅ PASS | No new containers; new code follows existing Django app structure; Docker Compose unchanged |

**Post-Phase 1 re-check**: ✅ No violations introduced by data-model or contract design. New `Benchmark` model and `available_capacity` field are additive changes with nullable/optional semantics.

## Project Structure

### Documentation (this feature)

```text
specs/003-report-visuals-page/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/
│   └── report-data-api.md   ← Phase 1 output
└── tasks.md             ← Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
django_app/
├── sitesync/
│   ├── models.py              ← extend Supply (available_capacity); add Benchmark model
│   ├── views.py               ← add report_view, report_data_api_view
│   ├── urls.py                ← add /report/ and /api/report-data/ routes
│   ├── serializers.py         ← add BenchmarkSerializer
│   ├── migrations/
│   │   └── 0004_supply_available_capacity_benchmark.py   ← new migration
│   ├── templates/sitesync/
│   │   └── report.html        ← new report visuals template
│   └── static/sitesync/js/
│       └── report.js          ← chart rendering, PDF export, comment management
└── tests/
    └── unit/
        └── test_report_data.py    ← unit tests for report data calculations
```

**Structure Decision**: Single Django app extension — no new apps, no new containers. All new code is additive within `sitesync/`.

## Complexity Tracking

*No constitution violations. No complexity justification required.*
