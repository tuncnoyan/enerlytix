# Feature Specification: Usage Invoice Import

**Feature Branch**: `002-usage-invoice-import`

**Created**: 2026-06-30

**Status**: Draft

**Input**: User description: "I want to add more features to Enerlytix. Before getting started, please create a new branch.
In the current version, Enerlytix downloads all site/asset and supply/account lists from Xcelerate and import them to the database. In the second version, I want Enerlytix to download the half hourly and monthly consumption data, as well as costs from invoices on Xcelerate for the selected supply or supplies, then import them into the database. Those downloaded values should be stored in the database and can be updated if requested by the user. In this version I want Enerlytix to display them on a separate page as a table. No visualisation is required at this stage.
Sample code will also be uploaded for the technical planning.
Could you please create spec documents for this sprint, now?"

## Clarifications

### Session 2026-06-30

- Q: Which update behavior should Enerlytix use when records already exist for the same supply-period scope? -> A: Upsert per key: update existing matching records and insert only missing ones (no delete).
- Q: How should monthly consumption and invoice periods be represented for filtering and storage? -> A: Store source billing period dates plus canonical month key; filter by canonical month key.
- Q: Which timezone should define period boundaries and canonical month keys? -> A: Use UTC for all period boundaries and keys.
- Q: How should import runs behave when some supplies or periods fail? -> A: Continue-on-error with one automatic retry per failed supply or period before finalizing run results.
- Q: What data retention policy should apply to imported usage and invoice records? -> A: Configurable retention with a default of 36 months.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Import selected supply usage and invoice data (Priority: P1)

As an operations user, I can select one or more supplies and a reporting month, then run a data import so Enerlytix retrieves half-hourly consumption, monthly consumption, and invoice costs from Xcelerate and stores them in Enerlytix.

**Why this priority**: This is the core business value for this sprint and enables all downstream review and reporting activities.

**Independent Test**: Can be fully tested by selecting one or more known supplies and a month, running import, and confirming usage and invoice rows appear in storage for the required month windows.

**Acceptance Scenarios**:

1. **Given** at least one valid supply and a selected month, **When** the user runs import, **Then** Enerlytix stores half-hourly consumption records for the selected month and the same month in the previous year for each selected supply.
2. **Given** multiple supplies are selected, **When** the user runs import, **Then** the import includes all selected supplies and stores each supply's data separately.
3. **Given** a selected month, **When** the user runs import, **Then** Enerlytix stores monthly consumption records for the previous 24 months ending at the selected month and invoice cost records for the previous 12 months ending at the selected month.

---

### User Story 2 - Refresh previously imported values on demand (Priority: P2)

As an operations user, I can request an update for previously imported supplies so existing usage and invoice values can be refreshed from Xcelerate.

**Why this priority**: Data accuracy depends on being able to re-import when source values are corrected or newly published.

**Independent Test**: Can be tested by importing a supply, running a second import/update request, and confirming existing records are updated rather than duplicated for the same supply and period.

**Acceptance Scenarios**:

1. **Given** supply-period records already exist for a selected month window, **When** the user requests an update import, **Then** Enerlytix updates matching records with latest source values.
2. **Given** an update request contains periods not yet stored, **When** import runs, **Then** Enerlytix adds the missing records while preserving existing unrelated records.

---

### User Story 3 - View imported usage and invoice values in a dedicated table page (Priority: P3)

As an operations user, I can open a separate page, choose a month for reporting, and view imported usage and invoice values in table form for operational review.

**Why this priority**: Users need immediate visibility of imported values to verify imports and support business workflows.

**Independent Test**: Can be tested by opening the dedicated data page after import, selecting a month, and confirming table rows match stored values for selected supplies and required date windows.

**Acceptance Scenarios**:

1. **Given** imported records exist, **When** the user opens the dedicated data page and selects a month, **Then** the page shows a tabular list of half-hourly consumption, monthly consumption, and invoice cost values for the defined windows tied to that month.
2. **Given** no imported records exist for a selected supply scope, **When** the user opens the page, **Then** the page clearly indicates no data is available.

### Edge Cases

