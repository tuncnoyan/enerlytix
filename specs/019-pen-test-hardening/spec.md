# Feature Specification: Pen-Test Hardening and Readiness

**Feature Branch**: `[019-pen-test-hardening]`

**Created**: 2026-08-07

**Status**: Draft

**Input**: User description: "I ran a pen-test readiness assessment, and you can find findings and suggested resolutions in the file I attached. Could you now convert it into a spec document?"

## Clarifications

### Session 2026-08-07

- Q: For the one-time recovery mechanism in FR-006, what token validity policy should the spec require? → A: Single-use token valid for 15 minutes.
- Q: For FR-010, how should trusted proxy boundaries be defined for accepting forwarding headers? → A: Trust forwarding headers only from configured proxy CIDR allowlist.
- Q: For FR-011, what enforcement point should be required for production security posture checks? → A: Fail CI/release checks and block production startup if required controls are missing.
- Q: For FR-003 and related access-control criteria, what response policy should the spec require for denied access? → A: Return 401 for unauthenticated requests and 403 for authenticated-but-unauthorized requests.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Close Unauthorized Access Paths (Priority: P1)

As a platform administrator, I need all sensitive endpoints and actions to require authenticated, role-appropriate access so unauthenticated or under-privileged users cannot trigger imports, read sensitive report data, or change critical settings.

**Why this priority**: Unauthorized access and privilege bypass findings are the highest risk items and are direct blockers for a security assessment pass.

**Independent Test**: Can be fully tested by attempting each protected endpoint with anonymous, standard, and admin accounts and verifying only authorized actors succeed.

**Acceptance Scenarios**:

1. **Given** an unauthenticated user, **When** they call any protected import, report-data, or settings mutation endpoint, **Then** access is denied and no state-changing action is performed.
2. **Given** an authenticated non-admin user, **When** they attempt admin-only settings updates or manual sync triggers, **Then** access is denied and no privileged action is performed.
3. **Given** an authorized admin user, **When** they perform approved protected actions, **Then** the actions complete successfully and are auditable.

---

### User Story 2 - Secure Account and Credential Workflows (Priority: P2)

As a security reviewer, I need account invitation and reset workflows to avoid predictable credentials and weak password acceptance so account takeover risk is reduced.

**Why this priority**: Credential weaknesses can directly lead to unauthorized account access even after endpoint authorization fixes.

**Independent Test**: Can be tested by performing account reset and invitation acceptance flows and verifying no predictable credentials are issued and weak passwords are rejected.

**Acceptance Scenarios**:

1. **Given** an administrator resets a user account, **When** the reset action completes, **Then** no static shared password is assigned and the user is required to set a unique credential through a single-use recovery token valid for 15 minutes.
2. **Given** an invited user submits a weak password, **When** they attempt account activation, **Then** activation is rejected with actionable validation feedback.
3. **Given** an invited user submits a compliant password, **When** activation succeeds, **Then** the account is created and invitation state is safely finalized.

---

### User Story 3 - Demonstrate Deployment-Grade Security Defaults (Priority: P3)

As an operations owner, I need production-mode security defaults and evidence checks to fail closed so insecure runtime configuration does not accidentally reach deployment.

**Why this priority**: Pen-test readiness depends on both code behavior and secure deployment configuration.

**Independent Test**: Can be tested by running deployment security checks in production-like mode and confirming required transport, cookie, and secret controls are enforced.

**Acceptance Scenarios**:

1. **Given** a production-mode environment with insecure security toggles, **When** startup validation or release checks run, **Then** deployment is blocked with clear remediation guidance.
2. **Given** production-mode configuration is complete, **When** deployment security checks run, **Then** critical hardening checks pass.
3. **Given** redirect parameters are user-provided, **When** redirect validation executes, **Then** external or scheme-relative redirect targets are rejected.

### Edge Cases

- What happens when a user is authenticated but lacks the specific role needed for a protected endpoint?
- How does the system behave when one-time credential recovery artifacts expire or are replayed?
- What happens when requests include forged forwarding headers for source IP attribution?
- How does redirect handling process malformed, encoded, or double-slash paths?
- What happens when production-mode startup is missing one required security setting but all others are present?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST require authentication for all endpoints that expose report, consumption, import-run, or other business-sensitive operational data.
- **FR-002**: System MUST enforce role-based authorization for all settings mutation, capacity upload, and manual synchronization actions.
- **FR-003**: System MUST deny unauthorized privileged actions with explicit non-success responses and without performing side effects, returning 401 for unauthenticated requests and 403 for authenticated-but-unauthorized requests.
- **FR-004**: System MUST ensure sensitive data import operations cannot be invoked by anonymous users.
- **FR-005**: System MUST ensure sensitive data import operations cannot be invoked by users outside the authorized administrative scope.
- **FR-006**: System MUST replace any static or predictable administrator-triggered password reset behavior with a single-use recovery token valid for 15 minutes.
- **FR-007**: System MUST enforce password quality requirements during invitation-based account activation.
- **FR-008**: System MUST prevent open redirect behavior by allowing only validated internal redirect targets.
- **FR-009**: System MUST avoid exposing internal exception details to end users in failure responses.
- **FR-010**: System MUST only trust client IP forwarding headers when requests originate from a configured proxy CIDR allowlist; otherwise it MUST use direct connection source information.
- **FR-011**: System MUST fail closed for production security posture by failing CI/release checks and blocking production startup when required secure secret handling and secure transport/cookie controls are missing.
- **FR-012**: System MUST provide a repeatable readiness verification process that confirms deployment-grade security checks pass in production-like configuration.
- **FR-013**: System MUST log privileged security-relevant actions and denied attempts with sufficient actor and request context for audit purposes.
- **FR-014**: System MUST include automated regression tests covering protected endpoint access, credential workflow safeguards, redirect validation, and safe error handling.

### Key Entities *(include if feature involves data)*

- **Security Finding**: A prioritized vulnerability record describing risk category, impact level, affected surface, and remediation status.
- **Security Control Rule**: A policy record describing required authentication, authorization, input validation, redirect handling, error exposure behavior, and production safety constraints.
- **Readiness Evidence**: A verifiable record of control validation results, including endpoint access test outcomes and deployment security check outcomes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of endpoints categorized as sensitive in this feature return denied access for unauthenticated requests.
- **SC-002**: 100% of admin-scoped actions in this feature return denied access for authenticated non-admin users.
- **SC-003**: 100% of administrator-initiated account reset events use one-time recovery behavior and never assign a reusable static password.
- **SC-004**: 100% of invitation activation attempts with non-compliant passwords are rejected with validation feedback.
- **SC-005**: 100% of tested redirect payloads containing external or scheme-relative targets are rejected or safely normalized to internal destinations.
- **SC-006**: 0 end-user error responses in tested failure paths contain raw internal exception details.
- **SC-007**: Deployment readiness checks in production-like mode complete with no unresolved critical security warnings related to secret handling, secure transport, and secure cookies.
- **SC-008**: Security regression suite for this feature passes at 100% in CI and local pre-release verification.

## Assumptions

- The findings in the attached assessment represent the accepted starting scope for this hardening effort.
- Existing role definitions and administrative governance remain the authority for privileged access decisions.
- The system already has an auditable logging capability that can be extended for additional denial and privileged-action events.
- Production readiness verification is performed in an environment that accurately represents production security configuration.
- Dependency vulnerability scanning and network perimeter controls are tracked separately from this feature unless later expanded into scope.
