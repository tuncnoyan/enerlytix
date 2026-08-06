# Quickstart Validation Guide: Saved Reports Search and Filters (Docker Runtime)

Feature: 015-report-search-filters  
Date: 2026-08-06

## Prerequisites

1. Docker Desktop is installed and running.
2. Repository `.env` is present and valid for the Django app.
3. Docker compose file is available at `django_app/docker/docker-compose.yml`.
4. You can sign in with at least one user that has report visibility.

## Container Startup and Migration

Run all commands from repository root.

```powershell
docker compose -f django_app/docker/docker-compose.yml up -d --build
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py migrate
```

Optional health check:

```powershell
docker compose -f django_app/docker/docker-compose.yml ps
```

## Automated Validation Commands (Docker Only)

Run feature-relevant tests in containerized environment:

```powershell
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test sitesync.tests.test_saved_reports_view sitesync.tests.test_saved_reports_ownership_listing sitesync.tests.test_saved_reports_team_context --verbosity 2
```

Run broader regression when needed:

```powershell
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test --verbosity 2
```

## Manual Validation Scenarios

### Scenario 1: Site and User searches

1. Open `/reports/` as an authenticated user with visible reports.
2. Enter a partial site string in Site search.
3. Enter a partial username in User search.

Expected:
- Results match case-insensitive contains rules.
- User search checks OWNER, LAST EDITED BY, and VALIDATOR columns using a single input.
- Combined Site + User criteria are both enforced.

### Scenario 2: Reporting month range and inclusive boundaries

1. Select Start Month and End Month.
2. Verify rows include boundary months.
3. Set Start Month later than End Month.

Expected:
- Valid range returns rows where `Start Month <= reporting_month <= End Month`.
- Invalid range returns a clear correction prompt and no misleading row set.

### Scenario 3: Status checkbox defaults and empty-selection behavior

1. Refresh `/reports/` with no query parameters.
2. Confirm default selected checkboxes:
   - Report Status: Draft + Final
   - Validation Status: Draft + Awaiting validation + Validated
3. Untick all options in either status group.

Expected:
- Default load has all statuses selected.
- Fully unticked status group is allowed.
- Empty state is shown with zero matching rows.

### Scenario 4: Combined restrictive filters empty state

1. Apply multiple restrictive filters (site + user + month range + statuses) that intentionally produce no records.
2. Remove one filter at a time.

Expected:
- Explicit empty-state message appears when no matches exist.
- Results recalculate immediately and consistently as criteria are adjusted.

## Evidence Capture

For planning sign-off, capture:
- Terminal output of Docker test command(s).
- Screenshot(s) of default filter state and empty-state rendering.
- One example URL/query combination proving combined criteria behavior.
