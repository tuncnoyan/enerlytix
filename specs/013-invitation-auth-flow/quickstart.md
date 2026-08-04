# Quickstart: Invitation-Only User Authentication

## Prerequisites

- Docker Desktop running on Windows.
- The Enerlytix `.env` file available for local/container configuration.
- Optional: `MAILTRAP_API_TOKEN` set when you want to verify real email sending instead of console output.

## Validation Commands

Run the auth-focused Django tests from the web container:

```powershell
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test sitesync.tests.test_auth_flow sitesync.tests.test_password_reset sitesync.tests.test_invitations sitesync.tests.test_user_admin
```

Run the broader app check if you want a quick smoke test after auth changes:

```powershell
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py check
```

## Manual Scenarios

### 1. Admin invitation copy path

1. Open the admin panel user page.
2. Create a new invitation.
3. Copy the invitation link from the pending list.

Expected result: the admin sees a usable invitation URL and can paste it into an external email client.

### 2. Invited user sign-up

1. Open a valid invitation link.
2. Complete the sign-up form.
3. Confirm the account is created and the invitation becomes used.

Expected result: the invitation cannot be reused after successful sign-up.

### 3. Password reset flow

1. Request a password reset for an existing user.
2. Open the reset email link.
3. Complete the password update form.

Expected result: the reset flow uses branded pages and the user can authenticate with the new password.

### 4. Logout confirmation

1. Click logout from a signed-in page.
2. Confirm the modal appears.
3. Cancel once and verify the session remains active.
4. Repeat and confirm logout.

Expected result: logout never completes without explicit confirmation.

## Notes

- Invitation emails may be manually copied from the admin panel if delivery is unavailable.
- Password reset emails should send automatically when the email backend is configured.
- If you are verifying live email sending, ensure the Docker web container has the updated dependencies and a valid Mailtrap token.