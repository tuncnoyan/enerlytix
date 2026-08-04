# Quickstart Validation Guide: Report Validation Workflow

Feature: 012-report-validation-workflow  
Date: 2026-08-04

## Prerequisites

1. Docker Desktop is running.
2. Services are started from `django_app/docker/docker-compose.yml`.
3. Database migrations are applied in the web container.
4. Test users exist for owner, contributor, validator, team lead, manager, admin, and read-only roles.
5. At least one report exists for a site with valid team hierarchy data.

## Docker Commands

From repository root:

```powershell
docker compose -f django_app/docker/docker-compose.yml up -d --build
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py migrate
```

Run validation workflow test suite in Docker only:

```powershell
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test sitesync.tests.test_report_validation_assignment sitesync.tests.test_report_validation_page_status sitesync.tests.test_report_validation_final_gate sitesync.tests.test_report_validation_reassignment sitesync.tests.test_saved_reports_validation_metadata
```

## Validation Scenarios

### SC-001 Assign eligible validator and enter awaiting-validation

Steps:
1. Sign in as report owner.
2. Assign an active non-owner validator from same team or supervisory chain.
3. Refresh report header and saved reports listing.

Expected:
- Validation status changes from `draft` to `awaiting_validation`.
- Validator identity appears in report and saved reports metadata.

### SC-002 Reject ineligible validator assignment

Steps:
1. Attempt assignment where validator equals owner.
2. Attempt assignment to user outside same team and outside supervisory chain.

Expected:
- Each request is denied with a clear validation message.
- Existing validator assignment and validation status remain unchanged.

### SC-003 Validator-only page checkbox behavior

Steps:
1. Sign in as assigned validator and mark page checkbox validated.
2. Sign in as owner or contributor and attempt to mark the same checkbox.

Expected:
- Validator action succeeds with timestamp.
- Non-validator action is denied.

### SC-004 Reset on business-content edit but not validation-comment edit

Steps:
1. Validate a page as assigned validator.
2. Edit business content on that page as owner/contributor and save draft.
3. Re-validate page.
4. Edit only validation comment text and save draft.

Expected:
- Step 2 clears page validation and shows reset warning.
- Step 4 does not clear page validation.

### SC-005 Full validation gate before final save

Steps:
1. Leave at least one page unvalidated and attempt final save.
2. Validate all pages and retry final save.

Expected:
- First final save is blocked with outstanding-page message.
- Second final save succeeds and report status reflects finalized state.

### SC-006 Validator reassignment resets all page validation

Steps:
1. Validate multiple pages with current validator.
2. Reassign validator.

Expected:
- All page validation checkboxes reset to unvalidated.
- Validation status remains `awaiting_validation` until new full validation.

### SC-007 Reopen final report via superior-chain regrant

Steps:
1. Save a fully validated report as final.
2. Regrant write access as team lead/manager/admin in owner's supervisory chain.
3. Edit business content and save draft.

Expected:
- Edit succeeds after authorized regrant.
- Validation state reopens and previously validated state is cleared per reset rules.

## References

- Plan: [plan.md](plan.md)
- Research: [research.md](research.md)
- Data model: [data-model.md](data-model.md)
- Workflow contract: [contracts/report-validation-workflow.md](contracts/report-validation-workflow.md)
- Saved reports metadata contract: [contracts/saved-reports-validation-metadata.md](contracts/saved-reports-validation-metadata.md)
