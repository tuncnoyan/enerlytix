# Feature Specification: Report Validation Workflow

**Feature Branch**: `[012-report-validation-workflow]`

**Created**: 2026-08-04

**Status**: Draft

**Input**: User description: "I want to add a validation workflow to Enerlytix. I drafted all details in the text file I uploaded. Could you create spec document accordingly, please."

## Clarifications

### Session 2026-08-04

- Q: When should page validation reset automatically after edits? -> A: Only business/report content changes clear validation; validation-comment edits do not clear it.
- Q: Who can re-grant write access on Final reports? -> A: Team lead, manager, or admin in the owner's supervisory chain can re-grant write access.
- Q: What happens to page validations when validator is reassigned? -> A: Reset all page validations to unvalidated when validator is reassigned.
- Q: Which users are eligible validators? -> A: Validator must be in same team or owner's supervisory chain, and cannot be the owner.

## Status Model

- **Publication Status**: Draft or Final. This controls whether the report is officially finalized.
- **Validation Status**: Draft, Awaiting Validation, or Validated. This controls pre-final quality-control readiness.
- Final save is allowed only when Validation Status is Validated.
- Validation Status transitions do not overwrite Publication Status; Publication Status changes to Final only on successful final save.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Assign Independent Validator (Priority: P1)

A report owner, team lead, manager, or admin assigns a validator who is not the report owner so the report can enter a controlled validation step before finalization.

**Why this priority**: Without independent validator assignment and state transition, the core quality-control workflow cannot begin.

**Independent Test**: Can be fully tested by assigning a validator to an existing draft report and confirming Validation Status changes to Awaiting Validation with assigned validator visible to authorized users.

**Acceptance Scenarios**:

1. **Given** a report in Draft validation status and an eligible assigner, **When** they assign an eligible validator who is not the owner, **Then** the report Validation Status changes to Awaiting Validation and the validator is recorded.
2. **Given** a report in Draft status, **When** someone tries to assign the owner as validator, **Then** the assignment is rejected with a clear message that validator must be a different person.
3. **Given** a report with an assigned validator, **When** users view report details and saved reports, **Then** the validator name is displayed consistently.

---

### User Story 2 - Validate Report Pages With Comment Trail (Priority: P2)

Report owners, contributors, and validators collaborate using dedicated validation comments on each report page, while only the validator can mark a page validated.

**Why this priority**: Page-level validation is required to confirm review completeness and to enforce accountability for each section.

**Independent Test**: Can be fully tested by entering validation comments from different roles and verifying only the validator can check page validation checkboxes.

**Acceptance Scenarios**:

1. **Given** a report page in Awaiting Validation, **When** owner, contributor, or validator adds text in the validation comment area, **Then** the comment is saved and visible to users with write access.
2. **Given** a report page in Awaiting Validation, **When** the assigned validator checks the page validation checkbox, **Then** the page is marked validated and shown as validated, and any later business/report content edit clears page validation before accepting the edit.
3. **Given** a report page in Awaiting Validation, **When** a non-validator user attempts to check the validation checkbox, **Then** the action is denied.

---

### User Story 3 - Reopen Validation on Edits and Gate Finalization (Priority: P3)

If any writable user changes validated page content, that page automatically returns to unvalidated state; once all pages are validated, the report is marked Validated and can be finalized.

**Why this priority**: This preserves integrity by ensuring validation always reflects the latest edited content and prevents finalization of unreviewed changes.

**Independent Test**: Can be fully tested by validating all pages, editing one validated page, and confirming validation reset, then re-validating all pages and confirming finalization gating behavior.

**Acceptance Scenarios**:

1. **Given** a validated page, **When** owner or contributor edits that page content, **Then** the page validation checkbox is automatically cleared and a warning reminds users that edits reset validation.
2. **Given** all report pages are validated, **When** users open the report, **Then** a visible message indicates report is ready for final save, report status is Validated, and validation timestamp is shown in report and saved reports views.
3. **Given** a report is not fully validated, **When** owner or contributor attempts to save it as Final, **Then** finalization is blocked until all pages are validated.
4. **Given** a report already saved as Final after validation, **When** write access is re-granted by an authorized superior and edits are made, **Then** validated status is removed and the report re-enters a non-final editable validation cycle.

### Edge Cases

