# Feature Specification: Admin Audit Log

**Feature Branch**: `[009-add-audit-log]`

**Created**: 2026-07-30

**Status**: Draft

**Input**: User description: "I want to add an audit log to Enerlytix. You can find details in the text file I uploaded. The audit log should be part of the Admin Panel and accessible by admins only."

## Clarifications

### Session 2026-07-30

- Q: Which actions are in scope for audit logging in Phase 3? → A: Log all authenticated mutating actions across the whole application (not only Admin Panel).
- Q: How should action type be represented for filtering and reporting? → A: Store a normalized action type code plus a separate human-readable message.
- Q: Should failed or denied attempts be logged? → A: Log successful mutating actions and denied/failed security-relevant attempts.
- Q: What retention rule should audit logs follow? → A: Follow organizational policy with a minimum retention of 1 year.
- Q: How should audit timestamps be stored? → A: Store timestamps in UTC; display can be localized.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record Traceable Activity (Priority: P1)

As an administrator or compliance reviewer, I need business-critical actions to be logged automatically so I can verify who did what and when.

**Why this priority**: Traceability is the core compliance need for this phase and must exist before collaborative editing is introduced.

**Independent Test**: Can be fully tested by performing tracked actions (create, delete, approve) and confirming a new audit log entry is created with all mandatory fields.

**Acceptance Scenarios**:

1. **Given** an authenticated user performs a tracked action, **When** the action succeeds, **Then** the system records an audit entry containing user identity, IP address, timestamp, affected entity, action type, and a human-readable summary.
2. **Given** a user attempts a security-relevant action that is denied or fails, **When** the system rejects or fails that action, **Then** the system records an audit entry describing the denied/failed attempt.
3. **Given** a user creates a report, **When** the action is committed, **Then** the audit log contains an entry equivalent to "Created Report #123".
4. **Given** a user deletes another user account, **When** the action is committed, **Then** the audit log contains an entry equivalent to "Deleted User John Smith".
5. **Given** a user approves a report, **When** the action is committed, **Then** the audit log contains an entry equivalent to "Approved Report #456".

---

### User Story 2 - Review and Filter Audit History (Priority: P2)

As an admin, I need to search and filter audit history in the Admin Panel so I can quickly investigate activity.

**Why this priority**: Logging without retrieval provides limited operational value; filtering is required for practical investigations.

**Independent Test**: Can be fully tested by opening the audit viewer, applying each filter independently and in combination, and verifying only matching entries are shown.

**Acceptance Scenarios**:

1. **Given** an admin opens the audit log viewer, **When** they filter by user, **Then** only entries from that user are displayed.
2. **Given** an admin enters a keyword, **When** search is applied, **Then** only entries containing that keyword in the summary or entity context are displayed.
3. **Given** an admin sets a date range and action type, **When** filters are applied, **Then** only entries within that range and action type are displayed.
4. **Given** a non-admin user attempts to access the audit log viewer, **When** access is requested, **Then** access is denied.

---

### User Story 3 - Export Filtered Audit Data (Priority: P3)

As an admin, I need to download audit logs in spreadsheet-friendly formats so I can provide evidence for audits and external reviews.

**Why this priority**: Export supports governance and audit workflows but depends on having reliable logging and filtering first.

**Independent Test**: Can be fully tested by applying filters and exporting in both supported formats, then confirming exported rows match on-screen filtered results.

**Acceptance Scenarios**:

1. **Given** an admin has applied filters, **When** they export to CSV, **Then** the file contains only rows matching the active filters.
2. **Given** an admin has applied filters, **When** they export to XLSX, **Then** the file contains only rows matching the active filters.
3. **Given** no entries match active filters, **When** export is requested, **Then** the system returns a valid empty export with headers and no data rows.

### Edge Cases

- How does the system behave when an affected entity is deleted after the event was logged? The historical log entry must remain readable.
- How does filtering behave when only one boundary date is provided (start only or end only)?
- How does the viewer behave when multiple events share the same timestamp?
- How does export behave for large filtered result sets?
- For exports exceeding 50,000 matching rows, the system should return a clear "narrow filters" message instead of attempting a long-running or partial export.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST create an audit log entry for all authenticated mutating actions across the application, including (at minimum) create report, delete user, and approve report actions.
- **FR-001a**: The system MUST create audit log entries for denied or failed security-relevant attempts, including unauthorized access attempts to protected resources.
- **FR-002**: Each audit log entry MUST include, at minimum, actor identity (actor user id when resolvable and username snapshot always), IP address, UTC timestamp, affected entity, normalized action type code, and human-readable action summary.
- **FR-003**: The audit log MUST record action summaries in a clear activity format (for example: created report, deleted user, approved report).
- **FR-004**: Audit logs MUST be accessible from the Admin Panel.
- **FR-005**: Only users with admin privileges MUST be able to access the audit log viewer.
- **FR-006**: The audit log viewer MUST support filtering by user.
- **FR-007**: The audit log viewer MUST support filtering by keyword.
- **FR-008**: The audit log viewer MUST support filtering by date range.
- **FR-009**: The audit log viewer MUST support filtering by normalized action type.
- **FR-010**: The system MUST allow admins to export audit log results in CSV format using the currently applied filters.
- **FR-011**: The system MUST allow admins to export audit log results in XLSX format using the currently applied filters.
- **FR-012**: Exported files MUST contain the same entries represented by active viewer filters at the moment of export.
- **FR-013**: Audit log records MUST remain available for review even if related entities are later modified or removed.
- **FR-014**: The system MUST reject unauthorized access attempts to audit log viewing and export functions.
- **FR-015**: Audit log records MUST be retained according to organizational policy with a minimum retention period of 1 year.
- **FR-016**: Audit log timestamps MUST be stored in UTC and any localized display or export labeling MUST preserve unambiguous time interpretation.
- **FR-017**: When filtered export result size exceeds 50,000 rows, the system MUST fail fast with a clear user-facing message instructing the admin to narrow filters, and MUST not generate a partial file.

### Key Entities *(include if feature involves data)*

- **Audit Log Entry**: A historical record of one tracked action, including actor, source IP, event timestamp, normalized action type code, target entity details, and human-readable summary.
- **Audit Filter Set**: A user-selected filter combination including user, keyword, date range, and action type that defines the displayed and exported subset.
- **Audit Export**: A generated file output (CSV or XLSX) containing the audit entries that match a specific filter set at export time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of tested tracked actions produce an audit log entry with all required fields populated.
- **SC-002**: Admin reviewers can locate a known target event using filters in under 2 minutes in at least 90% of validation trials.
- **SC-003**: 100% of export files (CSV and XLSX) match the active filter criteria used at export time.
- **SC-004**: 100% of non-admin access attempts to audit view or export are blocked.
- **SC-005**: At least 95% of admins successfully complete the activity investigation flow (find event and export evidence) on first attempt during acceptance validation.

## Assumptions

- Existing role and authentication controls in Enerlytix are reused to determine admin-only access.
- Audit logging scope includes authenticated mutating actions across the whole application, while viewer and export access remain admin-only in the Admin Panel.
- Audit log retention follows organizational policy and cannot be configured below 1 year.
- Audit timestamps are stored in UTC, while UI and exported views may be localized.
- Acceptance trial sample size is at least 20 validation runs for SC-002 and at least 20 admin investigation runs for SC-005.
- Admin users are expected to perform compliance review tasks from the Admin Panel, and non-admin users do not require audit log access.
- Exported files are intended for operational and compliance use and should preserve filter intent rather than full unfiltered history by default.
