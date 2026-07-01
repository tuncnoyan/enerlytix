# Implementation Plan: Usage Invoice Import

**Branch**: `002-usage-invoice-import` | **Date**: 2026-06-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-usage-invoice-import/spec.md`

## Summary

Extend Enerlytix to download usage and invoice consumption data from Xcelerate's `/consumption` and `/invoices` endpoints (half-hourly, monthly consumption, and invoice costs) for user-selected supplies and reporting months, store in Django models with canonical month keys and source period metadata, and display on a dedicated table page. All period boundaries normalize to UTC; import runs use upsert strategy; partial failures trigger one automatic retry per supply-period; imported data expires after configurable 36-month default retention.

## Technical Context

**Language/Version**: Python 3.x (Django 3.x+ based on existing project)

**Primary Dependencies**: Django ORM, `requests` library (Xcelerate API), `pandas` (existing workflows), Django REST Framework (API endpoints)

**Storage**: Django ORM with SQLite (dev) or PostgreSQL (production); new models: `HalfHourlyConsumption`, `MonthlyConsumption`, `InvoiceCost`, `ImportRun`

**Testing**: Django test framework (unittest + pytest based on existing `django_app/sitesync/tests/`)

**Target Platform**: Windows-native development; Docker deployment (Linux server per constitution)

**Project Type**: Web service (extends existing Enerlytix site/supply sync with usage/invoice import + display)

**Performance Goals**: 95% of import runs complete within 10 minutes for up to 20 supplies covering both half-hourly months, 24 months monthly consumption, and 12 months invoice costs

**Constraints**: No admin privileges for local operation; data security and audit logging required; upsert semantics to prevent duplicates; one automatic retry per failed supply-period

**Scale/Scope**: Single feature sprint targeting consumption/invoice data fetch and table display; no visualizations; table-only UI

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

PASS **Windows-Native Platform Alignment**: Existing Django+SQLite architecture already aligns.

PASS **Least-Privilege Development & Operations**: No elevated privileges needed for import operations; data fetch and storage run under standard user.

PASS **Data Security and Database Isolation**: Imported records stored in authenticated database; API keys managed via `.env`; sensitive timestamps and account IDs audited.

PASS **Approval-Governed Production Operations**: Deployment follows existing approval gates; data retention configs subject to change control.

PASS **Containerized Maintainability & Observability**: Existing Docker setup; new models and endpoints follow established patterns.

**GATE RESULT**: PASS - No constitution violations identified.

---

## Phase 0: Research Findings

### Xcelerate API Behavior

**Endpoint**: `https://api.etainabl.com/2.0/consumption`

**Parameters**:
- `accountId` (required): supply/account identifier
- `startDate`, `endDate` (ISO 8601): date window
- `granularity` (required): `monthly`, `halfhourly`
- `source` (optional): `combined`, `hh`, `invoice`, `reading`

**Response Structure**:
```
{
  "startDate": "2025-01-01T00:00:00.000Z",
  "endDate": "2026-01-01T00:00:00.000Z",
  "granularity": "monthly",
  "consumption": <total>,
  "data": [
    {
      "startDate": "2025-01-01T00:00:00.000Z",
      "endDate": "2025-02-01T00:00:00.000Z",
      "date": "2025-01",
      "consumption": <value>,
      "combinedBreakdown": { "hh": <x>, "invoice": <y> },
      "sources": ["hh", "invoice"]
    }
  ]
}
```

**Key Findings**:
- Monthly data returns canonical `date` field (YYYY-MM format) alongside source start/end timestamps
- `combinedBreakdown` breaks consumption by source (hh, reading, invoice, custom)
- Half-hourly responses can return large datasets (potentially 48 values per day x ~730 days = 35k+ records for 24-month window)
- Pagination not required but response size dictates streaming strategy for half-hourly imports
- API uses ISO 8601 UTC timestamps consistently

**Invoices Endpoint**: `https://api.etainabl.com/2.0/invoices?accountId=<id>`
- Returns paginated list of invoice records (limit/skip parameters)
- Each invoice has date, cost, and period metadata
- Total count provided; need to paginate through all records for 12-month window

### Retry Strategy

**Decision**: Implement exponential backoff with one automatic retry (as per clarification):
- First attempt on initial request
- If fails (timeout, 5xx, transient error): wait 2-5 seconds
- Single retry attempt
- If still fails: record as failed in ImportRun, continue with other supplies/periods

