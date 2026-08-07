# Data Model: Report Validator UI Fixes

## Overview

This feature primarily constrains and reshapes behavior across existing report validation and saved-reports flows. It does not require introducing new persistent domain tables. The model below defines the entities and state used by the feature contract.

## Entities

### 1) Report Review Session

- Purpose: Runtime context for rendering and interacting with a report page.
- Key Fields:
  - report_id (UUID)
  - viewer_user_id (int)
  - assigned_validator_user_id (int, nullable)
  - validation_status (draft/awaiting_validation/validated/finalized context)
  - page_keys (list of canonical validation page keys)
- Relationships:
  - Uses Validator Permission Context to determine interactive capabilities.
  - Reads and updates Page Validation State and Validation Notes.

### 2) Validator Permission Context

- Purpose: Effective permissions for current user in the current report session.
- Key Fields:
  - is_assigned_validator (bool)
  - has_editor_privilege (bool)
  - has_admin_privilege (bool)
  - effective_mode (enum: validator_restricted, editor_capable)
  - can_save_draft (bool)
  - can_save_final (bool)
  - can_toggle_page_validation (bool)
  - can_edit_validation_notes (bool)
- Relationships:
  - Derived from report assignment + role memberships.
  - Drives UI enablement/disablement for report actions.

### 3) Page Validation State

- Purpose: Validation state per page key.
- Key Fields:
  - report_id (UUID)
  - page_key (string)
  - is_validated (bool)
  - validated_by_user_id (int, nullable)
  - validated_at (datetime, nullable)
  - reset_reason (string, nullable)
- Relationships:
  - One row per report/page key.
  - Updated by validator actions.

### 4) Validation Note Entry

- Purpose: Freeform validation comment content per page and author.
- Key Fields:
  - report_id (UUID)
  - page_key (string)
  - authored_by_user_id (int)
  - comment_text (string)
  - updated_at (datetime)
- Relationships:
  - Linked to report and page key.
  - Updated by autosave on blur with debounce.

### 5) Saved Reports Row Selection State

- Purpose: Client-visible selection state for bulk operations in saved reports list.
- Key Fields:
  - report_id (UUID)
  - visible_checkbox (bool)
  - selected (bool)
  - selected_report_ids (list/hidden form state)
- Relationships:
  - Visible only when viewer is admin-authorized.
  - Must remain column-aligned with table header/body structure.

## State Transitions

### Validator Permission Context

- editor_capable -> validator_restricted
  - Trigger: current user is assigned as report validator in validation session.
- validator_restricted -> editor_capable
  - Trigger: user is not assigned validator for that report session.

### Page Validation and Notes

- page validation unchecked -> checked
  - Trigger: validator toggles page validated.
- page validation checked -> unchecked
  - Trigger: validator unchecks or report is reset.
- validation note dirty -> persisted
  - Trigger: note input loses focus; autosave executes after debounce.

### Saved Reports Selection Visibility

- checkbox hidden -> visible
  - Trigger: viewer is admin-authorized.
- checkbox visible -> hidden
  - Trigger: viewer is not admin-authorized.

## Validation Rules

- If effective_mode is validator_restricted:
  - Draft and final save actions must be unavailable.
  - Validation toggles and validation-note editing remain available.
- On first overview page:
  - Exactly one validation/comment block is rendered.
  - The rendered block width behavior matches standard page blocks.
- On Saved Reports:
  - Checkbox column is present only for admin-authorized users.
  - Header and row cell structures remain aligned in all row-count conditions.
