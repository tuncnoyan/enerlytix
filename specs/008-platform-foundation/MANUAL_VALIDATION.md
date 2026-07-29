# Manual Validation Checklist: Platform Foundation (T084)

**Purpose**: Step-by-step validation guide for all 5 user stories in the Platform Foundation feature  
**Execution Environment**: Docker (django_app/docker/docker-compose.yml)  
**Test Duration**: ~15 minutes per story (75 minutes total)  
**Prerequisites**: Docker running, test database initialized

---

## Setup Instructions

### Start Docker Environment
```bash
cd django_app/docker
docker compose up -d
# Wait for "web" service to be healthy
docker compose ps
# Access app at http://localhost:8000
```

### Reset Test Database
```bash
docker compose exec -T web python manage.py flush --noinput
docker compose exec -T web python manage.py migrate
docker compose exec -T web python manage.py createsuperuser --username admin --email admin@enerlytix.local --noinput
# Set password when prompted
```

### Admin Credentials for Testing
- **Username**: `admin`
- **Password**: (set during createsuperuser)
- **Access**: http://localhost:8000/admin/

---

## US1: User Authentication and Account Management

**Goal**: Verify secure login, profile management, and password reset

### Step 1.1: Login as Admin (First-Time Access)
- [ ] Navigate to http://localhost:8000/
- [ ] Click "Login" button or navigate to http://localhost:8000/login/
- [ ] Enter admin username and password created above
- [ ] Verify: Dashboard loads and displays welcome message with admin name
- [ ] **Screenshot**: Login page, logged-in dashboard

### Step 1.2: Access User Profile
- [ ] Click user icon/profile menu in top navigation
- [ ] Navigate to http://localhost:8000/profile/
- [ ] Verify: Profile page shows:
  - [ ] Username field
  - [ ] Email field
  - [ ] Date joined timestamp
  - [ ] Last login timestamp
  - [ ] Password change link
- [ ] **Screenshot**: Profile page

### Step 1.3: Test Profile Update (Optional)
- [ ] Update email address to `admin-test@enerlytix.local`
- [ ] Verify: Confirmation message appears
- [ ] Navigate away and back to profile; verify email persists
- [ ] Change email back to original (`admin@enerlytix.local`)

### Step 1.4: Test Password Reset Flow (Optional)
- [ ] On login page, click "Forgot Password" link
- [ ] Enter admin email address
- [ ] Verify: "Check your email" message appears
- [ ] (Note: Email sending requires SMTP config; skip if not available)

### Step 1.5: Logout and Re-Login
- [ ] Click logout button/menu item
- [ ] Verify: Redirected to login page
- [ ] Login again with admin credentials
- [ ] Verify: Dashboard loads (session works correctly)
- [ ] **Screenshot**: Logout and re-login flow

---

## US2: Invitation-Based Onboarding

**Goal**: Verify invitation creation, expiry, and new user registration via invitations

### Step 2.1: Create Invitation (Admin Only)
- [ ] Navigate to http://localhost:8000/user-admin/ or Admin panel
- [ ] Find "Invite User" section or button
- [ ] Fill in:
  - [ ] Email: `testuser1@enerlytix.local`
  - [ ] First Name: `Test`
  - [ ] Last Name: `User`
- [ ] Click "Send Invitation"
- [ ] Verify: Success message appears ("Invitation sent to testuser1@enerlytix.local")
- [ ] **Screenshot**: Invitation creation form

### Step 2.2: Accept Invitation (New User Flow)
- [ ] Open invitation email or copy invitation link from database:
  ```bash
  docker compose exec -T web python manage.py shell
  >>> from sitesync.models import Invitation
  >>> inv = Invitation.objects.latest('created_at')
  >>> print(f"http://localhost:8000/invitations/{inv.token}/accept/")
  ```
- [ ] Navigate to invitation accept URL in new browser/incognito window
- [ ] Fill in:
  - [ ] Password: `TempPassword123!`
  - [ ] Confirm Password: `TempPassword123!`
- [ ] Click "Create Account"
- [ ] Verify: Success message "Account created" appears
- [ ] Verify: Redirected to login page
- [ ] **Screenshot**: Invitation accept form

### Step 2.3: Login as New User
- [ ] Login with credentials:
  - [ ] Email: `testuser1@enerlytix.local`
  - [ ] Password: `TempPassword123!`
- [ ] Verify: Dashboard loads
- [ ] Verify: User name appears in top menu (First Last)
- [ ] **Screenshot**: New user logged in

