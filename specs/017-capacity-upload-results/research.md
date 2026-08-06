# Research: Capacity Upload Results UX

Feature: 017-capacity-upload-results  
Date: 2026-08-06  
Status: Complete

## Decision 1: Export target run

- Decision: Export results for the latest completed upload run shown in the settings panel.
- Rationale: Matches clarified requirement and existing UI mental model (`latest_capacity_run`) without adding run selection complexity.
- Alternatives considered:
  - User-selected historical run: rejected because out of scope for this feature and requires additional selector/filter UX.
  - Multi-run combined export: rejected due to ambiguity and larger data volume.

## Decision 2: Persist row-level outcomes for export

- Decision: Add a dedicated row-result persistence model linked to `CapacityUploadRun` to store per-row source payload, outcome, and explanation.
- Rationale: Current `CapacityUploadRun.error_summary` stores only failure strings and cannot reconstruct successes or original columns for export.
- Alternatives considered:
  - Store all row outcomes in `CapacityUploadRun.error_summary` JSON only: rejected because it mixes summary/error concerns and scales poorly.
  - Re-parse original uploaded file on download: rejected because original files are not retained as durable source artifacts.

## Decision 3: Workbook shape

- Decision: Generate one `.xlsx` workbook with exactly two sheets: `Successes` and `Failures`.
- Rationale: Explicit split supports quick remediation for failed rows while retaining full success auditability.
- Alternatives considered:
  - Single mixed sheet: rejected due to reduced readability for large runs.
  - Three-sheet workbook with extra summary tab: rejected as unnecessary because summary already appears on settings page.

## Decision 4: Failed-row explanation handling

- Decision: For failed rows, combine all validation reasons into one explanation field in that row.
- Rationale: Preserves complete troubleshooting context without duplicating the same source row multiple times.
- Alternatives considered:
  - First error only: rejected because it hides additional corrections needed.
  - One row per error: rejected due to row explosion and harder reconciliation with original file.

## Decision 5: Export column contract

- Decision: Each exported row includes source row number, original upload columns, outcome, and explanation.
- Rationale: Meets clarified requirement and ensures users can fix source data without switching back to upload files.
- Alternatives considered:
  - Minimal diagnostic columns only: rejected because users lose original context.
  - Omit explanation for success rows only: rejected to keep schema consistent across both sheets.

## Decision 6: Settings page UX treatment

- Decision: Remove inline `capacity_upload_errors` list rendering and keep only concise status notice + latest run summary + upload form + download action.
- Rationale: Eliminates the unusable long-page failure mode while preserving high-signal status context.
- Alternatives considered:
  - Collapse/expand issue list: rejected because requirement explicitly requests removal.
  - Pagination inside inline issues list: rejected as complexity without meeting requested simplification.

## Decision 7: Access control and no-data response

- Decision: Reuse existing settings authorization boundary for export endpoint; if latest run has no persisted row outcomes, return clear user-facing feedback.
- Rationale: Consistent security and predictable behavior for edge cases in spec FR-008 and FR-009.
- Alternatives considered:
  - Public export URL with signed token: rejected as unnecessary and out of scope.
  - Silent empty file when no outcomes exist: rejected because users need explicit action guidance.
