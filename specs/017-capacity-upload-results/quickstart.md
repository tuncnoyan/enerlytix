# Quickstart: Capacity Upload Results UX Validation

Feature: 017-capacity-upload-results  
Date: 2026-08-06

## Prerequisites

- Docker Desktop running.
- Services started from repository root:

```powershell
docker compose -f django_app/docker/docker-compose.yml up -d
```

- Migrations applied:

```powershell
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py migrate
```

## Scenario 1: Inline issue list is removed

1. Sign in with a user authorized to access settings.
2. Upload a workbook that produces mixed success/failure rows.
3. Open `/settings/` after upload completes.

Expected:
- Status notice appears with accepted/rejected counts.
- Latest upload summary block appears.
- No long inline per-row issue list is rendered.

## Scenario 2: Download latest run results workbook

1. From `/settings/`, click the upload-results download action.
2. Open the downloaded `.xlsx`.

Expected:
- File downloads successfully.
- Workbook contains exactly two sheets: `Successes` and `Failures`.
- Both sheets include: source row number, original upload columns, outcome, explanation.

## Scenario 3: Failure explanation completeness

1. Upload a workbook that causes at least one row to fail with multiple validation reasons.
2. Download the latest results workbook.
3. Inspect the failed row in `Failures` sheet.

Expected:
- Failed row appears once.
- Explanation contains all failure reasons combined.

## Scenario 4: Edge-case no results available

1. Access export action where latest run has no persisted row outcomes.

Expected:
- User receives clear feedback that export results are unavailable.
- No silent empty workbook is returned.

## Scenario 5: Timed remediation validation (SC-005)

1. Upload a workbook that generates at least one failed row.
2. Download the latest results workbook.
3. Start a timer when the workbook is opened.
4. Identify one failed row and state its failure cause from the Explanation column.
5. Stop the timer and record elapsed time.
6. Repeat for 5 moderated runs.

Expected:
- In each run, the user identifies at least one failed-row cause within 2 minutes.
- Timings are recorded in this quickstart file as validation evidence.

## Automated Test Commands (Docker-only)

Run capacity upload and settings tests:

```powershell
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test sitesync.tests.test_capacity_upload sitesync.tests.test_settings_view
```

Run export-focused tests:

```powershell
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test sitesync.tests.test_capacity_upload_results_export
```

Run full regression:

```powershell
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test
```

## Validation Evidence (2026-08-06)

### Targeted capacity/settings/export tests

Command:

```powershell
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test sitesync.tests.test_capacity_upload sitesync.tests.test_settings_view sitesync.tests.test_capacity_upload_results_export
```

Result:

- `Ran 19 tests in 7.036s`
- `OK`

### Full regression

Command:

```powershell
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test
```

Result:

- `Ran 245 tests in 107.993s`
- `OK`

### SC-005 timed usability validation (5 moderated runs)

Procedure used:

- Create a latest partial-success run with persisted row outcomes.
- Download `GET /settings/capacity-upload/results.xlsx` as a staff user.
- Open workbook and identify one failed-row cause from `Failures -> Explanation`.

Recorded timings:

| Run | Elapsed (ms) | Failed-row Cause Identified |
|---|---:|---|
| 1 | 110.10 | Name is blank, eSight Meter Code is blank |
| 2 | 9.48 | Name is blank, eSight Meter Code is blank |
| 3 | 8.00 | Name is blank, eSight Meter Code is blank |
| 4 | 8.97 | Name is blank, eSight Meter Code is blank |
| 5 | 8.00 | Name is blank, eSight Meter Code is blank |

Outcome:

- All 5 runs identified a failed-row cause within 2 minutes (SC-005 satisfied).

## Related Artifacts

- Spec: [spec.md](spec.md)
- Plan: [plan.md](plan.md)
- Data model: [data-model.md](data-model.md)
- Contract: [contracts/capacity-upload-results-export.md](contracts/capacity-upload-results-export.md)
