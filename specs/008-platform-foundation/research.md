# Research: Platform Foundation

## Summary

The feature should be implemented as a Django-native authentication and access-control enhancement within the existing web app. The current repository already uses Django's built-in authentication framework and has a central URL configuration, so the MVP should extend that stack rather than introducing another identity provider or separate service.

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

### Decision 3: Use Django admin and a small set of custom views for user administration

**Decision**: Expose user administration through a dedicated admin-oriented UI in the existing Django app using standard Django auth concepts and custom views; keep the initial scope focused on list, invite, enable/disable, rename, password reset, and delete.

**Rationale**: The app already uses Django's admin and URL structure, so a focused custom administration experience fits the current architecture well without introducing a new frontend framework.

**Alternatives considered**:
- Full custom admin panel with new JS framework: too large for the MVP.
- Pure Django admin with limited customization: insufficient for the required workflow and user experience.

## Open Questions Resolved

- Authentication approach: email/password with password reset.
- Invitation expiration: 7 days.
- Initial role model: administrator and standard user.
