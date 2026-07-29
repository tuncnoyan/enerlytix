# Quickstart: Platform Foundation

## Prerequisites

- Docker Desktop is available and running.
- The Enerlytix Django app can be started from the existing Docker compose setup.
- A local or test email backend is configured for password reset and invitation flows.

## Validation Scenarios

1. Start the application using the existing Docker workflow.
2. Sign in with a valid administrator account and confirm that the profile page loads.
3. Create a new invitation for a test email address and verify the invitation is listed with a 7-day expiry.
4. Accept the invitation and confirm the new account becomes active.
5. Sign in as the new user and verify standard access is available without administrative controls.
6. Disable the new account and confirm sign-in is blocked.
7. Reset a password from the admin area and confirm the user can sign in with the new password.

## Expected Outcomes

- Users can sign in and out securely.
- Invitation-only onboarding works for new accounts.
- Administrators can manage users and account state.
- Standard users cannot access administrative operations.
