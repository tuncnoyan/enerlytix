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

---

## Advanced Scenarios: Team Hierarchy Patterns (T085)

### Scenario A: Multi-Level Organizational Structure

**Setup**: Create a 3-level hierarchy representing typical enterprise org chart

1. **Level 1 (Root Team)**:
   - Create team "Operations" with manager "alice_manager"

2. **Level 2 (Sub-Teams)**:
   - Under Operations, create "Finance" with team_lead "bob_finance"
   - Under Operations, create "HR" with team_lead "carol_hr"
   - Under Operations, create "IT" with team_lead "dave_it"

3. **Level 3 (Sub-Sub-Teams)**:
   - Under Finance, create "Accounting" with team_lead "emma_accounting"
   - Under Finance, create "Payroll" with team_lead "frank_payroll"

4. **User Assignments**:
   - alice_manager: `manager` role in Operations
   - bob_finance: `team_lead` role in Finance
   - emma_accounting: `team_lead` role in Accounting, `user` role in Finance
   - frank_payroll: `user` role in Payroll
   - Assign 2-3 regular users to each leaf team

5. **Verify Access Hierarchy**:
   - alice_manager sees reports from: Operations, Finance, HR, IT, Accounting, Payroll (all sub-teams)
   - bob_finance sees reports from: Finance, Accounting, Payroll (team + sub-teams)
   - emma_accounting sees reports from: Accounting only (her primary team)
   - frank_payroll sees reports from: Payroll only

### Scenario B: Cross-Team Role Assignment (Matrix Organization)

**Setup**: User has different roles in multiple teams

1. **Create Teams**:
   - Team "Product" with manager "product_manager"
   - Team "Engineering" with manager "eng_manager"

2. **Assign User "john" to Multiple Teams**:
   - Assign john with role `manager` in Product
   - Assign john with role `team_lead` in Engineering

3. **Verify Multi-Role Assignment**:
   - Admin panel shows john with both role assignments
   - john can see reports from both Product and Engineering teams
   - john has manager privileges in Product only (can assign users to Product and sub-teams)
   - john has team_lead privileges in Engineering only

4. **Verify Admin Panel - Roles Section**:
   - Roles table shows john with 2 entries (Product + Engineering)
   - Each role can be independently revoked or modified

### Scenario C: Hierarchy Modification and Access Impact

**Setup**: Verify access changes when hierarchy structure changes

1. **Initial Setup**:
   - Create "Sales" team (manager: sales_manager)
   - Create "APAC" sub-team under Sales (manager: sales_manager)
   - Assign user "regional_lead" as team_lead in APAC
   - Create reports for APAC region

2. **Move Sub-Team**:
   - Create new "Regional" team (parent: Sales)
   - Move APAC to be a sub-team of Regional (change parent_team from Sales to Regional)
   - Verify access is maintained: sales_manager still sees APAC reports
   - Verify regional_lead still sees APAC reports

3. **Demote User Role**:
   - Change regional_lead's role from `team_lead` to `user` in APAC
   - Verify regional_lead can no longer see APAC reports as lead (only as regular user)
   - Verify reports still accessible to Sales manager (through hierarchy)

4. **Delete Empty Sub-Team**:
   - Create test sub-team with no users
   - Attempt deletion: should succeed (no cascade needed)
   - Create sub-team with users assigned
   - Attempt deletion: should fail with protection error
   - Remove all users first, then delete should succeed

### Scenario D: Large-Scale Hierarchy Performance Test

**Setup**: Verify performance with realistic organization size

1. **Create Hierarchy**:
   - 1 root team (Operations)
   - 5 sub-teams (Finance, Sales, Engineering, HR, Legal)
   - 3 sub-sub-teams under each (15 total)
   - 50-100 users distributed across teams

2. **Performance Checks**:
   - Admin panel loads in <2 seconds
   - Team list with 20+ teams displays in <1 second
   - User list with 100 users displays in <1 second
   - Hierarchy view renders in <2 seconds
   - Report access queries complete in <500ms (for user in deep hierarchy)

3. **Concurrent Access**:
   - Open multiple browser sessions with different roles
   - Verify each session shows correct reports (no data leakage)
   - Simulate 5+ concurrent users accessing reports
   - Monitor for performance degradation

### Scenario E: Role-Based Visibility in Admin Panel

**Setup**: Verify different admin panel views for different roles

1. **Admin User** (superuser):
   - Sees all users, all teams, all role assignments
   - Can perform all actions (create, edit, delete)

2. **Manager User** (manager role in Operations):
   - Can see only Operations team and sub-teams
   - Can see only users in Operations hierarchy
   - Cannot see Finance/HR/Legal/etc. teams
   - Can create sub-teams under Operations
   - Cannot create root teams

3. **Team Lead User** (team_lead in specific team):
   - Can view their own team and direct sub-teams
   - Cannot perform admin panel operations (only available to admin/managers)
   - Can see team members only for their own teams

4. **Regular User**:
   - Cannot access admin panel at all
   - Error message: "You do not have permission to access the admin panel"

---

## Testing Commands

### Run All Integration Tests
```bash
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test tests.integration --verbosity 2
```

### Run Specific Test Files
```bash
# Team hierarchy tests
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test tests.integration.test_team_hierarchy_full

# Admin panel tests  
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test tests.integration.test_admin_panel_full

# Report access tests
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test tests.integration.test_report_access_team

# All Phase 7 tests (110 total)
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test tests.integration --pattern="*.py"
```

### Manual Test Run Sequence
1. Start Docker: `docker compose -f django_app/docker/docker-compose.yml up -d`
2. Reset DB: `docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py flush --noinput && docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py migrate`
3. Create admin: `docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py createsuperuser`
4. Run scenarios A-E from this section
5. Follow manual validation checklist in [MANUAL_VALIDATION.md](MANUAL_VALIDATION.md)
6. Verify all tests pass: `powershell .specify/scripts/powershell/test-integration.ps1`
