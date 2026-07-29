# Feature Specification: Platform Foundation

**Feature Branch**: `008-platform-foundation`

**Created**: 2026-07-29

**Status**: Draft

**Input**: User description: "Move Enerlytix from a single-user application to a hosted multi-user application with secure authentication, invitation-based onboarding, user administration, and basic admin/user roles."

## Clarifications

### Session 2026-07-29 (Initial)

- Q: For the initial release, which authentication approach should the platform use for sign-in and password recovery? → A: Email/password with password reset.
- Q: For the initial release, how long should an invitation remain valid before it expires? → A: 7 days.

### Session 2026-07-29 (Organisational Structure Clarifications)

- Q: How should the team hierarchy be structured (flat, hierarchical with sub-teams, or matrix)? → A: Hierarchical — Teams can contain sub-teams; a user's access includes their team and all parent teams.
- Q: Can users hold multiple roles simultaneously (e.g., both manager and team lead)? → A: Yes, overlapping roles are allowed — A user can be admin, manager, team lead, and/or user all at once.
- Q: How should report access be scoped in a hierarchical team structure? → A: Hierarchical access with inheritance — Users access reports from their role level downward through the hierarchy.
- Q: What functions should be included in the admin panel, and how should they be organized? → A: Consolidated panel — All admin functions (users, teams, roles, hierarchy view) should be in one "panel" page with modular sections.
- Q: When should users gain access to reports — immediately upon sign-in or only after team assignment? → A: Team-gated — Users see reports only after team assignment; new users see a prompt or empty state until assigned.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sign in securely and manage personal access (Priority: P1)

As an authenticated user, I can sign in to Enerlytix, reset my password when needed, and view my account profile so I can access the application safely and manage my own account details.

**Why this priority**: Secure sign-in and self-service account recovery are foundational to any multi-user deployment and protect access to business data.

**Independent Test**: Create a valid account, sign in, request a password reset, and verify the profile page is available after authentication.

**Acceptance Scenarios**:

1. **Given** a registered user with valid credentials, **When** they sign in, **Then** they are granted access to the application and directed to their permitted workspace.
2. **Given** a user who has forgotten their password, **When** they start password recovery, **Then** they can complete the reset flow and sign in with their new password.
3. **Given** an authenticated user, **When** they open their profile page, **Then** they can view their account information and confirm their current account state.

---

### User Story 2 - Join the platform through invited access (Priority: P1)

As an invited user, I can accept an invitation to join Enerlytix, complete registration, and begin using the platform without requiring open self-registration.

**Why this priority**: Invitation-based onboarding controls access, reduces unauthorized accounts, and is a core requirement for an enterprise-ready hosted experience.

**Independent Test**: Receive an invitation, open the acceptance flow, complete the onboarding steps, and verify the account becomes active.

**Acceptance Scenarios**:

1. **Given** a user has received a valid invitation, **When** they accept it, **Then** they can complete the registration flow and become an active user.
2. **Given** an invitation that has expired, **When** a user attempts to use it, **Then** the system prevents activation and clearly indicates the invitation is no longer valid.
3. **Given** a user without a valid invitation, **When** they try to register, **Then** access is denied and they are guided to request an invitation.

---

### User Story 3 - Administer users and access rights (Priority: P1)

As an administrator, I can manage user accounts and role assignments so the platform remains secure, organized, and appropriate for the business team.

**Why this priority**: User administration is the core operational capability for moving from a single-user tool to a hosted multi-user platform.

**Independent Test**: Sign in as an administrator, create a user invitation, review the user list, and perform account state changes such as enablement, disablement, rename, password reset, or deletion.

**Acceptance Scenarios**:

1. **Given** an administrator is signed in, **When** they view the user administration area, **Then** they can see the list of current users and their account state.
2. **Given** an administrator creates a new invitation, **When** the invitation is sent and accepted, **Then** the new user is created with the expected access status.
3. **Given** an administrator changes a user account state, **When** the change is applied, **Then** the user’s ability to sign in and use the platform reflects the updated status.
4. **Given** an administrator performs account management actions such as renaming, resetting passwords, or deleting users, **When** the action completes, **Then** the change is reflected in the user record and the platform behavior.