- Selected supplies include one valid and one invalid or inaccessible source record.
- Source returns only part of the expected time periods for half-hourly or monthly data.
- User selects February in a leap year and the prior-year month has different day counts.
- User selects a month at year boundary (for example January), requiring correct cross-year date range calculation.
- Source billing periods cross month boundaries and must map to one canonical month key used for filtering.
- Source timestamps include mixed timezone offsets and must normalize to UTC period boundaries consistently.
- Transient source failures occur for some supply-period requests and require exactly one automatic retry.
- Retention cutoff changes must not break month-window imports or table visibility for still-retained records.
- Duplicate import requests are triggered for the same supply and overlapping time periods.
- Invoice cost values are missing for some periods while consumption values are present.
- Very large half-hourly result sets for multi-supply imports require pagination or chunked processing for stable completion.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to select one or multiple supplies for usage and invoice import.
- **FR-002**: System MUST require users to select a reporting month for import and table display workflows.
- **FR-003**: System MUST retrieve half-hourly consumption data for each selected supply for both the selected month and the same calendar month one year earlier.
- **FR-004**: System MUST retrieve monthly consumption data for each selected supply for the previous 24 months ending with the selected month.
- **FR-005**: System MUST retrieve invoice cost data for each selected supply for the previous 12 months ending with the selected month.
- **FR-006**: System MUST store imported half-hourly consumption, monthly consumption, and invoice cost values in Enerlytix data storage with clear linkage to supply, selected reporting month, source period, and canonical month key.
- **FR-007**: System MUST support user-initiated update requests using upsert behavior: update matching records and insert only missing records for the selected month windows.
- **FR-008**: System MUST prevent duplicate records by enforcing one record per supply and source period within each usage or invoice record type when running repeated imports.
- **FR-009**: System MUST preserve an auditable import outcome for each run, including selected month, start time, completion status, and affected supply count.
- **FR-010**: System MUST provide a separate page that displays imported values in a table format.
- **FR-011**: Users MUST be able to distinguish value type (half-hourly consumption, monthly consumption, invoice cost), selected month context, canonical month key, source period dates, and associated supply within the table page.
- **FR-012**: System MUST gracefully handle partial import failures using continue-on-error behavior and recording failed supplies or periods without discarding successfully imported records.
- **FR-013**: System MUST present a clear empty-state message on the separate page when no imported values are available.
- **FR-014**: For monthly consumption and invoice data, system MUST persist source billing period start and end dates and derive a single canonical month key used for month-based filtering.
- **FR-015**: System MUST normalize period boundaries and canonical month keys to UTC for import, storage, deduplication, and table filtering.
- **FR-016**: System MUST perform one automatic retry for each failed supply-period fetch before marking that unit as failed in final run results.
- **FR-017**: System MUST apply configurable retention for imported usage and invoice data with a default retention of 36 months.

### Key Entities *(include if feature involves data)*

- **Supply Selection**: User-selected supply scope used to initiate import; includes supply identifier and optional grouping context.
- **Reporting Month Selection**: User-selected month that drives all import windows and table display context.
- **Half-Hourly Consumption Record**: Consumption value tied to a single supply and half-hour interval.
- **Monthly Consumption Record**: Aggregated consumption value tied to a single supply and month.
- **Invoice Cost Record**: Cost value tied to a single supply and billing period.
- **Period Keying**: Shared metadata containing source billing period start, source billing period end, and canonical month key used for filtering.
- **Import Run**: A single user-triggered import or update request with reporting month, run timestamp, status, and result counts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 95% of standard import runs for up to 20 selected supplies complete successfully within 10 minutes while covering both half-hourly months, 24 months of monthly consumption, and 12 months of invoice costs.
- **SC-002**: 100% of successful import runs store records that can be viewed on the dedicated table page without manual intervention.
- **SC-003**: For repeated import requests on the same supply-period scope, duplicate rate remains at 0% while latest source values are reflected after update.
- **SC-004**: In user acceptance testing, at least 90% of test users can locate and verify imported usage and invoice values on the dedicated page within 2 minutes.

## Assumptions

- Existing supply selection mechanisms from the current Enerlytix workflow will be reused for this sprint.
- Users choose one reporting month per import/view action, and that month is the anchor for all required time windows.
- Reporting month interpretation and all derived period boundaries use UTC semantics.
- Retry policy is fixed at one automatic retry per failed supply-period request in this sprint.
- Retention period is configurable, with a default of 36 months unless explicitly changed by authorized configuration.
- User access permissions already in place for supply data views also apply to the new table page unless future stories change this.
- Visualization and charting are explicitly out of scope; table-based display only is required.
- Import scope for this sprint is limited to half-hourly consumption, monthly consumption, and invoice costs from Xcelerate.
- Sample code to be provided later will inform implementation planning details, but does not change this sprint-level scope.

