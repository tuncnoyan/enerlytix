# Implementation Plan: Homepage Refresh

**Branch**: `[014-homepage-refresh]` | **Date**: 2026-08-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/014-homepage-refresh/spec.md`

## Summary

Refactor the public home page so regular users only see site discovery and supply inspection, move refresh/import/report actions into the admin area, add a supply filter plus an inactive-meter toggle with inactive supplies excluded by default, and introduce an admin-only import review page with CSV/XLSX export for the current filtered view. Preserve the legacy `consumption-display` route as a compatibility redirect into the new admin page.

## Technical Context

**Language/Version**: Python 3.11+ with Django 5.0.1

**Primary Dependencies**: Django, Django REST Framework, pytest, pytest-django, openpyxl, vanilla JS/CSS assets

**Storage**: SQLite for local development and repository fixtures; PostgreSQL supported in deployment via `psycopg2-binary`

**Testing**: `pytest`, `pytest-django`, and targeted `python manage.py test` runs for `sitesync` app coverage

**Target Platform**: Windows-hosted browser-based web app, developed in `django_app`

**Project Type**: Django web application with server-rendered templates and AJAX-backed dashboard panels

**Performance Goals**: Keep dashboard interactions responsive; supply filtering and export generation should not add avoidable round trips or block page interaction longer than the current UX budget

**Constraints**: Preserve role-based access control, keep admin actions behind `admin_panel_required`, maintain compatibility with the legacy `consumption-display` URL, and default inactive supplies to hidden

**Scale/Scope**: One public dashboard, one admin dashboard, one new admin import review page, one legacy redirect, and filtered CSV/XLSX exports

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The feature is consistent with the constitution: it remains Windows-native, avoids elevated privileges, keeps admin actions role-gated, and does not introduce new deployment or security exceptions.

## Project Structure

### Documentation (this feature)

```text
specs/014-homepage-refresh/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── routes.md
└── tasks.md
```

### Source Code (repository root)

```text
django_app/
├── sitesync/
│   ├── views.py
│   ├── services.py
│   ├── urls.py
│   ├── serializers.py
│   ├── forms.py
│   ├── templates/
│   │   └── sitesync/
│   │       ├── site_list.html
│   │       ├── supply_list.html
│   │       ├── consumption_display.html
│   │       ├── panel_dashboard.html
│   │       ├── panel_base.html
│   │       └── admin_audit_logs.html
│   └── static/
│       └── sitesync/
│           ├── js/
│           │   ├── site_selection.js
│           │   ├── site_search.js
│           │   └── consumption_display.js
│           └── cxg-base.css
└── tests/
    ├── contract/
    ├── integration/
    └── unit/
```

**Structure Decision**: Keep the implementation inside the existing `django_app/sitesync` Django app so the public home page, admin panel, and consumption review flow can share views, templates, and the existing JavaScript lifecycle with minimal surface area.

## Complexity Tracking

No constitution violations are expected, so no complexity justification is required.
