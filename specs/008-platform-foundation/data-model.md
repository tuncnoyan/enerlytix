# Data Model: Platform Foundation (T087 - Finalized)

**Status**: Schema finalized and implemented  
**Database**: PostgreSQL (Django ORM)  
**Migrations**: Versions 0001-0015 completed  
**Last Updated**: 2026-07-29

## Entities

### UserAccount (Django User Model)

Represents a person who can authenticate to Enerlytix.

**Fields**:
- `id` (PK): Unique user identifier (auto-increment)
- `username` (CharField, unique): Login identifier for authentication
- `email` (EmailField, unique): Email address for password reset and invitations
- `first_name` (CharField): User's first name
- `last_name` (CharField): User's last name
- `password` (CharField): Hashed password (Django auth)
- `is_active` (BooleanField): Whether account can sign in (default: True)
- `is_staff` (BooleanField): Whether user can access admin site (default: False)
- `is_superuser` (BooleanField): Whether user is superuser (default: False)
- `date_joined` (DateTimeField): Account creation timestamp
- `last_login` (DateTimeField, nullable): Most recent login timestamp
- `groups` (M2M to Group): Django auth groups (not heavily used; see RoleAssignment)

**Constraints**:
- `username`: Unique, max 150 characters, alphanumeric + @/./+/-/_
- `email`: Unique, max 254 characters
- `is_active=False` blocks all login attempts

**Indexes**:
- PK on `id`
- Unique on `email`
- Unique on `username`

**Helper Methods**:
- `is_admin()`: Returns `is_superuser or is_staff`
- `get_roles()`: Get all RoleAssignment entries for this user
- `get_teams()`: Get all UserTeamAssignment entries for this user

### Team

Represents a hierarchical group within the organisation.

**Fields**:
- `id` (PK): Unique team identifier (auto-increment)
- `name` (CharField, unique=False): Team display name, max 255 characters
- `parent_team` (ForeignKey to Team, nullable): Reference to parent team for hierarchy (null = root team)
- `manager` (ForeignKey to User, nullable): User assigned as team manager
- `team_lead` (ForeignKey to User, nullable): User assigned as team lead
- `created_at` (DateTimeField): Team creation timestamp (auto_now_add)
- `updated_at` (DateTimeField): Last modification timestamp (auto_now)

**Constraints**:
- `parent_team`: ON_DELETE=models.PROTECT (prevents deletion of teams with sub-teams)
- `manager`, `team_lead`: ON_DELETE=models.SET_NULL (allows removal of users)
- `name`: Max 255 characters, not null

**Indexes**:
- PK on `id`
- FK on `parent_team`
- FK on `manager`
- FK on `team_lead`

**Helper Methods**:
- `get_parent_teams()`: Traverse up to root; returns list of parent teams
- `get_sub_teams()`: Returns direct sub-teams (one level down)
- `get_all_sub_teams()`: Recursively returns all descendants
- `get_team_members()`: Returns all users assigned to this team
- `get_manager()`: Returns the manager user object

### UserTeamAssignment

Represents the assignment of a user to a team (tracks membership and audit trail).

**Fields**:
- `id` (PK): Unique assignment identifier (auto-increment)
- `user` (ForeignKey to User): Reference to assigned user
- `team` (ForeignKey to Team): Reference to assigned team
- `assigned_at` (DateTimeField): Assignment timestamp (auto_now_add)
- `assigned_by` (ForeignKey to User, nullable): Administrator who performed the assignment

**Constraints**:
- `unique_together` = [('user', 'team')]: Prevents duplicate user-team assignments
- `user`: ON_DELETE=models.CASCADE (deleting user removes all assignments)
- `team`: ON_DELETE=models.CASCADE (deleting team removes all assignments)
- `assigned_by`: ON_DELETE=models.SET_NULL (preserves assignment history even if admin deleted)

**Indexes**:
- PK on `id`
- Unique index on `(user, team)`
- FK on `user`
- FK on `team`
- FK on `assigned_by`

**Helper Methods**:
- `get_report_scope()`: Returns QuerySet of reports accessible to this assignment based on user role in team
- `is_team_member()`: Boolean check if user is member of team

### Invitation

Represents a time-limited permission allowing a new user to create an account.

**Fields**:
- `id` (PK): Unique invitation identifier (auto-increment)
- `email` (EmailField): Target email address for invitation
- `token` (CharField, unique): URL-safe random token for invitation link
- `created_by` (ForeignKey to User): Administrator who issued the invitation
- `created_at` (DateTimeField): Issuance timestamp (auto_now_add)
- `expires_at` (DateTimeField): Expiry date/time (fixed at created_at + 7 days)
- `accepted_at` (DateTimeField, nullable): Acceptance timestamp (set when invitation used)
- `status` (CharField): One of 'pending', 'accepted', 'expired', 'revoked'
- `initial_team` (ForeignKey to Team, nullable): Optional auto-assign team upon acceptance

**Constraints**:
- `email`: Max 254 characters, not null
- `token`: Unique, auto-generated, not null
- `status`: Choices = ['pending', 'accepted', 'expired', 'revoked']
- `created_by`: ON_DELETE=models.SET_NULL (preserves invitation history)
- `initial_team`: ON_DELETE=models.SET_NULL (team can be deleted, invitation remains)

**Indexes**:
- PK on `id`
- Unique on `token`
- Index on `email`
- Index on `status`
- FK on `created_by`
- FK on `initial_team`

