# Contract: Saved Reports Ownership Listing

Feature: 010-report-ownership-model  
Date: 2026-08-03  
Status: Draft

## Browser Route

```text
GET /reports/
```

## Required Row Fields

Each saved report row must display:
- Report name or site
- Reporting month
- Owner
- Created at
- Last edited by
- Last edited at
- Status

## Behavior

- List remains stable for mixed draft and final reports.
- Metadata reflects latest persisted report state.
- Last edited fields update immediately after successful write.
- Rows still render when historical metadata was backfilled, with consistent fallback display rules.

## Access Indicator

The page must surface effective interaction mode for current user:
- editable as owner
- editable as collaborator
- read-only

## Open Action

```text
GET /report/?site_id=<id>&end_month=<YYYY-MM>
```

Opening a row must preserve and enforce the same write/read rules defined in ownership contracts.

## Error and Empty States

- If user has no visible reports, show explicit empty state.
- If metadata is partially unavailable for a legacy row, render with fallback text and continue listing without page failure.