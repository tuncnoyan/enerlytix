# Data Model: Invitation-Only User Authentication

## Invitation

Represents a single invitation to join Enerlytix.

### Fields

- `id`: UUID primary key used in the invitation accept link.
- `email`: Unique invited email address.
- `invited_by`: Foreign key to the user who created the invitation.
- `status`: One of `pending`, `accepted`, or `revoked`.
- `accepted_at`: Timestamp set when the invitation is used successfully.
- `revoked_at`: Timestamp set when an admin revokes the invitation.
- `created_at`: Timestamp for initial creation.
- `updated_at`: Timestamp for the latest status change.

### Relationships

- Belongs to one authenticated inviter.
- Resolves to one account creation event when accepted.

### Validation Rules

- Email must be unique across invitations.
- Pending invitations can be reused for copy/resend behavior.
- Accepted invitations block duplicate creation attempts for the same email.
- Revoked invitations are terminal and cannot be accepted.
- Invitation links are valid only when the status is `pending`.

### State Transitions

- `pending -> accepted` when the invited user completes sign-up successfully.
- `pending -> revoked` when an admin revokes the invitation.
- `accepted` and `revoked` are terminal states.

## User Account

Represents the authenticated account created from an accepted invitation.

### Notes

- Created through the invitation accept flow, not direct self-registration.
- Password reset updates the existing user account without changing invitation state.

## Password Reset Request

Represents the logical reset flow initiated by an existing user.

### Notes

- This is a transient token-based flow, not a new persistent table.
- The reset link contains a secure token and user identifier.
- The request is considered complete when the password is updated successfully.

## Email Template

Represents the branded invitation or password-reset message.

### Required Template Inputs

- `subject`
- `recipient_email`
- `action_url`
- `brand_name`
- `support_reply_to` when configured

### Template Variants

- Invitation email text and HTML variants.
- Password reset email text and HTML variants.

## Logout Confirmation Modal

Represents the confirmation UI that appears before logout completes.

### Notes

- No persistent data is stored.
- The modal must support confirm and cancel actions.
- Cancel leaves the current session active.