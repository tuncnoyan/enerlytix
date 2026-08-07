# Quickstart: Report Validator UI Fixes Validation

This guide validates the feature end-to-end after implementation.

## Prerequisites

- Docker Desktop running.
- Repository root contains configured .env.
- Containers built and running.

## Setup

1. Start containers:

```bash
docker compose -f django_app/docker/docker-compose.yml up -d --build
```

2. Run migrations:

```bash
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py migrate
```

3. (Optional) Create/prepare test users and report fixtures representing:
- admin-authorized user
- non-admin user
- validator-only user
- dual-role user (admin/editor + assigned validator)

## Automated Validation

Run focused tests (adjust module names if implementation introduces new test files):

```bash
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test sitesync.tests.test_saved_reports_view tests.contract.test_report_validation_page_mark_contract
```

Run broader regression set:

```bash
docker compose -f django_app/docker/docker-compose.yml exec -T web python manage.py test sitesync.tests
```

## Manual Validation Scenarios

### Scenario A: First overview page duplicate block removal

1. Open a report with overview content.
2. Navigate to first overview page.
3. Confirm only one validation/comment block is visible.
4. Confirm its width matches validation/comment blocks on at least three other report pages.

Expected:
- No duplicate top validation/comment block.
- Layout consistency across pages.

### Scenario B: Validator-restricted report session

1. Login as assigned validator.
2. Open target report.
3. Attempt report-content editing and draft/final save actions.
4. Toggle page validation state and enter validation notes.
5. Move focus out of validation note field.

Expected:
- Content-editing and draft/final save actions are unavailable.
- Validation toggle works.
- Validation note autosaves on blur after short debounce.

### Scenario C: Dual-role precedence

1. Login as a user who is both admin/editor and assigned validator on the report.
2. Open the report in validation context.

Expected:
- Validator-only restrictions apply for that report session.
- Validation controls remain available.

### Scenario D: Saved Reports admin visibility and alignment

1. Login as admin-authorized user.
2. Open Saved Reports.
3. Confirm row-selection checkboxes render in first column.
4. Confirm row values align with correct headers.
5. Select multiple rows and verify bulk selection count/IDs.

Expected:
- Checkboxes visible and functional for admin-authorized user.
- No column misalignment.

### Scenario E: Saved Reports non-admin behavior

1. Login as non-admin user.
2. Open Saved Reports.

Expected:
- No row-selection checkboxes or bulk-selection controls.
- Column alignment remains correct.

## Production Smoke Validation

After deployment approval and release:

1. Hard-refresh browser session.
2. Repeat Scenarios B, D, and E in production.
3. Verify no regression in validation note persistence, role restrictions, or saved-reports alignment.

## Related Artifacts

- Spec: [spec.md](spec.md)
- Plan: [plan.md](plan.md)
- Data Model: [data-model.md](data-model.md)
- Contract: [contracts/report-validator-ui-behavior.md](contracts/report-validator-ui-behavior.md)
