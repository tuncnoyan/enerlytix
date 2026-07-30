# Contract: Audit Log Viewer and Export

## Purpose

Define admin-facing interface contracts for viewing and exporting audit logs with consistent filtering semantics.

## Access Control

- Authentication required.
- Admin privilege required for all routes in this contract.
- Unauthorized users receive denied response (redirect or 403 based on route style).

## UI Route Contract

### GET /panel/audit-logs/

Returns audit log page with filter controls and paged results.

**Query parameters**:
- `user` (optional): Actor user id.
- `keyword` (optional): Keyword match in message/entity context.
- `start` (optional): UTC date/time lower bound.
- `end` (optional): UTC date/time upper bound.
- `action_type` (optional): Normalized action type code.
- `page` (optional): Page number.

**Response behavior**:
- 200 for authorized admin users.
- Filter controls reflect active query values.
- Result rows include: actor, source IP, UTC timestamp, action type, outcome, target, message.
- Invalid filter input returns 200 with inline validation errors on the HTML page and no export file.
- 403/redirect for non-admin users.

## Export Route Contracts

### GET /panel/audit-logs/export.csv

Returns CSV file for the exact filtered subset.

**Query parameters**: same as viewer route.

**Response**:
- Content-Type: `text/csv`
- Header row required.
- Data rows must match filtered subset exactly.
- 200 with empty data rows allowed when no matches.

### GET /panel/audit-logs/export.xlsx

Returns XLSX file for the exact filtered subset.

**Query parameters**: same as viewer route.

**Response**:
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Header row required.
- Data rows must match filtered subset exactly.
- 200 with headers only when no matches.

## Shared Filter Semantics

- All endpoints use identical filter interpretation.
- Date filters are interpreted against stored UTC timestamps.
- `start`-only and `end`-only filters are valid.
- Invalid filter combinations (for example `start > end`) return validation error.

## Error Contract

- Viewer route invalid filters: 200 HTML with field-level validation messages.
- Export routes invalid filters: 400 Bad Request with structured error payload.
- Unauthorized access: 403 Forbidden or authentication redirect (route-style dependent).

## Auditability Guarantees

- Viewer/export access denial attempts are themselves auditable events.
- Target entity deletion after event time does not remove existing log rows.
