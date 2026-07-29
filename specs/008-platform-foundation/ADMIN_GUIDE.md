# Admin Onboarding Guide: Platform Foundation (T086)

**Target Audience**: Platform administrators responsible for organizational setup and user management  
**Duration**: 30-45 minutes for initial setup  
**Prerequisite**: Django admin with superuser credentials

---

## Table of Contents

1. [Initial Admin Setup](#initial-admin-setup)
2. [Creating Organizational Structure](#creating-organizational-structure)
3. [Managing Users](#managing-users)
4. [Assigning Teams and Roles](#assigning-teams-and-roles)
5. [Access Control Configuration](#access-control-configuration)
6. [Monitoring and Audit](#monitoring-and-audit)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Initial Admin Setup

### Creating Your First Admin Account

The superuser account is created during Django initialization:

```bash
# Via Django command (one-time)
python manage.py createsuperuser
# Prompts for: username, email, password

# Or in Docker:
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py createsuperuser
```

**Tips**:
- Use a descriptive email (`admin@your-organization.com`)
- Store credentials securely (password manager recommended)
- This account is not subject to team restrictions (sees all data)

### First Login

1. Navigate to http://localhost:8000/login/
2. Enter superuser credentials
3. You'll see the dashboard with "Admin Panel" link in top menu
4. Click "Admin Panel" to access the consolidated admin interface

**What You See**:
- Dashboard with organization statistics
- Quick access to Users, Teams, Roles, and Hierarchy sections
- Recent activity log

---

## Creating Organizational Structure

### Step 1: Plan Your Organization Hierarchy

Before creating teams, document your structure:

```
Example Structure:
├── Operations (root team)
│   ├── Finance
│   │   ├── Accounting
│   │   └── Payroll
│   ├── HR
│   │   └── Recruitment
│   └── IT
└── Sales (root team)
    ├── APAC
    ├── EMEA
    └── Americas
```

**Planning Tips**:
- Start with 2-3 root teams (avoid too many top-level teams)
- Sub-teams should be 2-3 levels deep (deeper hierarchies are harder to navigate)
- Align with actual reporting structure
- Plan for future growth (teams can be easily restructured later)

### Step 2: Create Root Teams

1. Navigate to Admin Panel > Teams > Teams List
2. Click "New Team" button
3. Fill in:
   - **Team Name**: `Operations` (or your root team name)
   - **Parent Team**: Leave blank (this creates a root team)
   - **Manager**: Select from existing users (preferably a manager user)
   - **Team Lead**: Optional (usually same as Manager for root teams)
4. Click "Create Team"

**Creating Managers**:
- If no suitable manager user exists yet, create them first via Users section
- Send invitation, have them accept and create account
- Then return to team creation and assign them as manager

### Step 3: Create Sub-Teams

1. In Admin Panel > Teams, click on the root team (e.g., "Operations")
2. Click "New Sub-Team" button
3. Fill in:
   - **Team Name**: `Finance`
   - **Parent Team**: Automatically set to "Operations"
   - **Manager**: Select manager for this sub-team
   - **Team Lead**: Optional team lead
4. Click "Create Team"

**Repeat** for each sub-team under the parent team.

### Step 4: Create Nested Sub-Teams (Level 3+)

1. In Admin Panel > Teams, click on a Level 2 team (e.g., "Finance")
2. Click "New Sub-Team"
3. Fill in:
   - **Team Name**: `Accounting`
   - **Parent Team**: Automatically set to "Finance"
   - **Manager**: Select manager
4. Click "Create Team"

### Step 5: Verify Hierarchy

1. Navigate to Admin Panel > Hierarchy
2. Verify the organizational chart displays correctly:
   - Tree structure shows all levels
   - Manager names displayed with each team
   - Expansion/collapse working for each node
3. If structure is incorrect:
   - Click on a team to edit
   - Change parent_team to correct parent
   - Save changes

---

## Managing Users

### Creating User Invitations

**Method 1: Via Admin Panel (Recommended)**

1. Navigate to Admin Panel > Users
2. Click "Invite User" button
3. Fill in:
   - **Email**: `newuser@organization.com`
   - **First Name**: `John`
   - **Last Name**: `Doe`
4. Click "Send Invitation"
5. System sends invitation email with 7-day expiry
6. User receives link to accept invitation and create password

**Method 2: Via User Admin Page**

1. Navigate to Admin Panel > Users > User Management
2. Find "Invite New User" section
3. Follow same steps as Method 1

### Accepting Invitations (User Flow)

User receives email with invitation link:
```
Click here to create your account: 
http://your-domain.com/invitations/[TOKEN]/accept/
```

User clicks link and:
1. Enters desired password
2. Confirms password
3. Clicks "Create Account"
4. Receives confirmation message
5. Can now login with credentials

**Common Issues**:
- Invitation expired (7 days): Admin can resend from Users panel
- Email not received: Check spam folder or resend invitation

### User Account Actions

In Admin Panel > Users, for each user you can:

**Disable User**:
- Click "Disable" button
- User can no longer login
- Existing sessions expire
- Use for temporary access suspension

**Re-enable User**:
- Click "Enable" button
- User can login again immediately
- Previous team assignments restored

**Rename User**:
- Click "Edit" on user
- Update First Name or Last Name
- Save changes
- Changes appear in admin panel and user profile

**Reset Password**:
- Click "Reset Password" button
- System generates password reset link
- Email sent to user with link
- User clicks link to set new password
- Useful if user forgets password

**Delete User**:
- Click "Delete" button
- **WARNING**: Irreversible!
- User account permanently removed
- Team assignments deleted
- All user data removed (except audit logs)
- **Best Practice**: Use "Disable" instead of delete for audit trail

---

## Assigning Teams and Roles

### User Team Assignment Workflow

#### Step 1: Identify User to Assign
- Navigate to Admin Panel > Users
- Find the user in the list

#### Step 2: Assign to Team
- Click user name to open user detail
- Find "Team Assignments" section
- Click "Assign Team"
- Select team from dropdown (e.g., "Finance")
- Select role in that team:
  - `user`: Regular team member (can see team reports)
  - `team_lead`: Can see team reports and manage team members
  - `manager`: Can see team + all sub-team reports, manage assignments
  - `admin`: Full admin access (rare; use sparingly)
- Click "Assign"
- Verification message appears: "User assigned to Finance as user"

#### Step 3: Verify Assignment
- User detail now shows "Finance" in team assignments
- Multi-team assignments show with each role:
  - Finance: user
  - Accounting: team_lead

### Multi-Team Assignment (Matrix Organization)

Some users may have roles in multiple teams:

**Example - John (Product Manager)**:
- Manager in "Product" team
- Team Lead in "Engineering" team
- User in "Operations" team

**To Create This**:
1. Assign John to Product with role `manager`
2. Assign John to Engineering with role `team_lead`
3. Assign John to Operations with role `user`
4. John's access:
   - Sees Product team + all sub-teams (as manager)
   - Sees Engineering team + sub-teams (as team_lead)
   - Sees Operations reports only (as regular user)

**Admin Panel - Roles Section**:
- Shows all role assignments in matrix:
  - User | Team | Role | Assigned By | Assigned On
  - john | Product | manager | admin | 2026-07-29
  - john | Engineering | team_lead | admin | 2026-07-29
  - john | Operations | user | admin | 2026-07-29

### Removing Team Assignments

To remove a user from a team:
1. Navigate to Admin Panel > Users > [User Name]
2. Find "Team Assignments" section
3. Locate the assignment to remove
4. Click "Remove" or X button
5. Confirm: "Remove user from this team?"
6. Click "Confirm"
7. Assignment deleted; user loses access to that team's reports

---

## Access Control Configuration

### Role-Based Access Levels

**Admin / Superuser**:
- Access: All features, all data, all teams
- Scope: Entire organization
- Permissions: Create/edit/delete users, teams, manage all roles
- Dashboard: Full statistics and audit logs

**Manager** (in specific team):
- Access: Their team + all sub-teams
- Scope: Team hierarchy below their assignment
- Permissions: Can see all reports in scope, manage team members, create sub-teams
- Dashboard: Statistics for their managed teams only

**Team Lead** (in specific team):
- Access: Their team + direct sub-teams
- Scope: Limited to assigned team and immediate children
- Permissions: Can view team, see team members, limited user management
- Dashboard: Team-specific information only

**User** (regular team member):
- Access: Assigned team only
- Scope: Single team
- Permissions: Can see team reports only
- Dashboard: Personal report view

**Unassigned User** (no team):
- Access: Home page with empty state message
- Scope: None
- Permissions: Can request team assignment
- Dashboard: "Please contact administrator"

### Report Visibility Logic

Report access is determined by:

1. **User Role in Team**:
   - `admin`: See all reports in system
   - `manager`: See team + sub-team reports (recursive)
   - `team_lead`: See team + direct sub-team reports
   - `user`: See team reports only
   - `(unassigned)`: See no reports (empty state)

2. **Team Hierarchy**:
   ```
   Reports in:
   ├── Operations (level 0)
   ├── Finance (level 1, parent: Operations)
   │   ├── Accounting (level 2)
   │   └── Payroll (level 2)
   └── Sales (level 0)
       └── APAC (level 1)
   
   Alice (manager in Operations):
   - Sees: All reports (Operations + Finance + Accounting + Payroll + Sales + APAC)
   
   Bob (manager in Finance):
   - Sees: Finance + Accounting + Payroll reports only
   
   Carol (team_lead in Accounting):
   - Sees: Accounting reports only
   ```

### Configuring Access After Hierarchy Changes

After modifying team hierarchy (moving teams, changing managers):

1. **Change Takes Effect Immediately**:
   - Users' report access recalculated in real-time
   - No cache refresh needed
   - Audit log recorded

2. **Verify Access**:
   - Login as affected user
   - Navigate to Reports section
   - Verify reports show/hide as expected
   - Check admin panel for new hierarchy

3. **Communicate Changes**:
   - Send email to affected users explaining changes
   - Include deadline for any action needed
   - Provide troubleshooting contact

---

## Monitoring and Audit

### Admin Panel Dashboard

Displays key metrics:
- **Total Users**: Count of all user accounts
- **Total Teams**: Count of all teams in hierarchy
- **Total Team Assignments**: User-team relationships
- **Recent Users**: Newly created accounts
- **Recent Assignments**: Latest user-team assignments
- **Login Activity**: Last login timestamps

### Audit Logging

All administrative actions are logged:
```
[2026-07-29 14:23:45] admin created user: john.doe@org.com
[2026-07-29 14:24:10] admin created team: Finance (parent: Operations)
[2026-07-29 14:25:33] admin assigned john.doe to Finance as user
[2026-07-29 14:26:00] admin updated Finance manager: alice -> bob
```

**Accessing Audit Logs**:
1. Navigate to Admin Panel > Activity Log
2. Filter by:
   - Date range
   - User (who performed action)
   - Action type (create, update, delete)
   - Resource type (user, team, assignment)
3. View detailed changes for each log entry

### Monitoring User Access

To see which users have access to which teams:

1. Navigate to Admin Panel > Roles
2. View matrix of assignments:
   - User | Role | Team | Assigned Date | Assigned By
3. Click on user to see all their assignments
4. Click on team to see all users in that team

---

## Troubleshooting

### User Reports "No Reports Visible"

**Symptoms**: User says they can't see any reports  
**Possible Causes**:
1. User not assigned to any team
2. Team has no reports
3. User's role doesn't grant access

**Solution**:
```
1. Check user's team assignments:
   - Admin Panel > Users > [User Name]
   - Look for "Team Assignments" section
   
2. If no assignments:
   - Assign user to appropriate team
   - Confirm role is not (unassigned/restricted)
   
3. If assignments exist:
   - Check reports exist in user's team
   - Verify user's role (should not be blocked)
   - Verify hierarchy (e.g., if manager, sub-teams have reports)
   
4. Clear cache:
   - Admin Panel > Maintenance > Clear Cache
   - Have user logout/login
```

### User Can't Login

**Symptoms**: "Invalid credentials" error  
**Possible Causes**:
1. User account disabled
2. User invitation not accepted yet
3. Wrong password
4. User account deleted

**Solution**:
```
1. Check user status:
   - Admin Panel > Users > [User Name]
   - Verify account is "Enabled"
   
2. If disabled:
   - Click "Enable" to restore access
   
3. If user never accepted invitation:
   - Resend invitation
   - Provide new acceptance link
   
4. If user forgot password:
   - Use "Reset Password" button
   - Send password reset link to user
   
5. If user account deleted:
   - Recreate user (recreate invitation)
```

### Team Hierarchy Issues

**Problem**: Sub-team not appearing under parent  
**Solution**:
```
1. Edit sub-team:
   - Admin Panel > Teams > [Sub Team Name] > Edit
   
2. Verify parent_team:
   - Confirm it's set to correct parent
   - Select correct parent if wrong
   
3. Save changes
4. Refresh page
5. Verify hierarchy updated
```

**Problem**: Can't delete team  
**Solution**:
```
If error "Cannot delete team with sub-teams":
1. Move all sub-teams to new parent first:
   - Edit sub-team
   - Change parent_team to new parent
   - Save
   
2. OR keep sub-teams and update parent:
   - Don't delete this team
   - Update its parent instead
   
If error "Cannot delete team with users":
1. Remove all users from team:
   - Admin Panel > Teams > [Team Name]
   - Find "Team Members" section
   - Click "Remove" for each member
   
2. Then delete team
```

### Manager Can't Access Reports

**Symptoms**: Manager can see team in admin panel but reports are missing  
**Possible Causes**:
1. Reports not assigned to team
2. Reports not yet created
3. Reports in different team
4. Caching issue

**Solution**:
```
1. Verify reports exist:
   - Check actual Reports section
   - Confirm reports are created
   
2. Verify report-team association:
   - Reports section should show team assignment
   - If team mismatch, move report
   
3. Clear manager's cache:
   - Admin Panel > Users > [Manager] > Clear Cache
   - Manager logs out/back in
   
4. Verify hierarchy:
   - Admin Panel > Hierarchy
   - Confirm team is shown under manager's scope
```

### Performance Issues

**Problem**: Admin panel loads slowly with many teams/users  
**Solution**:
```
1. Archive old teams:
   - Move inactive teams to separate "Archive" root team
   - Reduces active hierarchy size
   
2. Optimize database:
   - Run: python manage.py optimize
   - Rebuilds indexes
   
3. Clear caches:
   - Admin Panel > Maintenance > Clear All Caches
   
4. Check server resources:
   - Verify Docker container has enough memory (4GB+ recommended)
   - Check database performance
```

---

## Best Practices

### User Management

1. **Invite First, Assign Second**:
   - Create user via invitation
   - Have user accept and create account
   - Then assign to teams
   - Avoids confusion with credentials

2. **Use Email-Based Identification**:
   - Invite using actual user email
   - Matches corporate directory
   - Easy to identify users
   - Prevents duplicates

3. **Regular Reviews**:
   - Monthly: Review disabled user list (clean up old accounts)
   - Quarterly: Audit team assignments (verify they match org)
   - Annually: Review role distribution (ensure appropriate access)

4. **Document Org Structure**:
   - Maintain org chart diagram (external to app)
   - Document team managers and leads
   - Keep decision log for hierarchy changes
   - Use for onboarding new admins

### Team Management

1. **Hierarchical Depth**:
   - Keep 3-4 levels maximum (easier to navigate)
   - Root level: 2-5 teams (not too many)
   - Avoid deeply nested structures

2. **Team Naming Convention**:
   - Use business unit names (Finance, Sales, HR)
   - Include region if applicable (APAC, EMEA)
   - Avoid generic names (Team A, Group B)
   - Use consistent case (Title Case recommended)

3. **Manager Assignment**:
   - Ensure every team has a manager
   - Manager should be active user
   - Document manager responsibilities
   - Have backup manager for critical teams

4. **Regular Audits**:
   - Quarterly: Check for orphaned teams (no users)
   - Quarterly: Verify managers still active
   - Annual: Review if structure still matches org

### Access Control

1. **Principle of Least Privilege**:
   - Don't over-assign admin roles
   - Use manager role for team oversight (not admin)
   - Regular audit of role distribution
   - Document role requirements

2. **Hierarchy-Based Access**:
   - Reports inherit team visibility
   - Managers see reports through hierarchy
   - Don't need to manually assign every report
   - Automatic propagation when sub-teams created

3. **Testing Access**:
   - Create test user accounts
   - Verify each role sees correct data
   - Test edge cases (deeply nested teams)
   - Document expected access levels

### Security

1. **Admin Credentials**:
   - Rotate admin passwords quarterly
   - Use strong passwords (16+ characters, mixed case, numbers, symbols)
   - Don't share admin credentials
   - Use single admin account per person

2. **Audit Logging**:
   - Review activity log monthly
   - Investigate unusual patterns
   - Archive logs for compliance
   - Track all user/team changes

3. **Session Management**:
   - Automatic logout after inactivity (30 minutes)
   - Users can manually logout
   - Sessions don't persist across browser close (recommended)
   - Monitor concurrent session count

---

## Getting Help

### Support Resources

- **Email**: admin-support@enerlytix.local
- **Internal Wiki**: [Link to team documentation]
- **Slack Channel**: #platform-foundation-support
- **Issue Tracker**: [Link to bug reports]

### Common Questions

**Q: How many users can the system handle?**  
A: Tested with 100+ users; performance remains good. With 1000+ users, consider database optimization.

**Q: Can I move a team to a different parent?**  
A: Yes, edit the team and change parent_team. All sub-teams move automatically. Reports access updates immediately.

**Q: What happens when I delete a team?**  
A: Team is permanently deleted. Sub-teams become orphaned (must be reassigned to new parent). Users lose access to reports.

**Q: Can users have roles in teams they're not assigned to?**  
A: No. Role assignment requires team assignment. Assign to team first, then assign role.

**Q: How do I prevent a manager from seeing certain reports?**  
A: Move those reports to a team outside the manager's hierarchy. Manager only sees teams below their assigned team.

---

## Change Log

| Date | Change | Administrator |
|------|--------|-----------------|
| 2026-07-29 | Initial guide creation | Platform Team |
| | | |