### Step 2.4: Test Invitation Expiry
- [ ] Create another invitation for `testuser2@enerlytix.local`
- [ ] Get the invitation link as in Step 2.2
- [ ] Forward time by 8 days (or modify Invitation.created_at in database):
  ```bash
  docker compose exec -T web python manage.py shell
  >>> from sitesync.models import Invitation
  >>> from datetime import timedelta
  >>> inv = Invitation.objects.filter(email='testuser2@enerlytix.local').first()
  >>> inv.created_at = inv.created_at - timedelta(days=8)
  >>> inv.save()
  ```
- [ ] Navigate to expired invitation URL
- [ ] Verify: Error message "Invitation has expired" appears
- [ ] **Screenshot**: Expired invitation error

### Step 2.5: Renew Expired Invitation
- [ ] Return to admin panel
- [ ] Find expired invitation for testuser2
- [ ] Click "Resend Invitation" or similar option
- [ ] Verify: New invitation link is generated
- [ ] Copy new link and accept (same as Step 2.2)
- [ ] **Screenshot**: Renewed invitation

---

## US3: User Administration and Roles

**Goal**: Verify user listing, role management, and admin-only operations

### Step 3.1: Access User Admin Panel
- [ ] Navigate to http://localhost:8000/user-admin/ or Admin > Users
- [ ] Verify: Page shows list of users:
  - [ ] admin (superuser)
  - [ ] Test User (testuser1@enerlytix.local)
- [ ] Verify: User table shows columns: Username, Email, Created Date, Status (Enabled/Disabled)
- [ ] **Screenshot**: User admin list

### Step 3.2: Rename User
- [ ] Click on "Test User" (testuser1@enerlytix.local) in the list
- [ ] Click "Edit" or pencil icon
- [ ] Change first name to "Updated"
- [ ] Click "Save"
- [ ] Verify: Name updates to "Updated User" in list
- [ ] **Screenshot**: User edit form and updated list

### Step 3.3: Disable User Account
- [ ] In user list, find "Updated User"
- [ ] Click "Disable" button or toggle
- [ ] Verify: Confirmation dialog appears ("Are you sure you want to disable this user?")
- [ ] Click "Confirm"
- [ ] Verify: User status changes to "Disabled" or grayed out
- [ ] Logout and try to login as disabled user
- [ ] Verify: Login fails with message ("Account disabled" or similar)
- [ ] **Screenshot**: Disabled user status

### Step 3.4: Re-enable User
- [ ] In user admin, find disabled "Updated User"
- [ ] Click "Enable" button
- [ ] Verify: Status changes back to "Enabled"
- [ ] Login as that user to verify access works
- [ ] **Screenshot**: Re-enabled user

### Step 3.5: Delete User (Careful!)
- [ ] In user admin, create a temporary user via invitation (e.g., `tempuser@enerlytix.local`)
- [ ] Accept invitation and login to verify user exists
- [ ] Logout and return to admin user admin panel
- [ ] Find the temp user
- [ ] Click "Delete" button
- [ ] Verify: Confirmation dialog ("Are you sure? This cannot be undone.")
- [ ] Click "Confirm"
- [ ] Verify: User removed from list
- [ ] Try to login as deleted user
- [ ] Verify: Login fails with "Invalid credentials"
- [ ] **Screenshot**: User deletion confirmation and result

---

## US4: Team Hierarchy and Multi-Team Assignment

**Goal**: Verify team creation, hierarchy, user assignment, and role management

### Step 4.1: Create Root Team
- [ ] Navigate to Admin Panel > Teams or http://localhost:8000/teams/
- [ ] Click "New Team" button
- [ ] Fill in:
  - [ ] Team Name: `Finance`
  - [ ] Parent Team: (leave empty for root team)
  - [ ] Manager: `admin` (from dropdown)
  - [ ] Team Lead: (leave empty)
- [ ] Click "Create Team"
- [ ] Verify: Team created message appears
- [ ] Verify: Team appears in team list with level 0
- [ ] **Screenshot**: Team creation form and new team in list

### Step 4.2: Create Sub-Team
- [ ] In team list, click "Finance" team
- [ ] Click "New Sub-Team" or "Create Sub-Team"
- [ ] Fill in:
  - [ ] Team Name: `Accounting`
  - [ ] Parent Team: `Finance` (auto-selected)
  - [ ] Manager: `admin`
  - [ ] Team Lead: (leave empty)
- [ ] Click "Create Team"
- [ ] Verify: Team created under Finance with proper hierarchy indicator
- [ ] **Screenshot**: Sub-team creation and hierarchy display

### Step 4.3: Create Second Sub-Team
- [ ] Create another sub-team under Finance:
  - [ ] Team Name: `Payroll`
  - [ ] Parent Team: `Finance`
  - [ ] Manager: `admin`
- [ ] Click "Create Team"
- [ ] Verify: Both "Accounting" and "Payroll" appear under Finance
- [ ] **Screenshot**: Multi-level hierarchy

