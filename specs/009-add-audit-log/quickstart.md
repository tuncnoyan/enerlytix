# Quickstart: Admin Audit Log (Docker Runtime)

## Prerequisites

- Docker Desktop is installed and running.
- Repository `.env` exists (copy from `.env.example` if needed).
- Docker Compose file: `django_app/docker/docker-compose.yml`.

## 1. Start the Containerized Stack

From repository root:

```bash
docker compose -f django_app/docker/docker-compose.yml up -d --build
```

Verify services:

```bash
docker compose -f django_app/docker/docker-compose.yml ps
```

## 2. Apply Migrations in Container

```bash
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py migrate
```

## 3. Create/Use Admin Account

```bash
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py createsuperuser
```

## 4. Validate Core Audit Logging

Scenario:
1. Sign in as admin.
2. Perform tracked mutating actions (for example create report, approve report, delete test user).
3. Attempt one denied security-relevant action using a non-admin account (for example access an admin-only audit URL).
4. Open audit viewer at `/panel/audit-logs/`.

Expected:
- Success events appear with actor, IP, UTC timestamp, normalized action type, target, and message.
- Denied/failed security-relevant attempt appears as an event.

## 5. Validate Filters

Apply each filter and combinations:
- user
- keyword
- date range (`start`, `end`)
- action type

Expected:
- Filtered rows match criteria exactly.
- One-sided date filters (start-only/end-only) are accepted.

## 6. Validate Export Behavior

From the filtered view, export:
- CSV (`/panel/audit-logs/export.csv`)
- XLSX (`/panel/audit-logs/export.xlsx`)

Expected:
- Both files contain the same row set as filtered view.
- Empty-result export returns headers with no data rows.

## 7. Run Automated Tests in Docker (Required)

Run tests inside web container only:

```bash
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test --verbosity 2
```

Optionally scope to audit tests as they are added:

```bash
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test sitesync.tests.test_audit_log --verbosity 2
```

Executed foundational audit validation command:

```bash
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test sitesync.tests.test_audit_log_entry_contract sitesync.tests.test_audit_logging_events --verbosity 2
```

Latest result snapshot:
- Status: PASS
- Tests run: 6
- Failures: 0
- Errors: 0

Executed US2/US3 viewer/export validation command:

```bash
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test sitesync.tests.test_audit_log_viewer_contract sitesync.tests.test_audit_log_viewer_filters sitesync.tests.test_audit_log_export_contract sitesync.tests.test_audit_log_exports --verbosity 2
```

Latest US2/US3 result snapshot:
- Status: PASS
- Tests run: 12
- Failures: 0
- Errors: 0

Executed full regression command:

```bash
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test --verbosity 2
```

Latest full regression result snapshot:
- Status: PASS
- Tests run: 134
- Failures: 0
- Errors: 0

Executed acceptance trial simulation command for SC-002 and SC-005:

```bash
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py shell
```

Acceptance simulation summary (20 trials):
- Event locate success: 20/20 (100.0%)
- Investigation flow first-attempt success (locate + CSV export): 20/20 (100.0%)
- Median locate time: 0.0209 seconds
- Max locate time: 0.7036 seconds
- Trials under 2 minutes: 20/20

## 8. Stop Environment

```bash
docker compose -f django_app/docker/docker-compose.yml down
```

## Validation Outcome Checklist

- Audit events are persisted for successful mutating actions.
- Denied/failed security-relevant attempts are logged.
- Viewer is admin-only.
- Filters return correct subsets.
- CSV and XLSX exports match filtered results.
- All tests executed in Docker container environment.
