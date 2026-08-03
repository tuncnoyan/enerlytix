# Contract: Saved Reports Delegation Visibility

Feature: 011-report-write-delegation  
Date: 2026-08-03  
Status: Draft

## Browser Route

```text
GET /reports/
```

## Required Behavior

- Existing saved-report listing remains available for users with report visibility.
- Opening a report from the listing enforces effective write permissions from delegation rules.
- Delegated writers can edit after opening; non-delegated non-owners remain read-only.

## Optional Delegation Indicator (if surfaced on listing)

If list-level delegation summary is shown, it must:
- Only display reports the user can already read.
- Reflect active delegation state (not revoked records).
- Avoid exposing users from inaccessible reports.

## Open Action Consistency

```text
GET /report/?site_id=<id>&end_month=<YYYY-MM>
```

Opening from saved reports must yield consistent editor state:
- owner write mode for owner
- delegated_writer mode for active delegates
- read_only mode for others

## Error and Empty States

- If a user has no visible reports, list displays explicit empty state.
- If a delegation is revoked between list view and save attempt, save is blocked at submit-time authorization check and caller receives a clear permission error.
