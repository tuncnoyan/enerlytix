# Quickstart: Saved Reports Admin Controls Validation

Feature: 016-admin-report-controls  
Date: 2026-08-06

## Prerequisites

- Docker Desktop running.
- Services started from repository root:

```powershell
docker compose -f django_app/docker/docker-compose.yml up -d
```

- Database migrations applied:

```powershell
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py migrate
```

## Scenario 1: Platform admin sees selection and delete controls

1. Sign in as a platform admin user.
2. Open saved reports page (`/reports/`).
3. Verify each row shows a left-side selection checkbox.
4. Verify bulk delete control is visible.

Expected:
- Admin-only delete controls are present.
- Existing filter controls still render.

## Scenario 2: Non-admin cannot delete reports

1. Sign in as a non-admin user.
2. Open `/reports/`.
3. Verify row-selection delete controls are hidden/unavailable.
4. Attempt a direct bulk-delete POST request (test client or HTTP tool).

Expected:
- Delete request is denied.
- No reports are deleted.
- Unauthorized attempt is present in audit logs.

## Scenario 3: Successful atomic bulk delete

1. Sign in as platform admin.
2. Select multiple report rows.
3. Submit delete with correct password.

Expected:
- Selected rows are deleted.
- Non-selected rows remain.
- Success audit entry exists with selected references.

## Scenario 4: Atomic failure when one row is not deletable

1. Prepare selection where at least one selected report is no longer deletable (e.g., removed concurrently).
2. Submit bulk delete with correct password.

Expected:
- Zero selected rows are deleted.
- UI/API response includes blocking report references.
- Failure audit entry exists.

## Scenario 5: Sorting by dropdown field

1. Open `/reports/`.
2. Choose each dropdown sort field one by one.
3. Validate ordering defaults:
   - Date fields newest-first.
   - Text fields A-Z.
   - Numeric fields high-low.
4. Apply filters, then change sort field.

Expected:
- Sort order changes per selected field.
- Active filters remain applied.

## Automated Test Commands (Docker-only)

Run targeted saved-reports tests:

```powershell
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test sitesync.tests.test_saved_reports_view sitesync.tests.test_saved_reports_ownership_listing sitesync.tests.test_saved_reports_team_context
```

Run audit-focused tests:

```powershell
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test sitesync.tests.test_audit_helpers sitesync.tests.test_audit_log_entry_contract sitesync.tests.test_audit_log_viewer_contract
```

Run full regression:

```powershell
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test
```

## Related Artifacts

- Spec: [spec.md](spec.md)
- Plan: [plan.md](plan.md)
- Data model: [data-model.md](data-model.md)
- Contract: [contracts/saved-reports-admin-controls.md](contracts/saved-reports-admin-controls.md)
