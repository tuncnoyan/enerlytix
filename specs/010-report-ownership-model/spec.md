# Feature Specification: Report Ownership Model

**Feature Branch**: `[010-report-ownership-model]`

**Created**: 2026-08-03

**Status**: Draft

**Input**: User description: "I want to add a report ownership model to Enerlytix. I drafted the key points in the text document I uploaded. This would be another critical key stone for the app before adding report validation workflows, team based acces and page level review system in later sprints."

## Clarifications

### Session 2026-08-03

- Q: How should ownership transfer work when an owner is inactive or unavailable? → A: TeamLead>Manager>Admin fallback
- Q: What qualifies a fallback candidate as available? → A: Active, role-matched, site/org-assigned
- Q: What access should the previous owner retain after automatic transfer? → A: Keep write collaborator access
- Q: How is owner unavailability determined? → A: Team lead approval workflow

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Own and Edit My Reports (Priority: P1)

As a report creator, I need each report to be owned by one person so editing responsibility is clear and I can safely maintain my report content.

**Why this priority**: Clear ownership and edit control are foundational for controlled collaboration and directly protect report integrity.

**Independent Test**: Can be fully tested by creating a report as one user and confirming only that owner can edit while other users can view but not edit.

**Acceptance Scenarios**:

1. **Given** a user creates a new report, **When** the report is saved, **Then** the system records that user as the report owner.
2. **Given** a report has an owner, **When** the owner opens the report, **Then** the owner can read and modify the report.
3. **Given** a report has an owner, **When** a non-owner opens the report without additional write access, **Then** they can read but cannot modify it.

---

### User Story 2 - Grant Named Collaborators Write Access (Priority: P2)

As a report owner, I need to grant write access to specific named users so trusted collaborators can update report content when needed.

**Why this priority**: Collaboration is required for operational continuity, but must remain owner-controlled to prevent uncontrolled edits.

**Independent Test**: Can be fully tested by having an owner grant write access to one named user and verifying that user can edit while ungranted users remain read-only.

**Acceptance Scenarios**:

1. **Given** I am the report owner, **When** I grant write access to a named user, **Then** that named user can edit the report.
2. **Given** I am not the report owner, **When** I attempt to grant or change write access, **Then** the system rejects the action.
3. **Given** a named user has granted write access, **When** the owner revokes that access, **Then** that user returns to read-only access.

---

### User Story 3 - View Ownership Metadata on Saved Reports (Priority: P3)

As a user viewing saved reports, I need to see report ownership and recent change details so I can understand accountability and current report state.

**Why this priority**: Metadata visibility supports transparency, operational handover, and preparation for later governance workflows.

**Independent Test**: Can be fully tested by opening the Saved Reports page and confirming required ownership and modification fields display correctly for each report.

**Acceptance Scenarios**:

1. **Given** reports exist in the system, **When** a user opens the Saved Reports page, **Then** each row shows report name/site, reporting month, owner, created date, last modified by, last modified date, and status.
2. **Given** a report is edited by a user with write permission, **When** the update is saved, **Then** last modified by and last modified date update to reflect that edit.

---

### Edge Cases

- A report owner account becomes inactive or unavailable: ownership is automatically transferred to the first available user in this strict order: team lead, then manager, then system admin; the previous owner retains collaborator write access unless manually removed.
- Owner unavailability is not inferred automatically; transfer begins only after a team lead approval workflow marks the owner as unavailable.
- An owner attempts to grant write access to a user who already has owner-level rights: the system should avoid duplicate or conflicting access records.
- A user opens a report with write access, then that access is revoked before save: the save attempt must be blocked and the user informed that permissions changed.
- A report has never been edited after creation: last modified by and last modified date should still present clearly, using the creation actor/date as the initial baseline.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST assign exactly one owner to each report record.
- **FR-002**: The system MUST store the following report metadata fields: owner, created date, last modified by, and last modified date.
- **FR-003**: The system MUST ensure the report owner has read and write access to their report.
- **FR-004**: The system MUST ensure non-owners have read-only access by default.
- **FR-005**: The system MUST allow the report owner to grant write access to specific named users.
- **FR-006**: The system MUST allow the report owner to revoke previously granted write access from named users.
- **FR-007**: The system MUST prevent non-owners from granting, modifying, or revoking report write access permissions.
- **FR-008**: The system MUST enforce write permission checks at the time a report change is submitted.
- **FR-009**: The system MUST update last modified by and last modified date whenever report content is changed by a permitted user.
- **FR-010**: The Saved Reports page MUST display: report name/site, reporting month, owner, created date, last edited by, last edited at, and status for each listed report.
- **FR-011**: The system MUST preserve an accurate, queryable history of active write-grant assignments per report for accountability.
- **FR-012**: If the current owner becomes inactive or unavailable, the system MUST automatically transfer ownership to the first available candidate in this strict order: team lead, then manager, then system admin.
- **FR-013**: For automatic fallback transfer, a candidate is considered available only if the account is active, has the required fallback role, and is assigned to the same report site/organization scope.
- **FR-014**: After automatic ownership transfer, the previous owner MUST retain report write access as a collaborator until manually revoked by an authorized owner.
- **FR-015**: The system MUST initiate ownership fallback transfer only after a team lead approval workflow explicitly marks the current owner as unavailable.

### Key Entities *(include if feature involves data)*

- **Report**: A saved reporting artifact for a site and reporting month, with ownership, status, and lifecycle metadata.
- **Report Access Grant**: A record that links a report to a named user who has owner-granted write permission.
- **Report Metadata Snapshot**: The accountability fields attached to each report state, including creator, creation time, last editor, and last edit time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of newly created reports have a non-empty owner and creation timestamp at first save.
- **SC-002**: In permission validation tests, 100% of unauthorized write attempts are blocked and return a clear access-denied outcome.
- **SC-003**: In permission validation tests, 100% of owner-granted named users can successfully complete report edits without additional manual intervention.
- **SC-004**: For a representative saved-report listing, required ownership and modification fields are visible for at least 99% of displayed report rows.
- **SC-005**: Stakeholder UAT confirms that users can identify report accountability details (owner and most recent editor) within 10 seconds per report in at least 90% of sampled tasks.

## Assumptions

- Existing authenticated user identities and report records remain the source of truth and are reused.
- This phase introduces report-level ownership and named-user write grants only; team-level access logic is handled in a later sprint.
- Existing report statuses remain unchanged; this feature only requires status visibility on Saved Reports.
- Historical reports without complete ownership metadata will be backfilled or displayed using a documented fallback during rollout.
- Permission checks apply consistently to all user-facing report edit actions in scope for this phase.