# API Documentation

## Site list

- `GET /`
- Returns the searchable site dashboard.

## Manual sync

- `POST /sync/`
- Triggers a manual refresh from the Etainabl API.
- Success redirects back to the dashboard.
- Errors return JSON in the form:

```json
{
  "error": {
    "message": "Unable to complete sync",
    "details": "..."
  }
}
```

## Supplies by site

- `GET /supplies/?site_id=<id>`
- Returns the supply panel HTML for a selected site.

## Settings

- `GET /settings/`
- `POST /settings/`
- Loads and saves the runtime Etainabl configuration.

### Available capacity upload via Settings

- Route: `POST /settings/`
- Content type: `multipart/form-data`
- Required file field: `capacity_upload_file` (`.xlsx` only)
- Action marker: `capacity_upload_submit=1`

Required columns in uploaded workbook:

- `Name`
- `eSight Meter Code`
- `Av Cap (kVA)`

Behavior:

- Performs partial import for row-level validation failures.
- Valid rows are upserted by normalized `eSight Meter Code`.
- When an incoming row matches an existing normalized `eSight Meter Code`, the stored `Name` and `Av Cap (kVA)` are replaced with the latest uploaded values.
- Invalid rows are skipped and returned as row-level messages.
- Blank, non-numeric, or negative `Av Cap (kVA)` values are rejected at row level.
- Existing records not referenced by incoming keys remain unchanged.

Rendered response context includes:

- `capacity_upload_status` (`success`, `partial_success`, `failed`)
- `capacity_upload_total_rows`
- `capacity_upload_accepted_rows`
- `capacity_upload_rejected_rows`
- `capacity_upload_errors` (row-level messages)

## Consumption import

- `POST /api/consumption-import/`
- Triggers usage and invoice import for selected supplies and reporting month.

Request payload:

```json
{
  "supply_ids": ["6584fdd1c9ec42556202eaa2"],
  "reporting_month": "2026-05",
  "refresh_mode": true
}
```

Response payload:

```json
{
  "import_run_id": "2bf3cfc6-a264-4cc9-8bfd-565e2a8f8507",
  "status": "success",
  "supplies_count": 1,
  "records_imported": 305,
  "records_failed": 0,
  "retry_count": 0,
  "error_details": {},
  "outcome_details": []
}
```

## Consumption display API

- `GET /api/consumption-display/?reporting_month=YYYY-MM&data_type=monthly&supply_id=<external_id>`
- Returns table-ready imported records for selected filters.

Response payload:

```json
{
  "reporting_month": "2026-05",
  "data_type": "monthly",
  "total_records": 24,
  "records": [
    {
      "id": "9aeeea50-62df-4f45-ba11-96ab190f6081",
      "supply_id": 12,
      "supply_external_id": "6584fdd1c9ec42556202eaa2",
      "supply_name": "Main Meter",
      "data_type": "monthly",
      "source_period_start": "2025-01-01T00:00:00Z",
      "source_period_end": "2025-02-01T00:00:00Z",
      "canonical_month_key": "2025-02",
      "value": "2078.115000"
    }
  ]
}
```

## Consumption display page

- `GET /consumption-display/`
- Renders the dedicated usage/invoice table UI with month, supply, and data-type filters.

## Import run audit detail

- `GET /api/import-runs/<import_run_id>/`
- Returns full persisted audit details for a single import run.
- Requires authentication.
