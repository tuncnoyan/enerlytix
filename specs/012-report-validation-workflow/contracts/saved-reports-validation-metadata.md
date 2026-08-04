# Contract: Saved Reports Validation Metadata

Feature: 012-report-validation-workflow  
Date: 2026-08-04  
Status: Draft

## Saved Reports Listing View

Route:

```text
GET /reports/
```

Behavior:
- Include validation lifecycle metadata in each report row.
- Replace or remove non-essential `updated` column to create space for validation metadata.
- Preserve existing access-mode and ownership metadata.

Rendered columns (minimum):
- Site
- Reporting Month
- Status
- Owner
- Last Edited By
- Last Edited At
- Validator
- Validation Date
- Validation Status

## Saved Reports JSON Payload

Route:

```text
GET /reports/?format=json
```

Required report row fields (minimum):
- id
- site_id
- site_name
- reporting_month
- status
- access_mode
- owner_name
- last_edited_by_name
- last_edited_at
- validator_name
- validated_by_name
- validation_status
- validation_date
- can_save_final
- open_url

Field semantics:
- `validation_status`: `draft`, `awaiting_validation`, or `validated`.
- `validation_date`: set when report status reaches `validated`; null otherwise.
- `validator_name`: current assigned validator display name or null.
- `can_save_final`: true only when fully validated.

Consistency requirements:
- Report page metadata and saved reports metadata must match for validator identity and validation date.
- Reassignment and reopen-edit events must be reflected in listing state on next load.

## Error and Access Behavior

- Existing report visibility scoping remains authoritative.
- Read-only users can still view validator and validation-date metadata.
- No additional privileges are granted through metadata exposure.
