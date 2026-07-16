# Contract: Saved Reports Browser

**Feature**: 004-report-draft-workflow
**Date**: 2026-07-16
**Status**: Draft

---

## Browser Route

```text
GET /reports/
```

### Purpose

Provide a browsable list of saved monthly reports so users can review drafts and finals by site and month.

### Page Content

The page must show, at minimum:

- Site name
- Reporting month
- Report status (`draft` or `final`)
- Last updated timestamp
- Open action for each report

### Behaviour

- Drafts and finals appear together in the same list.
- The latest final version is the one opened when a user selects a final report.
- Browsing should be stable even when multiple historical months exist for a site.

---

## Open Report Action

```text
GET /report/?site_id=<id>&reporting_month=<YYYY-MM>
```

### Behaviour

- Opens the existing monthly report identity.
- If the report is final, the editor should preserve the final status and show the edit warning flow when the user chooses to change content.

---

## Filtering Expectations

The implementation may add filters for site, month, or status, but the core contract requires only that the saved reports page list all saved reports and make them openable.
