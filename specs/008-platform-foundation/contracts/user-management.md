# User Management Contract

## Overview

This contract defines the primary user-management flows for the multi-user foundation MVP.

## Endpoints / Actions

### Authentication

- Sign in with email and password
- Sign out
- Request password reset via email
- Reset password through a secure token
- View profile page for authenticated users

### Invitations

- Create invitation for a target email address
- List active and expired invitations
- Accept invitation to create a user account
- Reject or expire invitations after 7 days

### Administration

- List users with account status and role
- Enable or disable a user account
- Rename a user account
- Reset a user password
- Delete a user account

## Validation Rules

- Invitations must be rejected if expired or already accepted.
- Disabled users must not be allowed to sign in.
- Password reset and invitation acceptance must be secured with tokens or signed links.
- Administrative actions must be restricted to users with administrator privileges.
