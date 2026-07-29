# Data Model: Platform Foundation

## Entities

### UserAccount

Represents a person who can authenticate to Enerlytix.

- id: unique user identifier
- username: login identifier used by Django auth
- email: email address used for password reset and invitations
- first_name / last_name: display name components
- is_active: whether the account can sign in
- is_staff: whether the user can access Django admin or admin-oriented management views
- is_superuser: whether the user has full administrative control
- date_joined: when the account was created
- last_login: most recent successful sign-in

### Invitation

Represents a time-limited permission allowing a new user to create an account.

- id: unique invitation identifier
- email: target email address for the invitation
- created_by: administrator who issued the invitation
- created_at: date and time of issuance
- expires_at: expiry date and time, fixed at 7 days after issuance
- accepted_at: date and time of acceptance, if any
- status: pending, accepted, expired, or revoked
- role: assigned role for the invited user (administrator or standard user)

### RoleAssignment

Represents the access role granted to a user.

- user_id: reference to the user account
- role_name: administrator or standard user
- assigned_at: assignment timestamp
- assigned_by: administrator who performed the assignment

### AccountStatus

Represents the effective sign-in state of a user account.

- user_id: reference to the user account
- is_active: true if the user may sign in
- reason: optional explanation for disablement or lockout

## Relationships

- One user can receive many invitations, but only one active invitation should be valid per email at a time.
- One invitation can be accepted to create one user account.
- One user has one effective role assignment for the initial MVP.
- User account state controls whether the account can sign in.