**Rationale**: Balances reliability (catches transient glitches) with avoiding indefinite hangs.

### UTC Period Boundaries

**Decision**: All canonical month keys stored as `YYYY-MM` (e.g., "2025-01") in UTC.
- Month boundaries: first day 00:00:00 UTC through last day 23:59:59 UTC
- Canonical month key derived from period end date rounded down to month start in UTC
- Example: Invoice period 2025-01-15 to 2025-02-14 maps to canonical month "2025-02" (includes most of February)

**Rationale**: Aligns with billing periods and monthly reporting; consistent with spec requirement for UTC timezones.

### Upsert and Deduplication

**Decision**: Use Django `update_or_create()` with unique key (supply_id, source_period_start, source_period_end):
```python
obj, created = Model.objects.update_or_create(
  defaults={'consumption': value, 'canonical_month_key': key},
  supply_id=supply_id,
  source_period_start=start,
  source_period_end=end
)
```

**Rationale**: Enforces one canonical record per (supply, period) within each data table; updates reflect latest source values; no duplicate records after repeated imports.

Because half-hourly, monthly, and invoice records are stored in separate tables, data type is implicit in table selection.

### Data Retention

**Decision**: Configurable retention (default 36 months) via Django setting:
```python
# settings.py
CONSUMPTION_RETENTION_MONTHS = 36
```

Management command runs nightly:
```
python manage.py cleanup_expired_consumption
```

Removes records where `import_date + retention_period < now()`.

**Rationale**: Balances data minimization with compliance; 36-month default covers typical billing audit requirements.

---

## Phase 1: Design Artifacts

### Data Model

**New Django Models** (in `sitesync/models.py`):

1. **ImportRun**
   - `id` (UUID)
  - `selected_supply_ids` (JSONField: list of requested supply IDs)
   - `reporting_month` (CharField, YYYY-MM format)
   - `status` (CharField: pending, in_progress, success, partial_failure, failed)
   - `started_at` (DateTimeField)
   - `completed_at` (DateTimeField, nullable)
  - `affected_supply_count` (IntegerField)
   - `records_imported` (IntegerField)
   - `records_failed` (IntegerField)
   - `retry_count` (IntegerField)
   - `error_details` (JSONField, nullable)
   - `created_at`, `updated_at` (auto timestamps)

2. **HalfHourlyConsumption**
   - `id` (UUID)
   - `import_run` (ForeignKey to ImportRun)
   - `supply` (ForeignKey to Supply)
   - `canonical_month_key` (CharField, YYYY-MM, indexed)
   - `source_period_start` (DateTimeField, UTC)
   - `source_period_end` (DateTimeField, UTC)
   - `consumption` (DecimalField)
   - `created_at`, `updated_at` (auto timestamps)
   - **Unique constraint**: (supply, source_period_start, source_period_end)

3. **MonthlyConsumption**
   - `id` (UUID)
   - `import_run` (ForeignKey to ImportRun)
   - `supply` (ForeignKey to Supply)
   - `canonical_month_key` (CharField, YYYY-MM, indexed)
   - `source_period_start` (DateTimeField, UTC)
   - `source_period_end` (DateTimeField, UTC)
   - `consumption` (DecimalField)
   - `breakdown` (JSONField: {hh, reading, invoice, custom})
   - `sources` (JSONField: list of sources)
   - `created_at`, `updated_at` (auto timestamps)
   - **Unique constraint**: (supply, source_period_start, source_period_end)

4. **InvoiceCost**
   - `id` (UUID)
   - `import_run` (ForeignKey to ImportRun)
   - `supply` (ForeignKey to Supply)
   - `canonical_month_key` (CharField, YYYY-MM, indexed)
   - `source_period_start` (DateTimeField, UTC)
   - `source_period_end` (DateTimeField, UTC)
   - `cost` (DecimalField)
   - `invoice_metadata` (JSONField: date, number, status)
   - `created_at`, `updated_at` (auto timestamps)
   - **Unique constraint**: (supply, source_period_start, source_period_end)

**Indexing Strategy**:
- `canonical_month_key` for fast month-based filtering on tables
- (supply, canonical_month_key) composite for supply+month queries
- (import_run) for audit/history lookups

### API Contracts

