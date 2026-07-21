# Enerlytix Django App

## Setup

- Install the Python dependencies from `requirements.txt`.
- Configure environment variables in `.env`.
- Run migrations from the `django_app/` directory.
- Start the app with `python manage.py runserver`.

## Runtime pages

- Site dashboard at `/`
- Manual refresh endpoint at `/sync/`
- Supply panel endpoint at `/supplies/`
- Settings page at `/settings/`
- Consumption display page at `/consumption-display/`
- Report visuals and export page at `/report/`

## Report cover pages

- The report editor includes three integrated cover pages:
	- Front cover page 1 (editable fields)
	- Front cover page 2 (editable Scope and Contents)
	- Back cover page (static image)
- Front cover page 1 editable defaults:
	- Site title from selected site
	- Report month title in `[Month Year] Energy Report` format
	- Date in `DD MMMM YYYY` format
	- Optional client logo area
- Upload validation:
	- Front background: JPG/JPEG/PNG/WebP up to 10 MB
	- Client logo: PNG/JPG/SVG up to 2 MB
- Cover sequence is consistent across draft, final, PDF, and PPTX exports.
- In PPTX exports, front-cover text fields remain editable.

## Usage and invoice import

- Trigger import with `POST /api/consumption-import/`.
- The import service fetches:
	- Half-hourly: reporting month and prior-year same month
	- Monthly: previous 24 months
	- Invoices: previous 12 months
- All records are stored with UTC source period metadata and canonical month key (`YYYY-MM`).
- Re-running import performs upsert per table on `(supply, source_period_start, source_period_end)` to prevent duplicates.
- One automatic retry is applied for transient per-period failures, and run outcomes are audited in `ImportRun`.

## Retention cleanup

- Default retention is 36 months (`CONSUMPTION_RETENTION_MONTHS`).
- Run cleanup manually:

```bash
python manage.py cleanup_expired_consumption
```

- Command removes expired `HalfHourlyConsumption`, `MonthlyConsumption`, and `InvoiceCost` records.

## Configuration

- Secrets must come from environment variables.
- Production deployments require approval.
- Database transport should use SSL where supported.
- Import configuration variables:
	- `CONSUMPTION_RETENTION_MONTHS`
	- `CONSUMPTION_IMPORT_RETRY_COUNT`
	- `CONSUMPTION_IMPORT_RETRY_BACKOFF_SECONDS`
	- `CONSUMPTION_HALFHOURLY_MONTHS`
	- `CONSUMPTION_MONTHLY_MONTHS`
	- `CONSUMPTION_INVOICE_MONTHS`
