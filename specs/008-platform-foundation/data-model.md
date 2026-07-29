# Data Model: Platform Foundation

## Entities

### UserAccount

Represents a person who can authenticate to Enerlytix.

- id: unique user identifier
- username: login identifier used by Django auth
- email: email address used for password reset and invitations
- first_name / last_name: display name components
- is_active: whether the account can sign in
- roles: set of roles assigned to the user (admin, manager, team_lead, user can coexist)
- date_joined: when the account was created
- last_login: most recent successful sign-in

**Note**: The role model supports multiple roles per user. A user can be admin AND manager AND team_lead simultaneously.

### Team

Represents a hierarchical group within the organisation.

- id: unique team identifier
- name: display name for the team
- parent_team: optional reference to parent team for hierarchical structure (null for root teams)
- manager: reference to the user assigned as team manager (can be null if no manager assigned yet)
- team_lead: optional reference to user assigned as team lead within this team
- created_at: when the team was created
- updated_at: last modification timestamp

**Hierarchy**: A team can have a parent team, creating a tree structure. Report access for managers includes all sub-teams within their hierarchy.

### UserTeamAssignment

Represents the assignment of a user to a team with their effective role within that team.

- id: unique assignment identifier
- user: reference to the user account
- team: reference to the team
- assigned_at: when the assignment was made
- assigned_by: administrator who performed the assignment

**Note**: A user can be assigned to multiple teams. Their role within each team is determined by their overall user roles (admin, manager, team_lead, user).

### Invitation

Represents a time-limited permission allowing a new user to create an account.

- id: unique invitation identifier
- email: target email address for the invitation
- created_by: administrator who issued the invitation
- created_at: date and time of issuance
- expires_at: expiry date and time, fixed at 7 days after issuance
- accepted_at: date and time of acceptance, if any
- status: pending, accepted, expired, or revoked
- initial_team: optional reference to team the user should be assigned to upon acceptance

### RoleAssignment

Represents the access roles granted to a user (multi-valued).

- user_id: reference to the user account
- role_name: one of admin, manager, team_lead, or user
- assigned_at: assignment timestamp
- assigned_by: administrator who performed the assignment

**Note**: Multiple rows can exist for the same user with different role_names, representing overlapping roles.

## Relationships

- One user can belong to multiple teams via UserTeamAssignment.
- One team can have one manager (user) and optionally one team lead (user).
- One team can have one parent team (optional, for hierarchy).
- One user can receive many invitations, but only one active invitation should be valid per email at a time.
- One invitation can be accepted to create one user account.
- One user can hold multiple roles simultaneously via RoleAssignment.
- User account sign-in permission is controlled by the is_active flag.

## Access Scoping

### Report Access by Role and Team

1. **User (no team assignment)**: Empty state; no reports visible until assigned to a team.
2. **User (with team assignment)**: Can access reports from their assigned team and all sub-teams within it.
3. **Team Lead**: Can access reports from their team and all sub-teams within the team they lead.
4. **Manager**: Can access all reports from teams they manage and all sub-teams recursively.
5. **Admin**: Can access all reports across the organisation.

### Admin Panel Visibility and Access

- Admin panel link visible in top-right menu: only for users with admin role.
- Admin panel URL protected: redirect non-admins to home or profile.
- Admin panel consolidates: user management, team management, organisational hierarchy view, and role assignments.

