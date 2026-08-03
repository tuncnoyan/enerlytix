# Feature Specification: Report Write Delegation

**Feature Branch**: `[011-report-write-delegation]`

**Created**: 2026-08-03

**Status**: Draft

**Input**: User description: "I want to add a new feature to delegate write access to reports. Report owners should be able to grant write access to other users for collaboration. Similarly, team leads and managers should be able to grant write access to all reports in their organisation, including themselves. For instance, a user level report owner is on sick leave and one of their reports needs to be updated or completed, in such a case, their team lead should be able to grant write access to another user or themselves for this job. Another scenario could be, a user is overloaded and needs other users' support. In such a case they should be able to grant write access to another user from the same team to get the support."

## Clarifications

### Session 2026-08-03

- Q: Who can revoke delegated write access? -> A: Report owner, original grantor, or same-organisation team lead/manager.
- Q: How are concurrent grant/revoke conflicts resolved? -> A: Last-write-wins by server commit timestamp, with both actions logged.
- Q: Who can view delegation details? -> A: Any user with read access to the report.
- Q: What makes a delegate ineligible and when is it enforced? -> A: Ineligible means inactive account or out-of-scope for delegation policy; eligibility is enforced at grant time and rechecked at report-save submission.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Owner Delegates Team Support (Priority: P1)

As a report owner, I need to grant and remove write access for teammates so I can get help completing reports when workload is high.

**Why this priority**: Owner-led delegation is the most frequent collaboration need and directly prevents delivery delays.

**Independent Test**: Can be tested independently by having a report owner grant write access to a same-team user, verify edits are allowed, then revoke access and verify editing is blocked.

**Acceptance Scenarios**:

1. **Given** I own a report and another active user is in my team, **When** I grant that user write access, **Then** that user can edit and save updates to my report.
2. **Given** I own a report and the report has an active delegated writer, **When** I revoke that access, **Then** that user can no longer save edits to the report.
3. **Given** I own a report, **When** I attempt to grant write access to a user outside my organisation, **Then** the system rejects the grant and explains the scope restriction.

---

### User Story 2 - Lead or Manager Delegates Org Coverage (Priority: P2)

As a team lead or manager, I need to grant write access on any report in my organisation, including to myself, so urgent coverage can continue when an owner is unavailable.

**Why this priority**: Leadership override is essential for business continuity during leave and operational incidents.

**Independent Test**: Can be tested independently by having a team lead or manager grant write access on a report they do not own and confirming the selected user (or themselves) can edit.

**Acceptance Scenarios**:

1. **Given** I am a team lead in the same organisation as a report, **When** I grant write access to another eligible user, **Then** that user can edit the report even if they are not the owner.
2. **Given** I am a manager in the same organisation as a report, **When** I grant write access to myself, **Then** I can edit that report without changing ownership.
3. **Given** I am a lead or manager from a different organisation, **When** I try to grant write access on that report, **Then** the system denies the action.

---

### User Story 3 - Users See Delegation Accountability (Priority: P3)

As a user working with reports, I need clear visibility of who has delegated write access and who granted it so collaboration remains accountable.

**Why this priority**: Visibility reduces confusion, prevents conflicting edits, and supports governance reviews.

**Independent Test**: Can be tested independently by opening a report access view and verifying active write delegates and grantor details are accurate after grant and revoke actions.

**Acceptance Scenarios**:

1. **Given** a report has active delegated writers, **When** a user with read access views report access details, **Then** the list shows each delegate and who granted the access.
2. **Given** delegated access is revoked, **When** report access details are viewed, **Then** revoked users are not shown as active writers.
3. **Given** no delegated writers exist, **When** report access details are viewed, **Then** the system clearly indicates owner-only write access.

---

### Edge Cases

- A report owner attempts to grant access to an inactive account: the request is rejected.
- Two authorized grantors submit conflicting grant/revoke changes for the same user at nearly the same time: the system applies last-write-wins by server commit timestamp and logs both actions.
- A delegated writer loses eligibility (for example, account deactivated) before saving changes: save is blocked at submit time.
- A delegated writer who was eligible at grant time but becomes inactive or out-of-scope before saving changes: save is blocked at submit time.
- A lead or manager is temporarily acting as report owner and also grants themselves access: system avoids duplicate effective write access records.
- A report has multiple delegated writers and one is revoked: remaining delegated writers keep access unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST keep report ownership unchanged when delegated write access is granted or revoked.
- **FR-002**: The system MUST allow a report owner to grant write access to active users within the same team.
- **FR-003**: The system MUST allow the report owner to revoke any active delegated write access on their report.
- **FR-004**: The system MUST allow team leads to grant write access to any report in their organisation, including granting access to themselves.
- **FR-005**: The system MUST allow managers to grant write access to any report in their organisation, including granting access to themselves.
- **FR-006**: The system MUST prevent users without owner, team lead, or manager grant authority from granting or revoking write access.
- **FR-007**: The system MUST prevent any user from granting or revoking write access for reports outside their organisation scope.
- **FR-008**: The system MUST enforce write permission checks at the moment a report edit is submitted.
- **FR-009**: The system MUST store delegation records containing report, delegate user, grantor user, grant timestamp, and active status.
- **FR-010**: The system MUST also allow revocation by the original grantor and by same-organisation team leads/managers, so delegated write access can be removed without changing report ownership or deleting report content.
- **FR-011**: The system MUST expose current active delegated writers and grantor identity to any user who has read access to that report.
- **FR-012**: The system MUST treat delegated write access as effective until explicitly revoked or the delegate becomes ineligible. A delegate is ineligible when the account is inactive or the user is no longer within the required delegation scope; eligibility MUST be checked at grant time and at report-save submission.
- **FR-013**: The system MUST keep an auditable history of delegation grant and revoke actions for each report.
- **FR-014**: When concurrent grant and revoke actions target the same delegate/report pair, the system MUST apply last-write-wins using server commit timestamp and preserve both actions in audit history.

### Key Entities *(include if feature involves data)*

- **Report**: A report owned by one user and editable by the owner plus any currently delegated writers.
- **Delegated Write Access**: A grant linking a report to a delegate user, with grantor, activation state, and lifecycle timestamps.
- **Grant Authority Role**: A role assignment that determines whether a user can delegate access at report-owner scope (owner) or organisation scope (team lead, manager).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In acceptance testing, 100% of valid owner-to-same-team delegation requests result in successful edit capability for the selected delegate.
- **SC-002**: In acceptance testing, 100% of valid lead/manager organisation-scope delegation requests result in successful edit capability for the selected delegate.
- **SC-003**: In permission enforcement tests, 100% of unauthorized delegation attempts are blocked with a clear denial outcome.
- **SC-004**: In permission enforcement tests, 100% of revoked delegates are unable to save subsequent report edits.
- **SC-005**: In user validation sessions, at least 90% of participants can identify active delegated writers and grantors for a report within 15 seconds.

## Assumptions

- Existing user authentication and organisational hierarchy data are already available and trusted as the source for role and team membership.
- Owner delegation is limited to same-team users to match the collaboration scenario described for workload support.
- Team leads and managers can delegate access across all reports in their own organisation but not across organisations.
- Delegated write access applies to editing report content only; ownership transfer and approval workflows are out of scope for this feature.
- Existing audit and log retention policies are sufficient for storing delegation history required by this feature.
