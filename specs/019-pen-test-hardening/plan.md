# Implementation Plan: Pen-Test Hardening and Readiness

**Branch**: `[019-pen-test-hardening]` | **Date**: 2026-08-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/019-pen-test-hardening/spec.md`

## Summary

Harden Enerlytix against identified pen-test blockers by enforcing strict authn/authz on sensitive endpoints, removing predictable credential flows, tightening redirect/error/IP-trust behavior, and introducing fail-closed production security gates. The implementation will use existing Django + DRF patterns, role checks, and audit logging while adding explicit regression tests and deployment-readiness validation aligned to constitution security and Docker workflow principles.

## Technical Context

**Language/Version**: Python 3.12 runtime (workspace-configured Pipenv), Django app dependencies pinned around Django 5.0.1

**Primary Dependencies**: Django, Django REST Framework, requests, python-dotenv, django-anymail, openpyxl, gunicorn, whitenoise

**Storage**: PostgreSQL in containerized development/production-style runs; SQLite fallback exists for local checks

**Testing**: Django test runner (`python manage.py test`) as primary; pytest/pytest-django available; deployment security check via `python manage.py check --deploy`

**Target Platform**: Containerized web deployment with Docker Compose workflows; Windows-native developer operations

**Project Type**: Django web application (server-rendered + JSON API endpoints)

**Performance Goals**: No material degradation to protected endpoint behavior; security checks complete within normal CI/runtime startup windows; manual sync/import endpoints remain operational for authorized users only

**Constraints**: Must preserve existing role-governance model and auditability; must run all validation commands in Docker-defined environment per constitution; must enforce 401/403 response semantics defined in spec clarifications

**Scale/Scope**: Targeted hardening of authentication/authorization, credential workflows, redirect/error handling, proxy trust, and production security gates across `django_app/config` and `django_app/sitesync` modules plus associated tests/docs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Principle I (Windows-Native Platform Alignment): PASS
  - Plan preserves current Windows-friendly operational workflow and avoids non-Windows-only assumptions.
- Principle II (Least-Privilege Development & Operations): PASS
  - Hardening reduces privilege exposure and does not introduce admin-required local workflows.
- Principle III (Data Security and Database Isolation): PASS
  - Core feature scope directly improves access control, secret safety posture, and audit trust boundaries.
- Principle IV (Approval-Governed Production Operations): PASS
  - Introduces explicit fail-closed release/startup security gating and retains auditable admin actions.
- Principle V (Containerized Maintainability, Docker Compatibility & Observability): PASS
  - Validation and testing commands remain Docker-first, with audit/event logging preserved and expanded.

Post-Design Re-check: PASS (no design decisions violate constitution constraints).

## Project Structure

### Documentation (this feature)

```text
specs/019-pen-test-hardening/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── security-hardening-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
django_app/
├── config/
│   ├── settings.py
│   └── urls.py
├── sitesync/
│   ├── views.py
│   ├── services.py
│   ├── forms.py
│   ├── urls.py
│   └── tests/
│       ├── test_*.py
│       └── ...
└── docker/
    └── docker-compose.yml

deployment/
├── SECURITY_CHECKLIST.md
└── PLATFORM_FOUNDATION_CHECKLIST.md

docs/
└── SECRET_MANAGEMENT.md
```

**Structure Decision**: Use the existing single Django web-application structure and implement hardening in-place across settings, views, and tests to minimize risk and preserve operational familiarity.

## Complexity Tracking

No constitution violations requiring justification.