**POST /api/consumption-import/**

**Request**:
```json
{
  "supply_ids": ["6584fdd1c9ec42556202eaa2", "..."],
  "reporting_month": "2026-05"
}
```

**Response**:
```json
{
  "import_run_id": "uuid",
  "status": "in_progress",
  "supplies_count": 2,
  "started_at": "2026-06-30T12:00:00Z"
}
```

**Errors**:
- 400: Invalid month format or missing supplies
- 401: Unauthorized
- 409: Another import already running for same supplies/month

**GET /api/consumption-display/?reporting_month=2026-05&supply_id=...&data_type=monthly**

**Response**:
```json
{
  "reporting_month": "2026-05",
  "records": [
    {
      "id": "uuid",
      "supply_id": "...",
      "data_type": "monthly",
      "source_period_start": "2025-01-01T00:00:00Z",
      "source_period_end": "2025-02-01T00:00:00Z",
      "consumption": 2078.115,
      "canonical_month_key": "2025-01"
    }
  ],
  "total_records": 145
}
```

### Source Code Structure

```text
django_app/sitesync/
|- models.py                           # NEW: ImportRun, HalfHourlyConsumption, MonthlyConsumption, InvoiceCost
|- api_client.py                       # UPDATE: add consumption() and invoices() methods
|- services.py                         # NEW: ConsumptionImportService class
|- views.py                            # UPDATE: add import_consumption and display_consumption views
|- serializers.py                      # UPDATE: add consumption serializers
|- urls.py                             # UPDATE: add /api/consumption-* routes
|- admin.py                            # UPDATE: register new models
|- management/commands/
|  `- cleanup_expired_consumption.py   # NEW: retention policy enforcement
`- tests/
   |- test_consumption_models.py
   |- test_consumption_import.py
   |- test_consumption_api.py
   `- test_consumption_display.py

templates/sitesync/
`- consumption_display.html            # NEW: table page template
```

### Complexity Tracking

| Consideration | Approach | Rationale |
|---|---|---|
| Period keying (source dates + canonical month) | Add `canonical_month_key` + `source_period_start`, `source_period_end` to models | Allows month-based filtering while preserving source billing details |
| UTC normalization across boundaries | All timestamps stored in UTC; canonical month always YYYY-MM format | Avoids timezone confusion at month boundaries |
| Upsert semantics for repeated imports | Django `.update_or_create()` keyed on (supply, source_period_start, source_period_end) in each data table | Prevents duplicates while allowing refresh |
| Retry policy (one automatic retry) | Implement in ConsumptionImportService with exponential backoff | Handles transient source failures |
| Data retention (configurable, 36-month default) | Add `retention_months` setting + management command | Balances data minimization with compliance |
| Pagination for large datasets | Half-hourly streaming/chunked processing | Prevents memory exhaustion |

---

## Phase 1: Quickstart & Validation

### Scenario 1: Successful Single Supply Import

**Setup**: Supply ID `6584fdd1c9ec42556202eaa2`, reporting month `2026-05`

**Command**:
```bash
curl -X POST http://localhost:8000/api/consumption-import/ \
  -H "Content-Type: application/json" \
  -d '{"supply_ids": ["6584fdd1c9ec42556202eaa2"], "reporting_month": "2026-05"}'
```

**Expected Outcome**:
- Import run created with status `in_progress`
- Fetches half-hourly data for May 2026 and May 2025 from Xcelerate
- Fetches monthly consumption for Jun 2024 - May 2026
- Fetches invoice data for Jun 2025 - May 2026
- Each stored record uses canonical_month_key derived from its own source period in UTC (YYYY-MM). Reporting month controls which windows are imported and displayed, not a single shared key value.
- Import run marked as `success` after completion
- Records viewable on display page immediately

**Validation**:
```python
# In Django shell:
from sitesync.models import ImportRun, HalfHourlyConsumption, MonthlyConsumption, InvoiceCost

run = ImportRun.objects.get(reporting_month='2026-05')
assert run.status == 'success'
assert HalfHourlyConsumption.objects.filter(import_run=run).count() > 0
assert MonthlyConsumption.objects.filter(import_run=run).count() == 24
assert InvoiceCost.objects.filter(import_run=run).count() == 12
```

### Scenario 2: Upsert on Repeated Import

**Setup**: Run import twice with same supply and month

**First Run**:
- Records created successfully

**Second Run** (same parameters):
- Call `/api/consumption-import/` again with identical supply_ids and reporting_month
- System fetches fresh data from Xcelerate
- `.update_or_create()` updates all matching records with new consumption values
- No duplicate records created
- ImportRun records both attempts with different IDs

**Validation**:
```python
# After second import:
runs = ImportRun.objects.filter(reporting_month='2026-05')
assert runs.count() == 2  # Two separate import runs

hh_records = HalfHourlyConsumption.objects.filter(canonical_month_key='2026-05')
# Count unchanged because upsert updated, not inserted
assert hh_records.count() == <first_run_count>

# Latest update timestamp reflects second import
assert hh_records.first().updated_at > runs.first().completed_at
```

### Scenario 3: Display Table with Filters

**Setup**: Import complete; navigate to display page

**Request**:
```
GET /consumption-display/?reporting_month=2026-05&supply_id=6584fdd1c9ec42556202eaa2&data_type=monthly
```

**Expected Output**:
- HTML table showing:
  - Columns: Date Range | Consumption | Data Type | Last Updated
  - 24 monthly consumption rows (Jun 2024 - May 2026)
  - Rows sorted by source_period_start descending (most recent first)
- No errors; page loads in <2 seconds

**Validation**:
```python
# Programmatic API check:
response = client.get('/api/consumption-display/?reporting_month=2026-05&data_type=monthly')
assert response.status_code == 200
assert len(response.json()['records']) == 24
assert response.json()['records'][0]['consumption'] > 0
```

### Scenario 4: Partial Failure with Retry

**Setup**: Supply A succeeds; Supply B fails on first attempt (timeout or transient error)

**Expected Behavior**:
- ImportRun starts for both supplies
- Supply A completes successfully
- Supply B fails, triggers one automatic retry after 2-5 second backoff
- If Supply B still fails: marked as failed in ImportRun, but Supply A records persisted
- ImportRun status set to `partial_failure`
- Error log includes Supply B failure details

**Validation**:
```python
run = ImportRun.objects.get(id=<import_run_id>)
assert run.status == 'partial_failure'
assert run.records_imported > 0
assert run.records_failed > 0
assert 'Supply B' in run.error_details  # Contains failure reason
```

### Scenario 5: Data Retention Cleanup

**Setup**: Records older than 36 months exist in database

**Command**:
```bash
python manage.py cleanup_expired_consumption
```

**Expected Outcome**:
- Records created >36 months ago are deleted
- Recent records unaffected
- Management command logs number of records cleaned up

**Validation**:
```python
from django.utils import timezone
from datetime import timedelta

# Create old record
old_time = timezone.now() - timedelta(days=37*30)
old_record = HalfHourlyConsumption.objects.create(
  supply_id=...,
  canonical_month_key='2023-01',
  consumption=100.0,
  created_at=old_time
)

# Run cleanup
call_command('cleanup_expired_consumption')

# Verify deletion
assert not HalfHourlyConsumption.objects.filter(id=old_record.id).exists()
```

---

## Post-Design Constitution Re-check

PASS **Windows-Native Platform Alignment**: Implementation uses Django ORM with standard database libraries; no platform-specific assumptions.

PASS **Least-Privilege Development & Operations**: All operations (import, display, cleanup) run under authenticated user context; no admin elevation required.

PASS **Data Security and Database Isolation**: New models integrate with existing Django authentication; API keys stored in `.env`; sensitive periods and account IDs audited via ImportRun logs.

PASS **Approval-Governed Production Operations**: Data retention config (36-month default) can be changed via Django settings; retention cleanup runs on schedule without manual approval per sprint scope.

PASS **Containerized Maintainability & Observability**: New code follows existing sitesync patterns; ImportRun model provides audit trail; Docker deployment unchanged.

**GATE RESULT**: PASS - Design complies with all constitution principles.

---

## Next Steps

**Phase 2**: Execute `/speckit.tasks` command to generate detailed task list for implementation.

**Artifacts Generated This Phase**:
- PASS plan.md (this file)
- PASS research.md (embedded in Phase 0 section)
- PASS data-model.md (embedded in Phase 1 section)
- PASS contracts/ (embedded in Phase 1 section)
- PASS quickstart.md (embedded in Phase 1 section)

**Ready for**: `/speckit.tasks` to generate implementation task breakdown

---

## Implementation Validation Log

Date: 2026-07-01

- Implemented core schema, API routes, service orchestration, display page, and retention command.
- Generated migration `0003_halfhourlyconsumption_importrun_invoicecost_and_more.py`.
- Completed static checks for updated Django modules (`models.py`, `services.py`, `views.py`, `serializers.py`, URLs) with no reported errors.
- End-to-end import execution and benchmark/UAT evidence are pending integrated environment execution with valid upstream API credentials and seeded test supplies.


