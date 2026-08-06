# Contract: Capacity Upload Results Export

Feature: 017-capacity-upload-results  
Date: 2026-08-06  
Status: Draft

## Scope

Defines behavior for settings-page upload outcome rendering and Excel export of latest capacity-upload results.

## Interface 1: Settings outcome rendering

```text
GET /settings/
```

Route name: `sitesync:settings_panel`

Behavioral contract:
- Show concise status notice for upload outcome (`success`, `partial_success`, `failed`).
- Show latest upload summary block (filename, timestamp, status, aggregate counts).
- Do not render inline per-row issue list on page.
- If latest completed run has persisted row outcomes, show a visible "Download Upload Results (.xlsx)" action.

## Interface 2: Export latest upload results workbook

```text
GET /settings/capacity-upload/results.xlsx
```

Suggested route name: `sitesync:capacity_upload_results_export`

Authorization:
- Must require an authenticated user where is_staff is true or is_superuser is true (same boundary as settings panel access for this feature).

Selection rule:
- Must export exactly the latest completed capacity upload run currently shown on settings page.

Error behavior:
- If no completed upload run exists, return clear user-facing feedback.
- If latest run exists but no row-level outcomes are available, return clear user-facing feedback.
- No silent empty success response for unavailable results.

Success response:
- `200 OK`
- `Content-Type`: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Attachment filename includes run context (for example, `capacity-upload-results-YYYYMMDD-HHMMSS.xlsx`).

Workbook contract:
- Exactly two worksheets:
  - `Successes`
  - `Failures`
- Row schema in both sheets includes:
  - `Source Row Number`
  - All original upload columns in original header names
  - `Outcome`
  - `Explanation`

Outcome/explanation rules:
- Success row: `Outcome=success`; explanation may be informational/empty but field must exist.
- Failure row: `Outcome=failure`; explanation must include all validation reasons combined for that row.

## Compatibility Requirements

- Existing upload processing summary counts and statuses remain unchanged.
- Existing `.xlsx` upload format and validation rules remain unchanged.
- Access control behavior for settings routes remains unchanged.