**Helper Methods**:
- `is_valid()`: Checks if pending and not expired
- `accept(user)`: Mark as accepted, set accepted_at timestamp, link to created user
- `is_expired()`: Checks if created_at + 7 days < now()

### RoleAssignment

Represents the access roles granted to a user (supports multiple, overlapping roles per user).

**Fields**:
- `id` (PK): Unique assignment identifier (auto-increment)
- `user` (ForeignKey to User): Reference to user being assigned a role
- `role_name` (CharField): One of 'admin', 'manager', 'team_lead', 'user'
- `assigned_at` (DateTimeField): Assignment timestamp (auto_now_add)
- `assigned_by` (ForeignKey to User, nullable): Administrator who performed the assignment

**Constraints**:
- `unique_together` = [('user', 'role_name')]: Prevents duplicate role assignments
- `role_name`: Choices = ['admin', 'manager', 'team_lead', 'user']
- `user`: ON_DELETE=models.CASCADE (deleting user removes all role assignments)
- `assigned_by`: ON_DELETE=models.SET_NULL (preserves audit history)

**Indexes**:
- PK on `id`
- Unique index on `(user, role_name)`
- FK on `user`
- Index on `role_name`
- FK on `assigned_by`

**Helper Methods**:
- `get_user_roles(user)`: Returns list of all role_names for a user
- `has_role(user, role_name)`: Boolean check if user has specific role
- `is_admin_or_manager(user)`: Boolean check if user has admin or manager role

## Relationships

### One-to-Many
- One User can have many UserTeamAssignments (assigned to multiple teams)
- One Team can have many UserTeamAssignments (multiple members)
- One Team can have many Invitations (invitations for team onboarding)
- One User can have many Invitations created by them (admins create invitations)
- One User can have many RoleAssignments (multiple roles per user)

### Self-Referential (Hierarchical)
- Team → Team via `parent_team` (creates tree structure, prevents cycles)

### Foreign Key Relationships
- `Team.manager` → `User` (nullable; team can have no manager)
- `Team.team_lead` → `User` (nullable; team can have no team lead)
- `UserTeamAssignment.user` → `User` (cascade delete)
- `UserTeamAssignment.team` → `Team` (cascade delete)
- `UserTeamAssignment.assigned_by` → `User` (set null on delete)
- `Invitation.created_by` → `User` (set null on delete)
- `Invitation.initial_team` → `Team` (set null on delete)
- `RoleAssignment.user` → `User` (cascade delete)
- `RoleAssignment.assigned_by` → `User` (set null on delete)

## Access Scoping

### Report Access by Role and Team Assignment

**Access Matrix**:
| User State | Role | Team Assignment | Reports Visible | Notes |
|---|---|---|---|---|
| New user | `user` | None | None | Empty state: "No team assigned" |
| Team member | `user` | Team A | Team A reports | Single team only |
| Team member+ | `user` | Team A, Team B | Team A + Team B reports | Multi-team assignment |
| Team lead | `team_lead` | Team A | Team A + sub-teams | Limited to assigned team scope |
| Manager | `manager` | Team A | Team A + all sub-teams recursively | Full hierarchy access |
| Admin | `admin` | Any | All reports | Full organization access |
| Superuser | `admin` | Any | All reports + admin functions | Django superuser override |

**Key Rules**:
1. Access requires `is_active=True` on User
2. Access requires `UserTeamAssignment` (team membership)
3. `RoleAssignment` determines visibility scope within team
4. Managers see team + all descendants (recursive)
5. Team leads see team + direct children only
6. Regular users see assigned team only
7. Admins bypass all restrictions
8. Role assignments are independent of team assignments

### Admin Panel Access Control

- **Who can access**: Only users with `is_staff=True` or `is_superuser=True` or admin role
- **Protected URL**: `/admin-panel/` - 302 redirect if not admin
- **Sections visible**: All users, teams, roles, hierarchy (same for all admins)
- **Actions allowed**: Create/update/delete users, teams, assignments, invitations
- **Audit trail**: All admin actions logged to admin activity log

---

## Database Migrations

### Migration History

| Migration | Description | Status | Date |
|---|---|---|---|
| 0001_initial | Django user model + sitesync app structure | ✅ | 2026-07-29 |
| 0002_site_supply | Site, Supply models for report framework | ✅ | 2026-07-29 |
| 0013_invitation | Invitation model with 7-day expiry | ✅ | 2026-07-29 |
| 0014_team | Team model with parent_team hierarchy | ✅ | 2026-07-29 |
| 0015_userteamassignment | UserTeamAssignment + RoleAssignment models | ✅ | 2026-07-29 |

### Apply Migrations

```bash
# Local development (SQLite)
python manage.py migrate

# Docker (PostgreSQL)
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py migrate
```

### Rollback Instructions (if needed)

```bash
# Rollback to specific migration
python manage.py migrate sitesync 0014
# Then forward again
python manage.py migrate sitesync
```

---

## Schema Finalization Checklist

- [x] User model finalized (Django User, no customization needed)
- [x] Team model with hierarchy implemented (parent_team FK, constraints)
- [x] UserTeamAssignment model with unique constraint (user, team)
- [x] RoleAssignment model with multi-role support (user, role_name)
- [x] Invitation model with 7-day expiry and token
- [x] All foreign key relationships defined (cascade/set_null rules)
- [x] All unique constraints applied
- [x] All indexes created for performance
- [x] Migrations generated and tested
- [x] Helper methods implemented on models
- [x] Access control logic finalized
- [x] Audit trail structure (assigned_by fields)
- [x] Documentation complete

**Schema is production-ready for Phase 7 deployment.**