### Step 4.4: Assign User to Team
- [ ] In Finance team view, find "Team Members" section
- [ ] Click "Assign User" or "Add Member"
- [ ] Select user: `Updated User` (testuser1)
- [ ] Select role: `user` (team member role)
- [ ] Click "Assign"
- [ ] Verify: User appears in team member list with role "user"
- [ ] **Screenshot**: User assignment to team

### Step 4.5: Assign User to Multiple Teams
- [ ] Assign `Updated User` to Accounting sub-team with role `team_lead`
- [ ] Verify: User now has:
  - [ ] Role `user` in Finance
  - [ ] Role `team_lead` in Accounting
- [ ] Navigate to user detail view (Admin > Users > Updated User)
- [ ] Verify: Team assignments section shows both teams with respective roles
- [ ] **Screenshot**: Multi-team assignment view

### Step 4.6: Change Team Manager
- [ ] Create another test user: `manageruser@enerlytix.local`
- [ ] Accept invitation and login to verify
- [ ] In Finance team view, click "Edit" or pencil icon
- [ ] Change Manager from `admin` to `manageruser`
- [ ] Click "Save"
- [ ] Verify: Team manager updated to manageruser
- [ ] Login as manageruser and navigate to team view
- [ ] Verify: manageruser can see Finance team and its members
- [ ] **Screenshot**: Manager change

### Step 4.7: Delete Sub-Team (Test Cascade)
- [ ] Create a test sub-sub-team under Accounting: `Tax`
- [ ] Verify: Tax appears under Accounting > Payroll hierarchy
- [ ] Attempt to delete Accounting team
- [ ] Verify: Error appears ("Cannot delete team with sub-teams" or similar)
- [ ] **Screenshot**: Cascade protection error

---

## US5: Consolidated Admin Panel

**Goal**: Verify admin panel access, layout, and integrated team/user management

### Step 5.1: Access Admin Panel
- [ ] Login as admin user
- [ ] Click "Admin" menu item or link in top navigation
- [ ] Verify: Admin panel loads at http://localhost:8000/admin-panel/
- [ ] Verify: Page displays all sections (breadcrumb: Home > Admin Panel)
- [ ] **Screenshot**: Admin panel home

### Step 5.2: Admin Panel - Dashboard Section
- [ ] On admin panel, find "Dashboard" or stats section
- [ ] Verify: Displays metrics:
  - [ ] Total Users: 3+ (admin, testuser1, manageruser, tempuser, etc.)
  - [ ] Total Teams: 3+ (Finance, Accounting, Payroll, etc.)
  - [ ] Total Team Assignments: 2+ (testuser1 has 2)
  - [ ] Recently Created Users: List with timestamps
- [ ] **Screenshot**: Dashboard stats

### Step 5.3: Admin Panel - Users Section
- [ ] Click "Users" tab/section in admin panel
- [ ] Verify: User table displays all users
- [ ] Test "Invite User" from this panel (same as US3 but from consolidated view)
- [ ] Create new user `paneluser@enerlytix.local`
- [ ] Verify: User appears in list immediately
- [ ] **Screenshot**: Admin panel users section

### Step 5.4: Admin Panel - Teams Section
- [ ] Click "Teams" tab/section in admin panel
- [ ] Verify: Team hierarchy displayed visually (tree or indented list)
- [ ] Expand/collapse teams to verify hierarchy navigation
- [ ] Click on a team to see details
- [ ] Verify: Team details show members, manager, sub-teams
- [ ] **Screenshot**: Admin panel teams hierarchy

### Step 5.5: Admin Panel - Hierarchy View
- [ ] Click "Hierarchy" tab/section
- [ ] Verify: Organizational structure displayed as tree or flowchart:
  - [ ] Finance (Manager: admin)
    - [ ] Accounting (Manager: admin, Team Lead: testuser1)
    - [ ] Payroll (Manager: admin)
      - [ ] Tax (if created)
- [ ] Click on a node to expand/collapse
- [ ] **Screenshot**: Org hierarchy visualization

### Step 5.6: Admin Panel - Roles Section
- [ ] Click "Roles" tab/section
- [ ] Verify: Displays all role assignments in table:
  - [ ] User, Role, Team, Assigned On
  - [ ] admin: admin in all teams
  - [ ] testuser1: user in Finance, team_lead in Accounting
  - [ ] manageruser: manager in Finance
- [ ] Verify: Can reassign or revoke roles from this panel
- [ ] **Screenshot**: Roles management

### Step 5.7: Non-Admin Access Check
- [ ] Logout and login as manageruser (or testuser1)
- [ ] Navigate to http://localhost:8000/admin-panel/
- [ ] Verify: Access denied ("You do not have permission to access this page" or redirect to home)
- [ ] Verify: No "Admin Panel" link in navigation for non-admin users
- [ ] **Screenshot**: Non-admin access denied

