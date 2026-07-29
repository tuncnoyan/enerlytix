# Implementation Plan: Platform Foundation

**Branch**: `008-platform-foundation` | **Date**: 2026-07-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/008-platform-foundation/spec.md`

## Summary

Add a multi-user authentication, team-management, and access-control foundation to the existing Django web app. The implementation will extend the current Django auth stack with email/password sign-in, password-reset support, invitation-only onboarding, hierarchical team structures with sub-teams, a consolidated admin panel for user and team management, and overlapping role support (admin, manager, team lead, user) while keeping the solution container-native and compatible with the existing Windows-based deployment model. Report access will be scoped hierarchically by team membership and role.

**Status**: Scope expanded to include organisational hierarchy and consolidated admin panel following clarification sessions.

## Technical Context

**Language/Version**: Python 3.12 with Django web app

**Primary Dependencies**: Django authentication framework, Django ORM for team/role models, Django templates, existing Django admin integration, containerized app runtime (Docker)

**Storage**: Containerized PostgreSQL (via Docker Compose) for persistent user, team, invitation, and role data

**Testing**: Django test suite executed inside the Docker web container using `docker compose exec -T web python manage.py test`, plus manual browser validation through the running Docker app

**Target Platform**: Windows-native Django web app running in Docker with Compose networking and PostgreSQL service

**Project Type**: Containerized server-rendered Django web application

**Performance Goals**: Support a small-to-medium multi-user environment (hundreds of users, hierarchical teams with ~10 levels) with no material performance regression for normal app access and report queries

**Constraints**: Keep implementation within the existing Django app structure; avoid introducing a new frontend framework; use least-privilege account handling; use the current containerized runtime and Docker-based test path; maintain consistency with existing home-page styling for the admin panel

**Scale/Scope**: Multi-user MVP covering authentication, invitations, hierarchical team management, overlapping roles, consolidated admin panel, team-gated report access, and role-based access control for a small hosted user base

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

### Phase 3: User administration and roles

- Add user listing with account status and role information.
- Add administrator actions for enable/disable, rename, password reset, and deletion.
- Implement multi-role support (users can hold admin, manager, team lead, or user roles simultaneously).
- Restrict administrative actions to administrator accounts.

### Phase 4: Team hierarchy and management

- Add a Team model with parent-team support for hierarchical structure.
- Add UserTeamAssignment to track team membership.
- Implement team creation, editing, and deletion in the admin panel.
- Implement user assignment to teams via the admin panel.
- Implement manager and team lead assignment within teams.
- Ensure team hierarchy updates propagate to report access scoping.

### Phase 5: Consolidated admin panel

- Create a branded "panel" page at /panel/ with layout and colour scheme matching the home page.
- Consolidate all admin functions in the panel: user management, team management, organisational hierarchy view, and role assignments.
- Add navigation sections for Users, Teams, and Hierarchy.
- Add quick-links to common admin operations.
- Ensure admin panel link appears in home-page top-right links menu only for admins.

### Phase 6: Report access scoping and validation

- Implement team-gated report access: users see reports only from teams they are assigned to.
- Implement hierarchical access: managers see reports from teams they manage and all sub-teams; team leads see team and sub-team reports within their scope.
- Add empty-state messaging for users with no team assignment.
- Validate end-to-end report access through different user roles and team assignments.

### Phase 7: Validation and hardening

- Add automated tests for authentication, invitation expiry, role enforcement, team management, and admin actions.
- Add tests for hierarchical team access and report visibility scoping.
- Validate the full end-to-end user and team management flow through the Docker-hosted app.
- Test team hierarchy changes and verify report access updates correctly.
- Document the quickstart with team setup and team-based access scenarios.

## Complexity Tracking

**Scope Expansion Note**: The original MVP scope (authentication, invitations, basic user admin, two roles) has been expanded following clarification sessions to include:
- Hierarchical team structures with sub-teams
- Overlapping roles (multi-role support per user)
- Consolidated admin panel consolidating users, teams, roles, and hierarchy
- Hierarchical report access with inheritance
- Team-gated report visibility for new users

This expansion increases implementation effort but aligns with business requirements for organisational structure and team-based access control. No constitution violations are introduced; the implementation remains within the existing Django app and containerized architecture.

**Justification**: The expanded scope is required to support the organisational structure and permission model outlined in the clarified requirements. The technical implementation remains straightforward using Django ORM and existing patterns, and the Docker-based testing path accommodates the additional test coverage needed.

No additional complexity exemptions are required beyond scope acknowledgment.