---

### User Story 4 - Manage the organisational structure and reporting hierarchy (Priority: P1)

As a manager, team lead, or administrator, I can create teams, assign users, and adjust reporting relationships so the organisation structure is clear and permissions match the business hierarchy.

**Why this priority**: Organisational structure and reporting boundaries are essential for approval workflows and for ensuring the right people can see the right reports.

**Independent Test**: Create a team, assign users and a team lead, change a manager, and verify that the organisation structure and reporting access reflect those changes.

**Acceptance Scenarios**:

1. **Given** an administrator or manager creates a team, **When** the team is saved, **Then** it becomes part of the organisation structure with an assigned manager and team lead where applicable.
2. **Given** users are assigned to a team, **When** the assignment is updated, **Then** their access and reporting scope reflect their team membership.
3. **Given** a manager or team lead changes, **When** the update is applied, **Then** the new reporting relationship is used for subsequent access and approvals.
4. **Given** a team is transferred or reorganised, **When** the change is made, **Then** the affected users and reporting permissions move with the new structure.

---

### User Story 5 - Use the admin panel and role-based navigation (Priority: P1)

As an administrator, I can open the admin panel from the home-page links menu and use a familiar, branded interface to manage users, teams, and access rights.

**Why this priority**: The admin panel is the primary control surface for operational administration and should be easy to find and visually consistent with the rest of the product.

**Independent Test**: Sign in as an administrator, confirm the admin panel link appears in the top-right links menu, open the panel page, and verify that it matches the home page’s overall layout and colour scheme.

**Acceptance Scenarios**:

1. **Given** an administrator is signed in, **When** they view the home page, **Then** the top-right links menu includes a visible link to the admin panel.
2. **Given** a non-administrator user is signed in, **When** they view the home page, **Then** they do not see the admin panel link in the top-right links menu.
3. **Given** an administrator opens the panel page, **When** the page loads, **Then** it presents a layout and colour scheme consistent with the home page experience.
4. **Given** a user with a standard role accesses the panel page, **When** they attempt to open it, **Then** access is denied and they are returned to the appropriate permitted experience.

---

### Edge Cases

