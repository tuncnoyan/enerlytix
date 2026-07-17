# Data Model - Available Capacity Integration

## Entity: CapacityReference
- Purpose: Persist manually uploaded available-capacity records for report-time lookup.
- Keys:
  - Primary key: UUID (or project-standard surrogate key)
  - Business key: normalized `esight_meter_code` (unique)
- Core Fields:
  - `name` (string, required): latest uploaded Name column value for reference and traceability
  - `esight_meter_code` (string, required, unique): lookup key used during report integration
  - `available_capacity_kva` (decimal, required): parsed Av Cap (kVA) value
  - `source_filename` (string, optional): uploaded workbook name for audit context
  - `last_imported_at` (datetime, required): timestamp of most recent upsert
  - `created_at` / `updated_at` (datetime)
- Validation Rules:
  - `esight_meter_code` must be non-empty after trim/normalization
  - `available_capacity_kva` must be numeric, non-null, and greater than or equal to zero
  - duplicate keys in one upload are invalid rows (skipped with error)
  - when a later valid row reuses the same `esight_meter_code`, both `name` and `available_capacity_kva` are overwritten with the latest uploaded values

## Entity: CapacityUploadRun
- Purpose: Record each upload operation outcome summary for UI feedback and troubleshooting.
- Keys:
  - Primary key: UUID
- Core Fields:
  - `uploaded_at` (datetime)
  - `uploaded_filename` (string)
  - `total_rows` (integer)
  - `accepted_rows` (integer)
  - `rejected_rows` (integer)
  - `status` (enum: success, partial_success, failed)
  - `error_summary` (JSON/text): aggregate validation errors
- Validation Rules:
  - `total_rows = accepted_rows + rejected_rows`
  - `status=failed` for schema-level failures (e.g., missing required columns)

## Derived Runtime Mapping: SupplyCapacityMatch
- Purpose: Resolve report supply -> capacity value during load-factor payload generation.
- Inputs:
  - `Supply.device_id` (normalized eSight Meter Code candidate)
  - `CapacityReference.esight_meter_code`
- Outputs:
  - matched `available_capacity_kva` if key exists
  - unmatched marker (`null`) if no record exists
- Rules:
  - Matching is exact after shared normalization
  - Name is not part of matching logic
  - If a reference record exists for the key, the most recently uploaded Name is metadata only and does not affect lookup eligibility

## State Transitions

### CapacityUploadRun
1. `received` -> `validating`
2. `validating` -> `failed` (schema/file-level invalid)
3. `validating` -> `importing` (schema valid)
4. `importing` -> `success` (all rows accepted)
5. `importing` -> `partial_success` (some rows rejected)

### CapacityReference (per key)
1. `absent` -> `created` (first valid row for key)
2. `created`/`updated` -> `updated` (later upload for same key)
3. `updated` persists until replaced by next valid row for same key
