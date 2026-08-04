# Feature Specification: Invitation-Only User Authentication

**Feature Branch**: `[013-invitation-auth-flow]`

**Created**: 2026-08-04

**Status**: Draft

**Input**: User description: "I want to finalise all essential features of Enerlytix before deploying it on Railway. Currently, all functions have been implemented. However, basic user authentication features are still missing. Users should only be added with invitations. However, the email integration hasn't been fully integrated yet. Because of that, the invitation link should be visible to admins on the admin panel page, so they can copy it with a button and then paste and send via email to the user. Additionally, there should be sign-up and password reset pages based on the apps page standards. Email templates should be added, too. For instance, invitation email and password reset email. Logout should also be a two step process, to avoid unintentional clicks on it."

## User Scenarios & Testing *(mandatory)*

## Clarifications

### Session 2026-08-04

- Q: How should invitation expiry work? → A: Invitations do not expire automatically; they remain valid until used or manually revoked.
- Q: How should invitation and password reset emails be handled? → A: Invitation emails may be copied manually by admins if delivery is unavailable, but password reset emails are sent automatically when the email provider is configured.
- Q: Can admins revoke pending invitations? → A: Admins can revoke a pending invitation from the admin panel, and the revoked link stops working immediately.
- Q: How should logout confirmation work? → A: Clicking logout opens an in-place confirmation modal on the current page.

### User Story 1 - Admin Manages Invitation-Only Access (Priority: P1)

An admin can add new users only through invitations, view the invitation link in the admin panel, and copy it with one action so the link can be sent manually when email delivery is not yet available.

**Why this priority**: Invitation-only access is the gate that prevents unsupported self-registration and establishes the onboarding path for every new user.

**Independent Test**: An admin creates an invitation, sees the invitation link in the admin panel, and copies it successfully without leaving the page.

**Acceptance Scenarios**:

1. **Given** an admin opens the user administration area, **When** they create a new invitation, **Then** the invitation appears in the pending list with a visible link and a copy action.
2. **Given** an invitation already exists for an email address, **When** an admin tries to invite that same email again, **Then** the system shows a warning and offers the existing pending invitation instead of failing.
3. **Given** an admin copies the invitation link, **When** they paste it into an email client, **Then** the copied value is the full usable invitation link for the intended user.
4. **Given** an admin revokes a pending invitation, **When** the invitation link is opened later, **Then** the system shows a clear message that the invitation is no longer valid.

---

### User Story 2 - Invited User Completes Sign-Up (Priority: P1)

An invited user opens a valid invitation link, completes sign-up, and becomes an active account holder without a separate self-registration path.

**Why this priority**: The platform must remain invitation-only while still allowing legitimate users to join.

**Independent Test**: A valid invitation link opens a sign-up page, the user creates credentials, and the account becomes usable after submission.

**Acceptance Scenarios**:

1. **Given** a valid invitation link, **When** the invited person opens it, **Then** they see a sign-up page that matches the rest of Enerlytix in layout and branding.
2. **Given** a valid invitation link, **When** the invited person submits their account details and password, **Then** the account is created and the invitation is marked as used.
3. **Given** an invalid or already-used invitation link, **When** a person opens it, **Then** they see a clear message explaining that the link can no longer be used.
4. **Given** a person tries to register without an invitation, **When** they reach the sign-up area, **Then** the system does not allow account creation.

---

### User Story 3 - Password Reset Support (Priority: P2)

Existing users can request a password reset and complete it through a branded reset flow and email template.

**Why this priority**: Password recovery is a basic account-access requirement and reduces support overhead before deployment.

**Independent Test**: A known user requests a reset, receives a branded reset email, and successfully sets a new password through the reset page.

**Acceptance Scenarios**:

1. **Given** an existing user cannot sign in, **When** they request a password reset, **Then** the system shows a neutral confirmation page and sends a reset email if the account exists.
2. **Given** a password reset email is opened, **When** the user follows the reset link, **Then** they can set a new password on a reset page that matches Enerlytix page standards.
3. **Given** a password reset link is expired or already used, **When** the user opens it, **Then** they see a clear message and are directed to request a new reset.

---

### User Story 4 - Logout Requires Confirmation (Priority: P2)

Users confirm logout before their session ends so accidental clicks do not immediately sign them out.

**Why this priority**: Logout is a frequent action and should be protected from accidental clicks without making the app harder to use.

**Independent Test**: A user clicks logout, sees an in-place confirmation modal, and can either confirm or cancel without side effects.

**Acceptance Scenarios**:

