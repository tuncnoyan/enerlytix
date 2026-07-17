# Contract: Report Capacity Resolution

## Producer
- Function scope: report payload assembly for electricity load factor sections.
- Source modules: `sitesync/views.py` and related report helpers.

## Lookup Rule
- Match key: normalized supply eSight Meter Code only.
- Supply key source: supply meter code field used by report integration (`Supply.device_id`).
- Reference source: capacity-reference table `esight_meter_code`.

## Output Shape
- Load-factor payload field:
  - `available_capacity_kva` (number or `null`)
- Existing fields remain unchanged unless explicitly renamed in implementation tasks.

## Behavioral Rules
- If a matching capacity reference exists, `available_capacity_kva` is populated.
- If no matching key exists, `available_capacity_kva` is `null` and UI shows `N/A`.
- Stored `name` metadata is not used for lookup and does not block a match when it differs from current supply display text.
- Label contract for UI metric card: `Available Capacity (kVA)`.

## Non-Regression Rules
- Load factor percentage and maximum demand calculations remain unchanged.
- Non-electricity supply rendering remains unaffected.
- Report generation must continue even when no capacity records exist.
