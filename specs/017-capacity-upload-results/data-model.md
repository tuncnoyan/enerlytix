# Data Model: Capacity Upload Results UX

Feature: 017-capacity-upload-results  
Date: 2026-08-06  
Status: Draft

## Overview

This feature extends the existing available-capacity upload flow by preserving row-level outcomes for export and simplifying settings-page outcome rendering.

## Entities

### 1) CapacityUploadRun (existing, reused)

Represents aggregate outcome for one upload attempt.

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary identifier for one run |
| uploaded_filename | string | Source file name as uploaded |
| uploaded_at | datetime | Most recent run selected as export source |
| total_rows | integer | Total non-empty processed data rows |
| accepted_rows | integer | Count of success rows |
| rejected_rows | integer | Count of failed rows |
| status | enum | `success`, `partial_success`, `failed` |
| error_summary | list[string] | Retained for aggregate compatibility, no longer rendered inline |

### 2) CapacityUploadRowResult (new persisted entity)

Represents one processed upload row outcome tied to a run.

| Field | Type | Required | Rules |
|---|---|---|---|
| id | UUID | Yes | Primary key |
| run | FK -> CapacityUploadRun | Yes | Cascade delete with run |
| source_row_number | integer | Yes | Original worksheet row index (starts at 2 for first data row) |
| outcome | enum | Yes | `success` or `failure` |
| explanation | text | Yes | Empty/neutral for success; combined reasons for failure |
| original_columns | JSON object | Yes | Key/value map of all original upload columns for that row |
| created_at | datetime | Yes | Audit timestamp |

Validation rules:
- `source_row_number` must be positive.
- `outcome=failure` requires non-empty `explanation`.
- `original_columns` must include required upload headers when present in source.

### 3) UploadResultsExportProjection (derived view model)

Sheet-ready representation produced from `CapacityUploadRowResult`.

| Field | Type | Rules |
|---|---|---|
| source_row_number | integer | First column in both sheets |
| original_upload_columns... | dynamic columns | Preserve original header names and row values |
| outcome | string | `success` / `failure` |
| explanation | string | Combined failure reasons or informational success explanation |

## Relationships

- One `CapacityUploadRun` has many `CapacityUploadRowResult` rows.
- `UploadResultsExportProjection` is derived from row results of the latest completed run.

## State Transitions

1. Upload starts -> rows validated and processed.
2. For each processed row, a `CapacityUploadRowResult` is written as success or failure.
3. Run summary (`CapacityUploadRun`) is finalized (`success` / `partial_success` / `failed`).
4. Export request resolves latest completed run and materializes two-sheet workbook:
   - `Successes`: rows where outcome is success
   - `Failures`: rows where outcome is failure

## Persistence Impact

- New migration required for `CapacityUploadRowResult` table and indexes.
- Existing `CapacityUploadRun` retained for compatibility with summary UI and historical behavior.
