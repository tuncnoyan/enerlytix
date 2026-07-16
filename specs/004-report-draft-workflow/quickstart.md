# Quickstart Validation Guide: Monthly Report Draft and Final Workflow

**Feature**: 004-report-draft-workflow
**Date**: 2026-07-16

---

## Prerequisites

1. Django development server running from `django_app/`.
2. Database migrations applied.
3. At least one site with supplies and at least one complete month of report data.
4. At least one previous-month final report with comments for carry-forward validation.

---

## Validation Scenarios

### SC-001 - Save and reopen a draft

**Steps**:
1. Open the dashboard.
2. Select exactly one site and a reporting month.
3. Open the report editor and save the report as a draft.
4. Reopen the same site and month.

**Expected**:
- The same monthly report is reopened.
- No second report is created for the same site and month.

---

### SC-002 - Finalise a report and preserve the original final

**Steps**:
1. Open a draft report.
2. Save it as final.
3. Reopen the final report and choose to edit it.
4. Accept the warning and save the changes.

**Expected**:
- The UI warns before editing the final report.
- The original final remains available as a historical version.
- A replacement final version becomes the current client-facing version.

---

### SC-003 - Carry previous month comments forward

**Steps**:
1. Ensure the previous month has a final report with comments.
2. Start a new report for the next month for the same site.

**Expected**:
- Matching comment boxes are prefilled from the previous month's final report.
- Each copied comment shows a reference warning that it came from the previous month.

---

### SC-004 - Browse saved reports

**Steps**:
1. Open the saved reports page.
2. Locate a draft and a final report for the same or different sites.
3. Open one of the reports from the list.

**Expected**:
- Reports are listed with site name, reporting month, and status.
- The selected report opens correctly.

---

## Commands

From `django_app/`:

```powershell
python manage.py migrate
python manage.py runserver 0.0.0.0:8080
python manage.py test
```

---

## References

- Plan: [plan.md](plan.md)
- Data model: [data-model.md](data-model.md)
- Workflow contract: [contracts/report-workflow.md](contracts/report-workflow.md)
- Saved reports browser contract: [contracts/saved-reports-browser.md](contracts/saved-reports-browser.md)