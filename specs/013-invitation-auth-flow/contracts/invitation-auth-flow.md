# Invitation Auth Flow Contract

## Overview

This contract defines the invitation-only onboarding, password-reset, and logout-confirmation surfaces for Enerlytix.

## Routes and Actions

### Invitation Management

- `GET /panel/users/` shows pending invitations, copy actions, resend actions, and revoke actions for admins.
- `POST /panel/users/` creates a new invitation or reuses the existing pending invitation for the same email.
- `POST /panel/users/` with a resend action reactivates a pending invitation and triggers another email attempt when enabled.
- `POST /panel/users/` with a revoke action marks a pending invitation as revoked and invalidates the link.

### Invitation Acceptance

- `GET /invitations/<uuid>/accept/` opens the sign-up page for a valid invitation.
- `POST /invitations/<uuid>/accept/` creates the user account, marks the invitation as accepted, and blocks reuse.

### Password Reset

- `GET /password-reset/` shows the reset request page.
- `POST /password-reset/` triggers the reset email flow for an existing user email.
- Django tokenized reset completion pages must be available for the secure reset link flow.

### Logout

- Clicking logout must open an in-place confirmation modal on the current page.
- Confirming logout submits the existing logout route and ends the session.
- Cancelling leaves the session active.

## Email Template Contract

### Invitation Email

- Must include a usable invitation accept URL.
- Must include the invited email address context.
- Must support branded subject and body text.
- Must support manual copy fallback from the admin panel when delivery is unavailable.

### Password Reset Email

- Must include a usable password-reset URL.
- Must include branded subject and body text.
- Must use the configured email backend when available.

## Validation Rules

- Invitation links are valid only while the invitation is pending.
- Accepted, revoked, or otherwise invalid invitation links must show a clear user-facing error.
- Password-reset confirmation must require the secure token flow.
- Logout must not complete until the user explicitly confirms in the modal.