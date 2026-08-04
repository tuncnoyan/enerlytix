# Implementation Plan: Invitation-Only User Authentication

**Branch**: `[013-invitation-auth-flow]` | **Date**: 2026-08-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/013-invitation-auth-flow/spec.md`

## Summary

Add invitation-only onboarding, branded sign-up and password-reset pages, a logout confirmation modal, and feature-specific email templates while preserving the manual copy fallback for invitations when automatic email delivery is unavailable. Keep the invitation signup flow custom, use Django's built-in password-reset lifecycle, and reuse the existing Django auth/login/logout stack and shared template layouts.

## Technical Context

**Language/Version**: Python 3.12 with Django 5.0.1

**Primary Dependencies**: Django auth/views, django-anymail 15.1, djangorestframework 3.14.0, python-dotenv, psycopg2-binary, pytest/pytest-django, existing `sitesync` app

**Storage**: SQLite for local development and tests; PostgreSQL when `DATABASE_URL` is provided; existing `Invitation` model extended for revocation state

**Testing**: Django test runner and pytest-based app tests, executed in the Docker web container via `docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test ...`

**Target Platform**: Windows-hosted, Docker-containerized Django web application

**Project Type**: Server-rendered web application

**Performance Goals**: Target p95 <= 800ms for auth page GET/POST requests, p95 <= 1200ms for admin invitation create/revoke actions, and password-reset request response <= 2s with reset email becoming usable within 2 minutes during normal operation

**Constraints**: Invitation-only onboarding remains mandatory; admins must be able to copy invitation links when email delivery is unavailable; password reset must use secure tokenized links; logout must require explicit confirmation in a modal; development and verification should stay container-first and Windows-compatible

**Scale/Scope**: Changes span the existing `sitesync` app, shared auth templates, admin panel shell, email templates, and auth-related tests across a small set of user-facing pages and routes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment | Notes |
|---|---|---|
| I. Windows-Native Platform Alignment | PASS | The feature stays within the existing Windows-friendly Django and Docker workflow |
| II. Least-Privilege Development & Operations | PASS | No admin privileges or host-level changes are required |
| III. Data Security and Database Isolation | PASS | Invitation lifecycle, password reset, and logout remain guarded by authenticated flows and secure tokens |
| IV. Approval-Governed Production Operations | PASS | No production workflow or privileged-account policy changes are introduced |
| V. Containerized Maintainability & Observability | PASS | Verification remains Docker-first and uses the existing logging/email infrastructure |

Post-Phase 1 re-check: PASS. The selected design does not require constitution exceptions.

## Project Structure

### Documentation (this feature)

```text
specs/013-invitation-auth-flow/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── invitation-auth-flow.md
└── tasks.md
```

### Source Code (repository root)

```text
django_app/
├── config/
│   ├── settings.py
│   └── urls.py
├── sitesync/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── tests/
│   └── migrations/
├── templates/
│   ├── registration/
│   └── sitesync/
└── static/
    └── sitesync/
```

**Structure Decision**: Implement the feature as additive changes inside the existing `django_app` project, with custom invitation-signup and modal logout behavior in `sitesync`, Django built-in password-reset views and templates under `templates/registration/`, shared branded layout changes in `templates/sitesync/`, and feature-specific contract and validation docs in `specs/013-invitation-auth-flow/`.

## Phase Plan

### Phase 0: Research and Decisions (Complete)

- Keep invitation signup custom and route it through the existing `sitesync` invitation accept path.
- Use Django's built-in password-reset lifecycle with custom templates rather than a new hand-rolled token system.
- Implement logout confirmation as a reusable modal in the shared template layer.
- Keep Anymail/Mailtrap as the email transport and preserve the admin copy fallback for invitations.
- Document the feature with a dedicated contract file for routes, actions, and email template variables.

### Phase 1: Design and Contracts (Complete)

- Authored [research.md](research.md) with implementation decisions and alternatives.
- Authored [data-model.md](data-model.md) with invitation lifecycle, token-flow, and UI-state entities.
- Authored [contracts/invitation-auth-flow.md](contracts/invitation-auth-flow.md) with route and email-template contracts.
- Authored [quickstart.md](quickstart.md) with Docker-first validation scenarios and test commands.

### Phase 2: Implementation Planning (Next)

- Extend invitation lifecycle handling for revoke support and no-auto-expiry behavior.
- Add branded invitation and password-reset templates with shared mail-rendering helpers.
- Replace the stub password-reset page with Django's full reset flow and matching templates.
- Add a shared logout confirmation modal and wire it into the existing topbar/profile/admin layouts.
- Expand tests for invitation copy/revoke behavior, password-reset flow, email backend behavior, and logout confirmation.

### Phase 3: Verification Planning (Next)

- Run the auth-focused Django tests in the Docker web container.
- Verify invitation creation, duplicate handling, manual copy fallback, and revoke behavior.
- Verify password-reset request, token completion, and branded email rendering.
- Verify logout requires confirmation and cancellation preserves the session.

## Complexity Tracking

No constitution violations identified; no complexity exceptions are required.
