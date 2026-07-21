# Quickstart Validation Guide: Report Cover Pages

**Feature**: 007-add-report-cover-pages
**Date**: 2026-07-21

---

## Prerequisites

1. Docker Desktop is running.
2. `.env` exists in repository root (copy from `.env.example` if needed).
3. The Docker compose stack can start successfully.
4. A valid site and reporting month exist for report generation.

---

## Environment Setup (Docker Only)

Run from repository root:

```powershell
docker compose -f django_app/docker/docker-compose.yml up --build -d
docker compose -f django_app/docker/docker-compose.yml exec web python manage.py migrate
```

Optional health check:

```powershell
docker compose -f django_app/docker/docker-compose.yml ps
```

Application URL:
- http://localhost:8080/report/

---

## Test Execution (Docker Only)

Run all Django tests inside the web container:

```powershell
docker compose -f django_app/docker/docker-compose.yml exec web python manage.py test
```

Optional targeted test runs (after feature tests are added):

```powershell
docker compose -f django_app/docker/docker-compose.yml exec web python manage.py test sitesync.tests
```

---

## Validation Scenarios

### SC-001 - Cover sequence in draft and final reports

**Steps**:
1. Open a report for a site/month.
2. Generate draft output.
3. Generate final output.

**Expected**:
- Both outputs use: front cover 1, front cover 2, body pages, back cover.

---

### SC-002 - First-cover default values and formatting

**Steps**:
1. Open report cover editor/view.
2. Inspect first-cover fields.

**Expected**:
- Site field defaults to selected site name.
- Report month title defaults to `[Month Year] Energy Report`.
- Date defaults to fixed `DD MMMM YYYY` format.

---

### SC-003 - First-cover background replacement validation

**Steps**:
1. Upload a valid replacement background (supported type, <=10 MB).
2. Generate report and verify cover.
3. Upload an invalid file type or >10 MB file.

**Expected**:
- Valid file replaces default first-cover background for current report context.
- Invalid upload is rejected with clear message.
- Default image remains active after invalid upload.

---

### SC-004 - Second-cover scope and contents behavior

**Steps**:
1. Inspect second-cover default scope text.
2. Verify site substitution in scope body.
3. Verify contents list order and meter-name suffix behavior.
4. Edit scope/contents fields and regenerate output.

**Expected**:
- Default scope/contents text appears as defined.
- Meter names are appended in parentheses except for `Total Utility Usage (£)`.
- Edited scope/contents values are reflected in output.

---

### SC-005 - PDF and PPTX parity with editability

**Steps**:
1. Download report as PDF.
2. Download same report as PPTX.
3. Open PPTX in a PowerPoint-compatible editor.
4. Edit first/second cover text fields.

**Expected**:
- PDF and PPTX both contain full cover sequence.
- Front-cover fields are editable in PPTX.
- Back cover remains static.

---

## Validation Evidence (SC-003 and SC-006)

Use the following table to record MP-001 and MP-002 outcomes:

| Run ID | Scenario | Outcome (Pass/Fail) | Failure Reason | Threshold | Running Pass Rate |
|--------|----------|---------------------|----------------|-----------|-------------------|
| 1 | SC-003 first-cover edit attempt | Pass | N/A | >=95% | 100% |
| 2 | SC-006 report generation with covers | Pass | N/A | >=95% | 100% |

Final calculations:

- SC-003: `successful_edit_attempts / total_edit_attempts * 100`
- SC-006: `successful_generations / total_generations * 100`
- Confirm compliance:
	- SC-003 >= 95%
	- SC-006 >= 95%

---

## References

- Plan: [plan.md](plan.md)
- Research: [research.md](research.md)
- Data model: [data-model.md](data-model.md)
- Contract: [contracts/report-cover-pages.md](contracts/report-cover-pages.md)
