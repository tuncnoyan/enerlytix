# Research: Platform Foundation

## Summary

The feature should be implemented as a Django-native authentication, team-management, and access-control enhancement within the existing web app. The current repository already uses Django's built-in authentication framework and has a central URL configuration, so the MVP should extend that stack to include hierarchical team structures, overlapping role support, a consolidated admin panel, and team-based report access scoping.

## Decisions

### Decision 1: Use Django's built-in authentication with email/password sign-in

**Decision**: Implement sign-in, sign-out, password reset, and profile access using Django's built-in auth system and existing Django views and templates.

**Rationale**: The repository already includes Django authentication wiring in the main URL configuration, and the app is already a Django server-rendered application. This is the lowest-risk way to add secure multi-user access while preserving the current deployment model.

**Alternatives considered**:
- External SSO/identity provider integration: higher setup cost and operational complexity for this MVP.
- Magic-link-only authentication: simpler for some cases but less aligned with the stated requirement for standard sign-in and password recovery.

### Decision 2: Use invitation-based registration rather than open self-registration

**Decision**: Add an invitation model and flow that allows administrators to issue invitations, each valid for 7 days, and only allow account activation through a valid invitation.

**Rationale**: This satisfies the requirement for invite-only registration and provides a clear governance boundary for who can join the hosted environment.

**Alternatives considered**:
- Open registration plus manual approval: weaker control and less aligned with invite-only onboarding.
- Separate tenant/subscription system: unnecessary for the initial multi-user foundation.

### Decision 3: Use Django admin and a consolidated custom admin panel for user and team administration

**Decision**: Expose all user and team administration through a dedicated "panel" page using standard Django auth concepts and custom views; consolidate user list, invitations, team management, organisational hierarchy view, and role assignments in one branded page. Keep the initial scope focused on list, invite, enable/disable, rename, password reset, delete, and team operations.

**Rationale**: The app already uses Django's admin and URL structure, so a focused custom administration experience fits the current architecture well without introducing a new frontend framework. Consolidating all admin functions in one panel provides a unified control surface and improves discoverability.

**Alternatives considered**:
- Full custom admin panel with new JS framework: too large for the MVP.
- Pure Django admin with limited customization: insufficient for the required workflow and user experience.
- Distributed admin pages (/users/, /teams/, /hierarchy/): confusing navigation and inconsistent experience.

### Decision 4: Support hierarchical team structures with sub-teams

**Decision**: Implement teams with optional parent-team references, allowing sub-teams to exist within parent teams. A user's access scope includes their assigned team and all sub-teams within their hierarchy level based on their role.

**Rationale**: This supports flexible organisational structures while remaining simple to implement and test. Report access follows the hierarchy naturally.

**Alternatives considered**:
- Flat teams only: insufficient for complex organisations.
- Full matrix team membership: too complex for the initial MVP.

### Decision 5: Allow overlapping roles (multi-role support)

**Decision**: Store roles as a set of independent flags or assignments on a user, allowing a single user to hold multiple roles simultaneously (e.g., both manager and team lead).

**Rationale**: In smaller organisations, one person often wears multiple hats. This avoids forced role reassignments during restructuring and provides flexibility while keeping the permission model clear.

**Alternatives considered**:
- Exclusive roles: forced reassignments and less flexibility for complex hierarchies.
- Role nesting rules: complex permission logic and harder to test.

### Decision 6: Implement hierarchical report access with inheritance

**Decision**: Report access is determined by team membership and role. A user can access reports from their assigned team and all sub-teams within their access scope. Managers access all reports from teams they manage and sub-teams. Admins access all reports.

**Rationale**: Aligns with hierarchical team structures and allows reporting at each organisational level while preventing cross-branch access unless explicitly granted.

**Alternatives considered**:
- Team-scoped flat access: insufficient for hierarchies.
- Manager-determined per-user rules: too complex for the initial MVP.

### Decision 7: Implement team-gated report access with empty-state prompts

**Decision**: New users begin with no team assignment and see an empty state or prompt until an administrator assigns them to a team. Report visibility is gated by team membership.

**Rationale**: Ensures clear accountability for access provisioning and prevents accidental over-exposure of reports. Provides a clear onboarding flow.

**Alternatives considered**:
- Auto-assign to default team: less explicit control.
- Role-based defaults: admins/managers see reports immediately, but confusing for standard users.

## Open Questions Resolved

- Authentication approach: email/password with password reset.
- Invitation expiration: 7 days.
- Role model: four roles (admin, manager, team lead, user) with overlapping support.
- Team structure: hierarchical with sub-teams.
- Report access: hierarchical with inheritance, team-gated for new users.
- Admin panel: consolidated with all functions in one branded page.

