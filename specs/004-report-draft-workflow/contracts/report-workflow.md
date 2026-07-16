# Contract: Report Workflow

**Feature**: 004-report-draft-workflow
**Date**: 2026-07-16
**Status**: Draft

---

## Report Editor Route

```text
GET /report/?site_id=<id>&end_month=<YYYY-MM>
```

`reporting_month` in user-facing copy maps to `end_month` in route/query parameters.

### Purpose

Open the monthly report editor for a single site and month. If a report already exists for the site and month, the existing monthly report identity is reopened.

### Behaviour

- If the monthly report does not exist, the page initializes a new draft report.
- If the previous month has a final report for the same site, its comments are copied into the new draft as reference comments.
- If the report is final and the user chooses to edit it, the UI must warn before allowing save operations that create a replacement final version.

---

## Save Draft Action

```text
POST /report/
```

### Form Fields

| Field | Required | Description |
|-------|----------|-------------|
| `site_id` | yes | Site being edited |
| `end_month` | yes | `YYYY-MM` month key (reporting month selected by the user) |
| `save_mode` | yes | `draft` |
| `comments` | yes | Comment payload for all visible visual comment boxes |

### Success Behaviour

- Persist a new draft version for the monthly report.
- Keep the monthly report identity unique per site/month.
- Redirect back to the report editor or the saved reports page depending on the implementation's current flow.

---

## Save Final Action

```text
POST /report/
```

### Form Fields

| Field | Required | Description |
|-------|----------|-------------|
| `site_id` | yes | Site being edited |
| `end_month` | yes | `YYYY-MM` month key (reporting month selected by the user) |
| `save_mode` | yes | `final` |
| `comments` | yes | Comment payload for all visible visual comment boxes |

### Success Behaviour

- Persist a new final version for the monthly report.
- Mark the monthly report as final for browsing and client delivery.
- Preserve the original final version when future edits are made.

---

## Final Edit Warning Flow

```text
POST /report/
```

### Additional Behaviour

- If the report is already final and the user requests an edit, the response must expose a warning state before saving.
- If the warning is accepted, the next save creates a replacement final version rather than overwriting the original final.

---

## Error Conditions

| Condition | Response |
|-----------|----------|
| Missing `site_id` or `end_month` | Validation error; no save occurs |
| Another report already exists for the same site/month | Reopen the existing monthly report instead of creating a duplicate |
| No final report exists for the previous month | New draft starts with blank comments |
