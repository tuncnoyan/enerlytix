# Phase 0 Research - Available Capacity Integration

## Decision 1: Store uploaded capacity in a dedicated reference table keyed by eSight Meter Code
- Decision: Introduce a dedicated persisted capacity-reference entity keyed by normalized eSight Meter Code, with the latest uploaded Name and Av Cap (kVA) captured from each valid row.
- Rationale: A dedicated table preserves uploaded business reference data independently of current Supply rows, supports future meter matching even when supply records are refreshed, and aligns with the requirement to keep static data available across sessions and periodic updates while still allowing harmless name drift to be refreshed.
- Alternatives considered:
  - Update only `Supply.available_capacity`: rejected because rows without an immediately matching supply would be lost and historical upload state becomes harder to inspect.
  - Store upload file blob only: rejected because report runtime needs normalized row-level lookup, not full-file parsing on demand.

## Decision 2: Use `openpyxl` for `.xlsx` ingestion
- Decision: Parse uploaded `.xlsx` files with `openpyxl` in Django view/service layer.
- Rationale: The feature scope is Excel-only (`.xlsx`), `openpyxl` is mature for workbook/worksheet parsing, supports variable column order, and avoids introducing heavier dataframe dependencies.
- Alternatives considered:
  - `pandas`: rejected as unnecessary overhead for simple schema validation/import and adds broader dependency surface.
  - `xlrd`: rejected due limited modern `.xlsx` support and maintenance constraints.

## Decision 3: Enforce partial-import semantics for row-level data errors
- Decision: Use partial import where valid rows are upserted and invalid rows are skipped with row-level error reporting.
- Rationale: This matches clarified requirements and allows operational progress while preserving visibility into data quality issues, including negative-capacity validation failures.
- Alternatives considered:
  - All-or-nothing import: rejected by explicit clarification.
  - Validate-then-confirm two-step import: rejected as extra interaction complexity not requested in scope.

## Decision 4: Match report supplies to uploaded capacity by eSight Meter Code only
- Decision: Resolve load-factor capacity by normalized eSight Meter Code only, using each supply's meter-code field at report build time.
- Rationale: Explicit clarification selected code-only matching and avoids ambiguous name-based collisions.
- Alternatives considered:
  - Composite Name + code matching: rejected by clarification.
  - Fallback name matching: rejected to prevent incorrect capacity assignment.

## Decision 5: Integrate upload controls into existing Settings page and view
- Decision: Extend `settings_panel_view`, `settings_panel.html`, and settings tests with a dedicated upload section and structured result summary.
- Rationale: Reuses existing operations entry point, minimizes navigation change, and aligns with requested user flow.
- Alternatives considered:
  - New standalone admin page: rejected because user explicitly requested settings-page integration.

## Decision 6: Present capacity units as kVA in load-factor UI and payload naming
- Decision: Update UI label to "Available Capacity (kVA)" and align report payload naming/usage to kVA semantics.
- Rationale: Requirement explicitly changes user-facing unit and avoids mixed unit terminology.
- Alternatives considered:
  - Keep `kW` labels for backward compatibility: rejected because it conflicts with feature requirement and data source semantics.

## Decision 7: Treat eSight Meter Code as the sole business key and overwrite Name on refresh
- Decision: When an uploaded row matches an existing normalized eSight Meter Code, update both `available_capacity_kva` and stored `name` using the latest uploaded row.
- Rationale: The user clarified that matching is code-only, so a differing Name should not block refresh. Replacing the stored Name preserves a current reference label without expanding the business key.
- Alternatives considered:
  - Keep the previous Name while updating capacity: rejected because it leaves stale metadata after a successful refresh.
  - Reject rows where Name differs: rejected because it would turn harmless naming drift into avoidable operational failures.

## Decision 8: Accept zero but reject negative capacity values
- Decision: Validate `Av Cap (kVA)` as numeric and non-negative; zero is accepted, negative values are rejected as row-level validation errors.
- Rationale: Negative available capacity is not meaningful for reporting, while zero remains a possible business-entered value and should not require artificial inflation.
- Alternatives considered:
  - Require strictly positive values: rejected because it forbids legitimate zero entries.
  - Normalize negatives to zero: rejected because silent coercion hides data quality issues.
