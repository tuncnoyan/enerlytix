# Quickstart Validation Guide: Report Ownership Model

Feature: 010-report-ownership-model  
Date: 2026-08-03

## Prerequisites

1. Docker Desktop is running.
2. Containers are started from repository root with compose file django_app/docker/docker-compose.yml.
3. Database migrations are applied in the web container.
4. At least one admin user, one team lead, one manager, and one regular user exist.
5. At least one site and one monthly report exist for validation.

## Docker Commands

From repository root:

```powershell
docker compose -f django_app/docker/docker-compose.yml up -d --build
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py migrate
```

Run tests in Docker only:

```powershell
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test tests/integration tests/contract tests/unit
```

## Validation Scenarios

### SC-001 Owner is set and can edit

Steps:
1. Sign in as user A.
2. Create or open a report for a site and month, then save.
3. Reopen the same report.

Expected:
- Report owner equals user A.
- User A has write capability.
- Created date is present.

### SC-002 Non-owner default is read-only

Steps:
1. Sign in as user B with report visibility but no grant.
2. Open user A report.
3. Attempt to save changes.

Expected:
- Report opens in read-only mode.
- Save is blocked with permission-denied response.

### SC-003 Owner grant and revoke collaborator

Steps:
1. Sign in as owner user A.
2. Grant write access to user B.
3. Sign in as user B and save a report change.
4. Sign back in as owner and revoke user B grant.
5. Sign in as user B and attempt save again.

Expected:
- User B can edit while grant is active.
- Last edited fields update after B save.
- User B becomes read-only after revoke.

### SC-004 Saved reports shows ownership metadata

Steps:
1. Open saved reports page.
2. Inspect multiple rows spanning draft and final reports.

Expected:
- Each row displays report/site, reporting month, owner, created at, last edited by, last edited at, status.
- Metadata matches latest report state.

### SC-005 Team-lead approved fallback transfer

Steps:
1. Prepare report owned by user A.
2. Sign in as team lead in same scope and approve owner unavailability.
3. Confirm fallback evaluation order team lead then manager then admin.
4. Open report as selected new owner.
5. Check previous owner permissions.

Expected:
- Ownership transfers to first available candidate in strict order.
- Candidate eligibility checks active status, role, and same scope.
- Previous owner retains collaborator write access unless later revoked.
- Transfer action is traceable in ownership transfer history/audit records.

## References

- Plan: [plan.md](plan.md)
- Research: [research.md](research.md)
- Data model: [data-model.md](data-model.md)
- Ownership contract: [contracts/report-ownership.md](contracts/report-ownership.md)
- Saved reports contract: [contracts/saved-reports-ownership.md](contracts/saved-reports-ownership.md)