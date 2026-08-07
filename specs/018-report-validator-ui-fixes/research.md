# Research: Report Validator UI Fixes

Feature: 018-report-validator-ui-fixes  
Date: 2026-08-07  
Status: Complete

## Decision 1: Validator session permission precedence

- Decision: When a user is assigned validator for a specific report, validator-only permissions take precedence in that report validation session, even if the user also has editor/admin roles.
- Rationale: Preserves separation of duties and prevents accidental report-content changes during validation.
- Alternatives considered:
  - Prefer highest role (editor/admin) permissions: rejected because it weakens validation controls.
  - Add explicit mode switch between edit and validate: rejected as added UX complexity for current scope.

## Decision 2: Validation note autosave interaction

- Decision: Autosave validation notes on field blur with short debounce.
- Rationale: Meets clarified requirement for automatic persistence while limiting unnecessary write frequency.
- Alternatives considered:
  - Save on every keystroke: rejected due to excess request volume and noisier change history.
  - Interval autosave: rejected as less predictable than blur-driven persistence.

## Decision 3: First overview page duplicate control removal

- Decision: Remove the duplicate first comment/validation block from the first overview page and keep one canonical block sized consistently with other pages.
- Rationale: Removes reviewer confusion and standardizes layout behavior across report pages.
- Alternatives considered:
  - Keep both blocks and relabel one: rejected because requirement requests removal and single-source interaction.
  - Hide one block conditionally by role: rejected because duplicate UI is still structurally present.

## Decision 4: Saved Reports selection visibility

- Decision: Show row-selection checkboxes only to admin-authorized users.
- Rationale: Aligns with least-privilege expectations and clarified requirement.
- Alternatives considered:
  - Expose to all report viewers: rejected as broader than required access.
  - Expose to admin + manager: rejected because scope clarification selected admin-authorized only.

## Decision 5: Production consistency for Saved Reports rendering

- Decision: Treat template and built static asset consistency as an explicit acceptance target for this feature.
- Rationale: The reported production-only misalignment indicates deployment/runtime artifact drift must be verified as part of delivery.
- Alternatives considered:
  - Verify only in local/dev: rejected because issue is environment-specific to production behavior.
  - Limit to CSS-only fix: rejected because root issue may include stale/mismatched JS/template rendering.

## Decision 6: Validation strategy and test focus

- Decision: Validate via Docker-first automated tests plus production smoke checks for role-based behavior and Saved Reports alignment.
- Rationale: Satisfies constitution containerized workflow and confirms production-specific regressions are addressed.
- Alternatives considered:
  - Unit tests only: rejected because role gating and rendered layout require integration-level coverage.
  - Manual testing only: rejected because regression protection requires repeatable automated checks.
