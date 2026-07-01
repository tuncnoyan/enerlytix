# Quickstart Validation: Usage Invoice Import

## Preconditions

- Django migrations applied through `0003_halfhourlyconsumption_importrun_invoicecost_and_more`.
- Valid `ETAINABL_API_KEY` configured in environment.
- Target supplies synchronized and available in `Supply` table.

## Scenario A: Trigger Import

Request:

```http
POST /api/consumption-import/
Content-Type: application/json

{
  "supply_ids": ["6584fdd1c9ec42556202eaa2"],
  "reporting_month": "2026-05",
  "refresh_mode": true
}
```

Expected:

- `ImportRun` created.
- Response includes `import_run_id`, run status, counts, and auditable `outcome_details`.
- Records upserted into `HalfHourlyConsumption`, `MonthlyConsumption`, and `InvoiceCost`.

## Scenario B: Display Imported Data

Request:

```http
GET /api/consumption-display/?reporting_month=2026-05&data_type=monthly
```

Expected:

- Response returns table-ready records.
- `total_records` matches filtered data.
- Rows include source period and canonical month key.

## Scenario C: Retention Cleanup

Command:

```bash
python manage.py cleanup_expired_consumption
```

Expected:

- Records older than configured retention window are deleted.
- Command prints per-table deletion counts.

## UAT Protocol for SC-004

Target: 90% of users can locate and verify imported values within 2 minutes.

Protocol:

1. Prepare a tenant with at least 3 supplies and imported records for one reporting month.
2. Provide participants with task: "Find monthly value for supply X in reporting month Y and confirm source period."
3. Start timer when participant opens `/consumption-display/`.
4. Stop timer when participant verbally confirms value and period.
5. Record completion time and success/failure in UAT log.
6. Compute pass rate and average completion time.

Evidence template:

| Participant | Success | Time (seconds) | Notes |
|-------------|---------|----------------|-------|
| UAT-01 | TBD | TBD | |
| UAT-02 | TBD | TBD | |
| UAT-03 | TBD | TBD | |

## Timing Benchmark Protocol

Target: 95% of imports for up to 20 supplies complete within 10 minutes.

Protocol:

1. Select 20 representative supply IDs.
2. Trigger imports for fixed reporting month in 20 repeated runs.
3. Capture `started_at` and `completed_at` from `ImportRun`.
4. Compute run duration in seconds and percentile distribution.
5. Mark pass when p95 duration <= 600 seconds.

Evidence template:

| Run | Supplies | Duration (seconds) | Status |
|-----|----------|--------------------|--------|
| 1 | 20 | TBD | TBD |
| 2 | 20 | TBD | TBD |
| ... | ... | ... | ... |

Result: Pending execution in integrated environment with valid upstream API connectivity.