- Validator is assigned, then removed or replaced before validation completes: the report remains in Awaiting Validation and only the currently assigned validator can validate pages.
- A report has no contributors and only owner plus validator: validation still proceeds normally with owner/validator collaboration.
- A report is partially validated and then reassigned to a new validator: previously validated pages are treated as unvalidated to ensure end-to-end review by the currently accountable validator.
- A user with read-only access views validation information: validator identity, status, and validation date are visible, but no write or validation actions are available.
- Attempts to finalize a report while one or more pages are unvalidated must fail with a clear explanation of outstanding pages.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support assigning one validator per report by the report owner or the owner's superiors (team lead, manager, admin).
- **FR-002**: System MUST prevent assigning the report owner as validator.
- **FR-002A**: System MUST only allow validator assignment to active users who are either in the owner's same team or in the owner's supervisory chain.
- **FR-003**: System MUST transition Validation Status from Draft to Awaiting Validation immediately after a validator is assigned.
- **FR-004**: System MUST expose Validation Status values as Draft, Awaiting Validation, and Validated, separate from Publication Status.
- **FR-005**: System MUST display the assigned validator name on both the report page and saved reports listing.
- **FR-006**: System MUST provide a distinct validation comments area on each report page for owner, contributors, and validator collaboration.
- **FR-007**: System MUST provide a page-level validation checkbox on each report page that only the assigned validator can mark as validated.
- **FR-008**: System MUST, when a write-authorized user attempts a business/report content edit on a validated page, clear that page's validated state and warning-state it before accepting the edit.
- **FR-009**: System MUST automatically clear a page's validated state when any user with write access changes business/report page content, excluding edits to the validation comment area.
- **FR-010**: System MUST display a visible warning that editing validated content resets page validation.
- **FR-011**: System MUST detect when all report pages are validated and set the report validation status to Validated.
- **FR-012**: System MUST record and display the report validation timestamp on both the report page and saved reports listing when report status becomes Validated.
- **FR-013**: System MUST allow Publication Status to change to Final only when Validation Status is Validated.
- **FR-014**: System MUST block saving as Final when any page remains unvalidated and provide clear user feedback.
- **FR-015**: System MUST keep reports saved as Final read-only for regular write users unless a team lead, manager, or admin in the owner's supervisory chain re-grants write access.
- **FR-016**: System MUST clear report-level validated status if a Final report is reopened for write and edited after superior-approved write re-grant.
- **FR-017**: System MUST show validated-by person and validation date as report metadata wherever report status is summarized.
- **FR-018**: System MUST remove or replace the non-essential Updated column in saved reports if needed to surface validator and validation date metadata.
- **FR-019**: System MUST reset all page-level validations to unvalidated whenever the assigned validator is changed.

### Key Entities *(include if feature involves data)*

- **Report Validation Assignment**: Represents the current validator linked to a report, including who assigned the validator and assignment timing.
- **Report Validation State**: Represents report-level progression (Draft, Awaiting Validation, Validated, Final) and includes validated-by identity and validation timestamp.
- **Page Validation State**: Represents per-page validation status, who validated the page, and when it was validated.
- **Validation Comment Entry**: Represents collaborative validation notes tied to report pages and authored by owner, contributor, or validator.
- **Write Regrant Event**: Represents superior-approved reopening of a Final report for edits, triggering reset of validated state upon subsequent modifications.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of reports saved as Final have all pages validated and a recorded validator identity.
- **SC-002**: 100% of attempted Final saves for reports with any unvalidated page are blocked with a clear reason.
- **SC-003**: For validated pages that are edited by write-authorized users, validation reset is reflected to users within the same editing session in at least 99% of cases.
- **SC-004**: At least 95% of pilot users in owner/contributor/validator roles can complete assign-validate-finalize workflow without support.
- **SC-005**: Report and saved reports views show matching validator name and validation date for at least 99% of validated reports in acceptance testing.

## Assumptions

- Existing role hierarchy (owner, contributor, team lead, manager, admin) and access-control model remain authoritative and are reused.
- Validation workflow applies to report pages already included in the current report structure; no new report page types are introduced in this feature.
- Validation comments are part of ongoing report collaboration and follow existing report visibility rules for users with report access.
- Finalization remains an explicit user action by owner or contributor, but it is always gated by completion of full-page validation.
- Saved reports listing can be adjusted to prioritize validation metadata display (including removing the current Updated column).
