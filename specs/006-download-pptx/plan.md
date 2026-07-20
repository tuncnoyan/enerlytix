# Implementation Plan: Download as PPTX

**Branch**: `[not-set]` | **Date**: 2026-07-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-download-pptx/spec.md`

## Summary

Add a Download as PPTX action beside the existing PDF button on the report page, using the current report section layout to generate a PowerPoint deck that preserves report fidelity while keeping comment boxes and key text editable. The implementation stays client-side in the existing Django/vanilla-JavaScript app, reuses the current `html2canvas` capture flow, and outputs a 16:9 landscape presentation with one slide per report section.

## Technical Context

**Language/Version**: Python 3.14 + Django 5.0.1 backend, vanilla JavaScript ES6 frontend

**Primary Dependencies**: Django, Django REST Framework, Chart.js 4.x (existing), html2canvas 1.x (existing), jsPDF 2.x (existing), PptxGenJS or equivalent PPTX generation library loaded in the browser

**Storage**: N/A for the export artifact itself; no database schema changes expected

**Testing**: Django `TestCase` / request tests for any supporting backend changes, plus manual browser validation of the export flow and downloaded deck in PowerPoint-compatible software

**Target Platform**: Windows-native Django web application, browser-based report page, container-capable via existing Docker setup

**Project Type**: Web application with server-rendered Django templates and lightweight client-side export logic

**Performance Goals**: Typical report export should complete within 60 seconds for a multi-section report and remain usable on the supported desktop browser; PDF export performance must remain unchanged

**Constraints**: Keep the feature client-side; do not introduce a new backend export service or frontend framework; preserve the existing PDF download path; keep slide layout landscape 16:9; make visuals/tables image-based while keeping comment boxes and key labels editable; avoid admin-privileged setup or new host dependencies

**Scale/Scope**: Single report page workflow with one slide per report section; report decks may include multiple sections, charts, tables, headings, and editable comment boxes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment | Notes |
|-----------|------------|-------|
| I. Windows-Native Platform Alignment | PASS | Browser-based report export remains Windows-friendly and does not introduce non-Windows assumptions |
| II. Least-Privilege Development & Operations | PASS | No admin-only tooling or privileged host changes required |
| III. Data Security and Database Isolation | PASS | No new data exposure surface; export uses existing authenticated report data |
| IV. Approval-Governed Production Operations | PASS | No production deployment or privilege workflow changes in scope |
| V. Containerized Maintainability & Observability | PASS | No new containers or service topology changes; implementation stays within the existing Django app |

**Post-Phase 1 re-check**: PASS. The planned artifacts are documentation-only at this stage and introduce no constitutional conflicts.

## Project Structure

### Documentation (this feature)

```text
specs/006-download-pptx/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── report-pptx-export.md
└── tasks.md
```

### Source Code (repository root)
```text
django_app/
├── templates/
│   └── sitesync/
│       └── report.html        # add PPTX button and load export library
├── static/
│   └── sitesync/
│       └── js/
│           └── report.js      # add PPTX export flow beside downloadPdf()
└── sitesync/
    └── tests/
        └── test_report_pptx_export.py   # focused export-related tests if backend support is added later
```

**Structure Decision**: Extend the existing Django `sitesync` report page and its client-side export script; keep the feature inside the current web app and browser JavaScript surface. No new app, package, mobile tree, or backend export service is required for v1.

## Complexity Tracking

No constitution violations or exceptional complexity justifications are required for this plan.
