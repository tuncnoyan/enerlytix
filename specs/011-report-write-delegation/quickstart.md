# Quickstart Validation Guide: Report Write Delegation

Feature: 011-report-write-delegation  
Date: 2026-08-03

## Prerequisites

1. Docker Desktop is running.
2. Services are started using django_app/docker/docker-compose.yml.
3. Database migrations are applied in the web container.
4. Test users exist for owner, team lead, manager, collaborator, and read-only viewer roles.
5. At least one report exists with valid owner and organisation/team linkage.

## Docker Commands

From repository root:

```powershell
docker compose -f django_app/docker/docker-compose.yml up -d --build
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py migrate
```

Run feature-focused tests in Docker only:

```powershell
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test sitesync.tests.test_report_write_delegation_access sitesync.tests.test_report_write_delegation_authority sitesync.tests.test_report_write_delegation_visibility sitesync.tests.test_report_write_delegation_conflicts
```

## Validation Scenarios

### SC-001 Owner grants same-team delegate

Steps:
1. Sign in as report owner.
2. Grant write access to an active same-team user.
3. Sign in as delegate and save a report change.

Expected:
- Delegate can edit and save while active delegation exists.
- Save updates report metadata per existing ownership model.

### SC-002 Owner revokes delegated writer

Steps:
1. Owner revokes delegate write access.
2. Delegate retries report edit save.

Expected:
- Delegate save is denied at submit time.
- Existing report content remains unchanged after denied save.

### SC-003 Team lead/manager organisation-wide delegation

Steps:
1. Sign in as team lead and grant self write access on a non-owned report in same organisation.
2. Repeat with manager role granting another eligible user.

Expected:
- Team lead self-delegation works within organisation scope.
- Manager delegation works within organisation scope.
- Cross-organisation attempts are denied.

### SC-004 Delegation visibility for report readers

Steps:
1. Open report delegation details as a user with read access.
2. Verify active delegates and grantors are shown.
3. Revoke a delegate and reload details.

Expected:
- Readers can view active delegated writers and grantor identity.
- Revoked delegates no longer appear as active.

### SC-005 Concurrent grant/revoke determinism

Steps:
1. Trigger near-simultaneous grant and revoke actions for the same report/delegate pair.
2. Query resulting active state and audit events.

Expected:
- Final active state follows last-write-wins by server commit timestamp.
- Both actions are present in audit history.

### SC-005 Timed UAT for delegation visibility threshold

Steps:
1. Select a representative sample of at least 10 users who have report read access.
2. Ask each participant to open a report and identify active delegated writers and grantor identity.
3. Record completion time per participant.

Expected:
- At least 90% of participants complete identification within 15 seconds.
- Results are captured in this quickstart validation log for release evidence.

## References

- Plan: [plan.md](plan.md)
- Research: [research.md](research.md)
- Data model: [data-model.md](data-model.md)
- Delegation contract: [contracts/report-write-delegation.md](contracts/report-write-delegation.md)
- Saved reports visibility contract: [contracts/saved-reports-delegation-visibility.md](contracts/saved-reports-delegation-visibility.md)
