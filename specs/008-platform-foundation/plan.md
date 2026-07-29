# Implementation Plan: Platform Foundation

**Branch**: `008-platform-foundation` | **Date**: 2026-07-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/008-platform-foundation/spec.md`

## Summary

Add a multi-user authentication and access-control foundation to the existing Django web app. The implementation will extend the current Django auth stack with email/password sign-in, password-reset support, invitation-only onboarding, a lightweight user-administration flow, and basic administrator/user roles while keeping the solution container-native and compatible with the existing Windows-based deployment model.

## Technical Context

**Language/Version**: Python 3.12 with Django web app

**Primary Dependencies**: Django authentication framework, Django templates, existing Django admin integration, containerized app runtime

**Storage**: Existing Django database (SQLite in development, likely containerized relational DB in deployment)

**Testing**: Django test suite and manual browser validation through the existing Docker-hosted app flow

**Target Platform**: Windows-native Django web app running in Docker

**Project Type**: Containerized server-rendered Django web application

**Performance Goals**: Support a small-to-medium multi-user environment with no material performance regression for normal app access

**Constraints**: Keep implementation within the existing Django app structure; avoid introducing a new frontend framework; use least-privilege account handling; use the current containerized runtime and test path

**Scale/Scope**: Initial multi-user MVP covering authentication, invitations, basic administration, and role-based access for a small hosted user base

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment | Notes |
|-----------|------------|-------|
| I. Windows-Native Platform Alignment | PASS | The work remains in the existing Django web app and Windows-friendly Docker workflow |
| II. Least-Privilege Development & Operations | PASS | The feature uses standard user-level app operations and role-based access rather than elevated privileges |
| III. Data Security and Database Isolation | PASS | Authentication and invitation flows will use Django auth protections and secure account-state handling |
| IV. Approval-Governed Production Operations | PASS | No production deployment or privileged account changes are introduced by the MVP |
| V. Containerized Maintainability & Observability | PASS | The feature stays within the existing containerized app architecture and can be tested through the current runtime |

**Post-Phase 1 re-check**: PASS. The planned artifacts preserve the existing containerized deployment model and do not introduce constitutional conflicts.

## Project Structure

### Documentation (this feature)

```text
specs/008-platform-foundation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── user-management.md
└── tasks.md
```

### Source Code (repository root)

```text
django_app/
├── config/
│   └── urls.py
├── sitesync/
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   └── templates/
│       └── sitesync/
├── templates/
│   └── registration/
└── docker/
    └── docker-compose.yml
```

**Structure Decision**: Use the current Django app, templates, and URL routing structure. No new service or framework is introduced for this MVP.

## Implementation Phases

### Phase 1: Authentication and account access

- Add or refine login and logout views and templates.
- Add password reset request and confirmed reset flows.
- Add a profile page for authenticated users.
- Protect existing app routes so unauthenticated users are redirected to sign-in.

### Phase 2: Invitation-based onboarding

- Add an invitation model and persistence for invite issuance, expiry, and acceptance state.
- Add invitation issuance and management flows for administrators.
- Add an invitation acceptance flow for new users.
- Ensure expired or already-accepted invitations are rejected clearly.

### Phase 3: User administration and basic roles

- Add user listing with account status and role information.
- Add administrator actions for enable/disable, rename, password reset, and deletion.
- Add basic role mapping for administrator and standard user.
- Restrict administrative actions to administrator accounts.

### Phase 4: Validation and hardening

- Add automated tests for authentication, invitation expiry, role enforcement, and admin actions.
- Validate the full end-to-end user flow through the Docker-hosted app.
- Document the quickstart and expected setup steps.

## Complexity Tracking

No constitution violations or additional complexity exemptions are required.
