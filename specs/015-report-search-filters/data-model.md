# Data Model: Saved Reports Search and Filters

Feature: 015-report-search-filters  
Date: 2026-08-06  
Status: Draft

## Overview

This feature introduces query/filter behavior over existing saved report listing data. No new persistent tables are required. The model changes are logical/view-level entities derived from existing `MonthlyReport`, related user fields, and validation metadata.

## Entities

### 1) SavedReportListRow (derived view model)

Represents one row in the saved reports listing returned to the page.

| Field | Type | Source | Rules |
|---|---|---|---|
| id | UUID string | MonthlyReport.id | Required |
| site_id | integer | MonthlyReport.site_id | Required |
| site_name | string | Site.name | Required; used by Site search |
| reporting_month | YYYY-MM string | MonthlyReport.reporting_month | Required; used by month range filter |
| status | enum | MonthlyReport.current_status | `draft` or `final` |
| owner_name | string | owner_user.username | Fallback `Unassigned` allowed |
| last_edited_by_name | string | last_modified_by_user.username | Fallback `Unknown` allowed |
| validator_name | string or null | validation summary | Nullable |
| validation_status | enum | MonthlyReport.validation_status | `draft`, `awaiting_validation`, `validated` |
| open_url | string | reverse("sitesync:report") | Required row action |

Validation rules:
- `status` must be one of `draft`, `final`.
- `validation_status` must be one of `draft`, `awaiting_validation`, `validated`.
- `reporting_month` must be normalizable as month-year key (`YYYY-MM`).

### 2) SavedReportsFilterCriteria (request/view model)

Represents active filters applied to the listing.

| Field | Type | Required | Rules |
|---|---|---|---|
| site_query | string | No | Case-insensitive contains match against `site_name`; trim surrounding whitespace |
| user_query | string | No | Case-insensitive contains match across `owner_name`, `last_edited_by_name`, `validator_name` |
| start_month | YYYY-MM string | No | Month-year precision only |
| end_month | YYYY-MM string | No | Month-year precision only |
| report_statuses | list[string] | Yes (default all) | Allowed: `draft`, `final` |
| validation_statuses | list[string] | Yes (default all) | Allowed: `draft`, `awaiting_validation`, `validated` |

Validation rules:
- If both `start_month` and `end_month` are set, must satisfy `start_month <= end_month`.
- If either status list is empty, filtering remains valid and yields zero rows for that status dimension.
- Unknown status values are rejected or ignored according to endpoint error policy, but must not broaden result set.

### 3) SavedReportsFilterState (UI state)

Represents the filter values persisted in page controls for current request/session context.

| Field | Type | Rules |
|---|---|---|
| selected_site_query | string | Reflects current Site search box text |
| selected_user_query | string | Reflects current User search box text |
| selected_start_month | YYYY-MM or empty | Reflects Start Month filter |
| selected_end_month | YYYY-MM or empty | Reflects End Month filter |
| selected_report_statuses | list[string] | Defaults to both statuses selected on first load |
| selected_validation_statuses | list[string] | Defaults to all three selected on first load |

State transitions:
- Initial load -> all statuses selected by default.
- Any control change -> criteria set recalculated and listing refreshed.
- All statuses unticked in a group -> valid state with empty results and explicit empty-state messaging.

## Relationships

- `SavedReportsFilterCriteria` constrains the dataset used to generate `SavedReportListRow` instances.
- `SavedReportsFilterState` is the UI representation of the currently active `SavedReportsFilterCriteria`.

## Persistence Impact

- No new database schema objects required.
- No migrations required for this feature.