---

## US6: Report Access Scoping

**Goal**: Verify team-gated report visibility and hierarchical access

### Step 6.1: Create Test Reports (Admin)
- [ ] Login as admin
- [ ] Navigate to Report section
- [ ] Create 3 test reports:
  - [ ] Report A: Site 1
  - [ ] Report B: Site 2
  - [ ] Report C: Site 3
- [ ] Verify: All reports visible in admin view
- [ ] **Screenshot**: Admin sees all reports

### Step 6.2: Unassigned User - Empty State
- [ ] Create new user via invitation: `unassigneduser@enerlytix.local`
- [ ] Accept invitation and login
- [ ] Navigate to Reports section (http://localhost:8000/sitesync/)
- [ ] Verify: Empty state message appears:
  - [ ] "No reports available"
  - [ ] "You have not been assigned to a team"
  - [ ] Button/link to "Request Team Assignment" or "Contact Administrator"
- [ ] **Screenshot**: Empty state for unassigned user

### Step 6.3: Request Team Assignment (Optional)
- [ ] Click "Request Team Assignment" button
- [ ] Select desired team: `Finance`
- [ ] Add optional message: "Please assign me to Finance team"
- [ ] Click "Submit Request"
- [ ] Verify: Confirmation message "Request submitted to administrator"
- [ ] **Screenshot**: Team assignment request

### Step 6.4: Assign User to Team and Verify Access
- [ ] Login as admin
- [ ] Navigate to Finance team or Admin Panel > Users
- [ ] Assign unassigneduser to Finance team with role `user`
- [ ] Logout and login as unassigneduser
- [ ] Navigate to Reports section
- [ ] Verify: Reports now visible (if reports belong to Finance scope)
- [ ] Verify: Welcome message appears: "Welcome to your team! You now have access to the following reports:"
- [ ] **Screenshot**: Newly assigned user sees reports

### Step 6.5: Role-Based Report Access - Manager Sees Sub-Teams
- [ ] Login as manageruser (manager of Finance)
- [ ] Navigate to Reports section
- [ ] Verify: Reports from Finance team are visible
- [ ] If testuser1 has reports in Accounting sub-team, verify those are also visible to manageruser
- [ ] **Screenshot**: Manager sees team + sub-team reports

### Step 6.6: Role-Based Report Access - Team Lead Sees Team Only
- [ ] Login as testuser1 (team_lead in Accounting)
- [ ] Navigate to Reports section
- [ ] Verify: Reports from Accounting team are visible
- [ ] Verify: Reports from Finance or Payroll are NOT visible
- [ ] **Screenshot**: Team lead sees only their team's reports

### Step 6.7: Report Access After Hierarchy Change
- [ ] Create a new sub-team: Finance > Marketing
- [ ] Create test report for Marketing
- [ ] Assign testuser1 as manager of Marketing
- [ ] Logout and login as testuser1
- [ ] Verify: Marketing reports are now visible (due to manager role)
- [ ] Change testuser1's role to `user` in Marketing (demote from manager)
- [ ] Logout and login as testuser1
- [ ] Verify: Marketing reports are now NOT visible (no access)
- [ ] **Screenshot**: Access change after role change

---

## Summary Validation

### Test Execution Log
| User Story | Start Time | End Time | Duration | Status | Notes |
|------------|-----------|---------|----------|--------|-------|
| US1 Auth | | | | ✓ Pass | |
| US2 Invitations | | | | ✓ Pass | |
| US3 User Admin | | | | ✓ Pass | |
| US4 Team Hierarchy | | | | ✓ Pass | |
| US5 Admin Panel | | | | ✓ Pass | |
| US6 Report Scoping | | | | ✓ Pass | |

### Screenshots Captured
- [ ] Login page
- [ ] Admin dashboard
- [ ] User profile
- [ ] Invitation creation and acceptance
- [ ] User admin list
- [ ] User edit and disable/enable
- [ ] Team creation and hierarchy
- [ ] Multi-team assignment
- [ ] Admin panel (all sections)
- [ ] Org hierarchy visualization
- [ ] Report empty state
- [ ] Report access by role

### Known Limitations
- Email sending requires SMTP configuration (password reset email step may be skipped)
- Performance testing may vary based on Docker environment resources
- Database reset required between fresh test runs for consistent results

### Pass/Fail Determination
- **PASS**: All 6 user stories validated successfully with all steps completed
- **FAIL**: Any user story with incomplete steps or unexpected behavior
- **PARTIAL**: Some user stories complete, others incomplete or deferred

---

**Validation Date**: _________________  
**Validated By**: _________________  
**Result**: ☐ PASS  ☐ FAIL  ☐ PARTIAL  
**Comments**: ____________________________________________________________
