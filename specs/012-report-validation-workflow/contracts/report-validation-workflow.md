# Contract: Report Validation Workflow

Feature: 012-report-validation-workflow  
Date: 2026-08-04  
Status: Draft

## Report Access View

Route:

```text
GET /report/?site_id=<id>&end_month=<YYYY-MM>
```

Behavior:
- Owner and active write-authorized contributors can edit business content.
- Assigned validator can mark/unmark page validation checkboxes.
- Read-only users can view validation metadata but cannot edit or validate.
- Response context includes validation summary and per-page validation state.

Response context fields (minimum):
- validation_status
- validator_user
- validated_by_user
- validated_at
- pages_validation (page_key -> is_validated, validated_by, validated_at)
- validation_comments (page_key -> latest validation comment text)
- validation_comment_threads (page_key -> ordered comment thread entries)
- can_save_final

## Assign Validator

Route:

```text
POST /reports/<report_id>/validation/assign/
```

Required fields:
- validator_user_id

Authorization behavior:
- Allowed for report owner or owner's superiors (team lead, manager, admin).
- Selected validator must be active, must not be owner, and must be either same-team or in owner's supervisory chain.

State behavior:
- On first assignment: set report validation status to `awaiting_validation`.
- On reassignment: set report validation status to `awaiting_validation` and reset all page validations to unvalidated.

Error behavior:
- 403-equivalent response for unauthorized assigners.
- 400-equivalent response for ineligible validator target.

## Page Validation Toggle

Route:

```text
POST /reports/<report_id>/validation/pages/<page_key>/mark/
```

Required fields:
- is_validated (true/false)

Path parameter validation:
- `page_key` must match a canonical rendered report page key.
- Unknown or non-rendered `page_key` values are rejected with a 400-equivalent response.

Authorization behavior:
- Only currently assigned validator may set `is_validated=true`.
- Non-validator users attempting checkbox updates are denied.

State behavior:
- Marking a page validated stores validator identity and timestamp.
- If all pages become validated, report validation status transitions to `validated`, and report-level `validated_by` and `validated_at` are updated.

## Save Report Action (Validation Gate)

Route:

```text
POST /report/
```

Required fields:
- site_id
- end_month
- save_mode (`draft` or `final`)
- comments (existing business comment payload)
- validation_comments (validation comment payload per page, optional)

Validation behavior:
- Business-content page edits clear page validation for affected pages.
- Validation-comment-only edits do not clear page validation.
- Final save (`save_mode=final`) is allowed only when report validation status is `validated` and all pages are validated.

Error behavior:
- Final save denied with clear message when any page is unvalidated.
- Unauthorized writes remain denied by existing submit-time access checks.

## Reopen Final Report for Write

Route:

```text
POST /reports/<report_id>/validation/regrant-write/
```

Required fields:
- target_user_id
- reason (optional but recommended for audit)

Authorization behavior:
- Allowed only for team lead, manager, or admin in the owner's supervisory chain.

State behavior:
- Regrant alone enables write per existing access model.
- Upon subsequent business-content edit, validation status reopens from `validated` to `awaiting_validation` and affected page validations reset.

Notes:
- This route is an alias for the existing write-grant workflow and accepts `target_user_id` or `granted_user_id`.
- A blocked final save emits a `final_blocked` validation event and returns `can_save_final=false`.

## Validation Audit Requirements

For each workflow action, store immutable events with:
- report_id
- event_type
- event_by_user_id
- event_at
- page_key when applicable
- metadata describing state transitions and reason