- What happens if a user tries to sign in with a disabled account? The system denies access and shows a clear account-status message.
- What happens if an invitation has expired before it is accepted? The invitation cannot be used and the user must request a new invite.
- What happens if an administrator performs a sensitive account action for the wrong account? The action must apply only to the intended user record and be visible through the account management workflow.
- What happens if a password reset request is initiated for a user who does not exist or is inactive? The system must handle the request securely without revealing sensitive account details.
- What happens if an organisation changes are made while users are assigned to multiple teams or reporting roles? The system must preserve the new hierarchy consistently and prevent ambiguous access.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support secure email/password sign-in and sign-out.
- **FR-002**: The system MUST allow users to initiate and complete an email-based password reset flow.
- **FR-003**: The system MUST provide a user profile page where signed-in users can view their account information.
- **FR-004**: The system MUST support invitation-only registration so new accounts can be created only through a valid invitation.
- **FR-005**: The system MUST allow invitations to expire after 7 days from issuance.
- **FR-006**: The system MUST provide a clear invitation acceptance flow for invited users.
- **FR-007**: The system MUST allow administrators to view the current list of users.
- **FR-008**: The system MUST allow administrators to create user invitations.
- **FR-009**: The system MUST allow administrators to enable and disable user accounts.
- **FR-010**: The system MUST allow administrators to rename user accounts.
- **FR-011**: The system MUST allow administrators to reset user passwords.
- **FR-012**: The system MUST allow administrators to delete user accounts.
- **FR-013**: The system MUST support at least four basic roles for organisational structure: admin, manager, team lead, and user.
- **FR-014**: The system MUST ensure administrator users can access user administration functions while standard users cannot.
- **FR-015**: The system MUST prevent disabled or inactive users from signing in to the platform.
- **FR-016**: The system MUST ensure account changes performed by administrators are applied consistently to the relevant user account.
- **FR-017**: The system MUST support hierarchical team creation and management, including the ability to create sub-teams under parent teams.
- **FR-018**: The system MUST allow administrators or managers to assign users to teams, change team managers, transfer team leads, and move teams within the hierarchy.
- **FR-019**: The system MUST provide hierarchical role-based report access so users can access their own reports, team leads can access team reports and sub-team reports within their scope, managers can access all reports from their managed teams and sub-teams, and administrators can access all reports.
- **FR-020**: The system MUST enforce team-gated report access where users see reports only for teams they are assigned to or manage; new users see an empty state until assigned to a team.
- **FR-021**: The system MUST provide a consolidated admin panel (named \"panel\") with sections for user management, team management, organisational hierarchy view, and role assignments, all with layout and colour scheme consistent with the home page.
- **FR-022**: The system MUST expose the admin panel link in the home-page top-right links menu for administrators only.
- **FR-023**: The system MUST handle account recovery and invitation flows securely and without exposing private account information to unauthorized users.

### Key Entities *(include if feature involves data)*

- **User Account**: The person-specific account that provides access to the platform, including identity, status, roles (admin, manager, team lead, user), and profile information. A user can hold multiple roles simultaneously.
- **Invitation**: A time-limited permission that enables a new person to create or activate a platform account.
- **Team**: A hierarchical group within the organisation that can contain sub-teams, has a manager, and may have a team lead. Users are assigned to teams for reporting and access scope.
- **Role Assignment**: Multi-valued designation that determines whether a user has administrative, managerial, team-lead, and/or standard access. A single user can hold multiple roles.
- **Organisation Structure**: The hierarchical reporting tree connecting teams, sub-teams, managers, team leads, and users. Parent team managers can access all reports from child teams.
- **Account Status**: The current active or disabled state of a user account that affects sign-in permissions.
- **Report Scope**: Determined by team membership and role; a user can access reports from their assigned team and all sub-teams within their scope based on their role level.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of valid invited users can complete the invitation acceptance flow and sign in successfully.
- **SC-002**: 100% of enabled users can sign in and access the appropriate workspace for their role.
- **SC-003**: 95% or more of password reset requests are completed successfully without support intervention.
- **SC-004**: 100% of administrator account-management actions are reflected in the affected user account state.
- **SC-005**: 95% or more of administrators can complete core user administration tasks without confusion or blocking issues.
- **SC-006**: 100% of hierarchical team changes (including sub-team creation, team assignment, and manager transfer) are reflected in reporting access and organisational structure.
- **SC-007**: 100% of team-gated report access rules are enforced; users see only reports for teams they are assigned to or manage.
- **SC-008**: 100% of administrators see the admin panel link in the home-page links menu; non-administrators do not.
- **SC-009**: 100% of administrators can access the consolidated admin panel and manage users, teams, and organisational hierarchy from a single branded page.

## Assumptions

- The initial deployment will support a small to medium number of users with a single hosted environment.
- An initial administrator account can be created or provisioned as part of onboarding.
- User profile data in this phase is limited to basic account information and does not require full profile customization.
- Invitation expiry and access controls are required for secure multi-user operation from the start of rollout.
- The platform will continue to use existing business workflows after authentication and access control are in place.
- Teams have a hierarchical structure where sub-teams inherit parent team properties and managers can oversee multiple levels.
- Users can hold multiple roles simultaneously (e.g., a user can be both a manager and a team lead at different levels).
- Report access is determined by team membership and role level; users see reports only for their assigned team and sub-teams within their access scope.
- The admin panel is the primary interface for all administrative functions and consolidates user, team, and hierarchy management.
- New users begin with no team assignment and see an empty state or prompt until an administrator assigns them to a team.
