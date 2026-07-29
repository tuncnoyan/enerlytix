# Quickstart: Platform Foundation

## Prerequisites

- Docker Desktop is available and running.
- The Enerlytix Django app can be started from the existing Docker compose setup (`docker compose -f django_app/docker/docker-compose.yml up`).
- A local or test email backend is configured for password reset and invitation flows.
- PostgreSQL is running in the Docker Compose environment for persistence.

## Validation Scenarios

### Scenario 1: Authentication and Profile Access

1. Start the application using `docker compose -f django_app/docker/docker-compose.yml up`.
2. Open the browser and navigate to `http://localhost:8000/`.
3. Sign in with a valid administrator account (created during setup or via `manage.py`).
4. Confirm that the profile page loads at `/profile/` and displays account information.
5. Confirm that the top-right links menu shows an "Admin Panel" link.
6. Sign out and verify sign-out redirects to the login page.

### Scenario 2: Invitation-Based Onboarding

1. Sign in as an administrator.
2. Open the admin panel at `/panel/`.
3. Navigate to the Users section.
4. Create a new invitation for a test email address (e.g., `testuser@example.com`).
5. Verify the invitation is listed with a 7-day expiry date.
6. Accept the invitation from a new browser session or guest mode by navigating to the invitation link.
7. Complete registration with a username and password.
8. Verify the new user account becomes active.
9. Sign in as the new user and confirm standard access is available without administrative controls.

### Scenario 3: Team Creation and User Assignment

1. Sign in as an administrator.
2. Open the admin panel at `/panel/`.
3. Navigate to the Teams section.
4. Create a new root team named "Sales" with an assigned manager (an existing admin user).
5. Create a sub-team under "Sales" named "Sales North" with a team lead.
6. Assign existing users to the "Sales" and "Sales North" teams.
7. Verify the organisation hierarchy view shows the team structure correctly.

### Scenario 4: Hierarchical Access and Report Visibility

1. Sign in as a standard user who is assigned to "Sales North" team only.
2. Navigate to the reports section.
3. Confirm the user sees reports only from the "Sales North" team.
4. Sign in as the "Sales North" team lead.
5. Confirm the team lead sees reports from "Sales North" and any sub-teams within it.
6. Sign in as the "Sales" manager.
7. Confirm the manager sees reports from all teams under "Sales" (including "Sales North" and any other sub-teams).
8. Sign in as an administrator.
9. Confirm the admin sees all reports across the organisation.

### Scenario 5: Team-Gated Access and Empty State

1. Sign in as an administrator.
2. Create a new user invitation (as in Scenario 2).
3. Accept the invitation and create a new user account without assigning them to a team initially.
4. Sign in as the new user.
5. Navigate to the reports section.
6. Confirm an empty state or prompt appears indicating no team assignment yet.
7. Sign in as an administrator and assign the new user to a team.
8. Sign back in as the new user.
9. Confirm reports from their assigned team are now visible.

### Scenario 6: User and Team Management Actions

1. Sign in as an administrator.
2. Open the admin panel at `/panel/`.
3. Navigate to the Users section.
4. Disable a test user and confirm sign-in is blocked for that user.
5. Re-enable the user and confirm sign-in works again.
6. Reset a password for a user.
7. Sign in as that user with the reset password and confirm it works.
8. Change a user's username (rename).
9. Verify the user can sign in with the new username.
10. Navigate to the Teams section.
11. Change the manager of a team and verify the hierarchy is updated.
12. Transfer a team lead to another team and verify the update takes effect.

### Scenario 7: Docker-Based Regression Testing

1. From the repository root, run Django tests inside the web container:
   ```bash
   docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test sitesync.tests --verbosity 2
   ```
2. Verify all tests pass, including:
   - Authentication and sign-in flows
   - Invitation expiry and acceptance
   - User administration and account actions
   - Team creation and user assignment
   - Hierarchical access and report visibility
   - Role enforcement and admin panel access

## Expected Outcomes

- Users can sign in and out securely.
- Invitation-only onboarding works for new accounts.
- Teams can be created with hierarchical structure and managed via the admin panel.
- Users are assigned to teams and see team-gated reports.
- Administrators and managers access reports according to their organisational level.
- Team-gated access prevents users from seeing reports outside their assigned scope.
- The admin panel consolidates all administrative functions in a branded, consistent interface.
- Standard users cannot access administrative operations or the admin panel.
- All functionality works reliably within the Docker container environment with a persistent PostgreSQL database.