1. **Given** a signed-in user clicks logout, **When** the confirmation modal appears, **Then** the user must confirm before the session ends.
2. **Given** a signed-in user sees the logout confirmation modal, **When** they cancel, **Then** they remain signed in.
3. **Given** a signed-in user confirms logout in the modal, **When** the confirmation is submitted, **Then** the session ends and the user is returned to a signed-out state.

### Edge Cases

- An admin creates an invitation for an email address that already has a pending invitation: the system warns the admin and reuses the existing invitation rather than creating a duplicate.
- An admin creates an invitation for an email address that has already been accepted: the system explains that the account already exists and does not create another invitation.
- A copied invitation link is shared after the invitation is used or revoked: opening it should show a clear used-or-revoked state rather than allowing a second account to be created.
- A password reset is requested for an unknown email address: the user still sees a neutral response so account existence is not revealed.
- A logout confirmation modal is dismissed accidentally: the user remains signed in and can continue working.
- Email delivery is unavailable when an invitation is created: the admin can still copy the invitation link from the admin panel and send it manually.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST prevent direct self-registration and allow new accounts only through valid invitations.
- **FR-002**: The admin panel MUST show each pending invitation with a visible invitation link and a copy action.
- **FR-003**: The admin panel MUST warn an admin when they attempt to create an invitation for an email address that already has a pending invitation.
- **FR-004**: When an invitation already exists and is still pending, the system MUST preserve the existing invitation and make its link available for copying instead of failing.
- **FR-005**: When an invitation already exists and has been accepted, the system MUST block a duplicate invitation and show a clear explanation.
- **FR-006**: The admin panel MUST allow a pending invitation to be revoked.
- **FR-007**: A revoked invitation link MUST stop working immediately and show a clear user-facing message.
- **FR-008**: The system MUST provide a sign-up page for invited users that allows them to create credentials only when the invitation is valid.
- **FR-009**: The system MUST reject invalid, already-used, or revoked invitation links with a clear user-facing message.
- **FR-010**: The system MUST mark an invitation as used after a successful sign-up.
- **FR-011**: The system MUST provide a password reset request page for existing users.
- **FR-012**: The system MUST provide a password reset completion page reached from a valid reset link.
- **FR-013**: The system MUST use branded email templates for invitation and password reset messages.
- **FR-014**: The system MUST include a working invitation link in the invitation email template.
- **FR-015**: The system MUST include a working password reset link in the password reset email template.
- **FR-016**: The system MUST require an explicit in-place logout confirmation modal before ending a signed-in user session.
- **FR-017**: The system MUST allow a user to cancel logout and remain signed in.
- **FR-018**: All sign-up, password reset, and logout screens MUST follow the established Enerlytix page styling and branding.
- **FR-019**: The system MUST make invitation management usable even if email delivery is not available, by allowing admins to copy the invitation link from the admin panel.

### Key Entities *(include if feature involves data)*

- **Invitation**: Represents a pending, used, or revoked invitation for a single email address.
- **Invitation Link**: Represents the unique link an invited user follows to start sign-up.
- **User Account**: Represents an active authenticated user created from a valid invitation.
- **Password Reset Request**: Represents a request to recover access to an existing user account.
- **Email Template**: Represents the branded content used for invitation and password reset messages.
- **Logout Confirmation Modal**: Represents the extra confirmation required before ending a signed-in session.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of new user accounts are created only after a valid invitation link is used.
- **SC-002**: In usability testing, admins can copy an invitation link from the admin panel in under 30 seconds.
- **SC-003**: At least 95% of invited users can complete sign-up on the first attempt without support.
- **SC-004**: At least 95% of password reset requests for existing accounts produce a usable reset email within 2 minutes during normal operation.
- **SC-005**: 100% of logout attempts require explicit confirmation in a modal, and 100% of cancel actions preserve the current signed-in session.
- **SC-006**: 100% of invitation and password reset emails show the correct branded subject/content and include a working action link.
- **SC-007**: 100% of invalid, already-used, or revoked invitation links are rejected with a clear explanation instead of allowing account creation.

## Assumptions

- Users are added through invitations only; direct self-registration remains disabled.
- The admin panel is the source of truth for invitation management and link copying.
- Invitations do not expire automatically; they remain valid until used or manually revoked.
- Invitation and password reset emails should use the existing Enerlytix brand, tone, and page standards.
- Invitation links must remain copyable from the admin panel even when automatic email delivery is unavailable.
- The sign-up flow for invited users will create the account from a valid invitation link and then mark that invitation as used.
- Logout confirmation is presented as an in-place modal on the current page, and the user must explicitly confirm before the session ends.
- Railway deployment will continue to rely on the existing environment-based configuration patterns already used by Enerlytix.
- If email delivery is unavailable, administrators still need to be able to copy invitation links manually and send them through an external mail client.
