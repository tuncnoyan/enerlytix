# Contract: Report Validator UI and Saved Reports Behavior

## Purpose

Define externally visible behavior for report validation sessions and saved-reports row-selection rendering.

## Contract Scope

- Report page reviewer interactions for validators.
- Validation note autosave behavior.
- First overview-page validation/comment block rendering.
- Saved Reports row-selection visibility and column alignment.

## 1) Report Session Permission Contract

### Inputs

- Current authenticated user
- Report assignment context (including assigned validator)
- User role memberships

### Rules

- When user is assigned validator for the report session:
  - Report-content edit inputs are read-only.
  - Save as draft/final actions are unavailable.
  - Validation checkbox toggles remain available.
  - Validation note text entry remains available.
- Dual-role users (editor/admin + validator): validator-restricted behavior must apply for that report session.

### Observable Outcomes

- No report-content save request is accepted from validator-restricted session controls.
- Validation state and validation-note updates succeed for validator-restricted sessions.

## 2) Validation Note Autosave Contract

### Trigger

- Validation note field loses focus.

### Behavior

- System autosaves note text after short debounce.
- No explicit Save button action is required for validation notes.

### Failure Behavior

- On autosave failure, UI must keep user-entered note text available for retry and communicate failure state.

## 3) First Overview Page Validation Block Contract

### Rendering Rules

- Exactly one validation/comment interaction block is rendered for first overview section.
- Duplicate top block is not rendered.
- Remaining block width/placement is consistent with standard report-page validation block layout.

## 4) Saved Reports Selection Contract

### Visibility Rules

- Row-selection checkboxes are visible only to admin-authorized users.
- Non-admin users do not see row-selection checkboxes or bulk-selection controls.

### Alignment Rules

- Header and body column structures remain aligned for:
  - zero rows
  - one row
  - many rows

### Selection State Rules

- For admin-authorized users, selected report IDs map exactly to checked row checkboxes.
- Bulk actions consume only currently selected report IDs.

## 5) Environment Consistency Contract

- Behavior above must be consistent across local/dev/test and production deployments.
- Production verification explicitly includes checkbox visibility, column alignment, and validator-restricted interactions.
