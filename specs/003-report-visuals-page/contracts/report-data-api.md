# Contract: Report Data API

**Feature**: 003-report-visuals-page
**Date**: 2026-07-01
**Status**: Final

---

## Endpoint

```
GET /api/report-data/
```

### Authentication

Requires an active Django session (existing `@login_required` pattern). Returns `302 → /login/` for unauthenticated requests.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `site_id` | integer | yes | Primary key of the `Site` record |
| `end_month` | string (`YYYY-MM`) | yes | The last month of the 12-month reporting window |

### Derived Window

- `start_month` = `end_month` minus 11 months (e.g., end `2026-05` → start `2025-06`)
- `prev_start_month` = `start_month` minus 12 months (for previous-year comparison series)
- `prev_end_month` = `end_month` minus 12 months

---

## Success Response

**Status**: `200 OK`
**Content-Type**: `application/json`

```json
{
  "site": {
    "id": 123,
    "name": "11 Charles II Street",
    "external_id": "abc-123"
  },
  "reporting_period": {
    "start_month": "2025-06",
    "end_month": "2026-05",
    "last_complete_month": "2026-05"
  },
  "overview": {
    "total_cost": 194511.29,
    "by_utility": [
      {
        "utility_type": "electricity",
        "label": "Electricity",
        "total_cost": 139594.77,
        "percentage": 71.77,
        "meter_numbers": ["1200061225556"]
      },
      {
        "utility_type": "gas",
        "label": "Gas",
        "total_cost": 2955.95,
        "percentage": 1.52,
        "meter_numbers": ["9336780803"]
      },
      {
        "utility_type": "water",
        "label": "Water",
        "total_cost": 51960.57,
        "percentage": 26.71,
        "meter_numbers": ["14552664", "3010332408W17"]
      }
    ]
  },
  "supplies": [
    {
      "id": 1,
      "utility_type": "electricity",
      "meter_number": "1200061225556",
      "name": "Electricity Fiscal Meter",
      "available_capacity_kw": 355.0,
      "monthly": {
        "months": ["2025-06", "2025-07", "2025-08", "2025-09", "2025-10",
                   "2025-11", "2025-12", "2026-01", "2026-02", "2026-03",
                   "2026-04", "2026-05"],
        "current_kwh":       [39152.86, 39030.03, 34979.36, 35614.89, 38058.94,
                               43652.82, 45254.60, 51164.65, 43602.62, 42208.04,
                               38244.64, 39419.29],
        "previous_year_kwh": [33755.70, 36123.91, 35473.23, 35707.63, 39078.06,
                               40585.04, 40264.39, 45392.13, 41271.16, 42435.76,
                               38637.29, 38169.80],
        "benchmark_kwh":     [null, null, null, null, null,
                               null, null, null, null, null,
                               null, null],
        "table": [
          {
            "month": "2025-06",
            "current_kwh": 39152.86,
            "previous_year_kwh": 33755.70,
            "gross_variance_kwh": 5397.16,
            "relative_variance_pct": 0.16
          }
        ]
      },
      "load_factor": {
        "month": "2026-05",
        "max_demand_kw": 121.1,
        "load_factor_pct": 43.77,
        "available_capacity_kw": 355.0,
        "halfhourly": [
          { "ts": "2026-05-01T00:00:00Z", "consumption_kwh": 20.5 },
          { "ts": "2026-05-01T00:30:00Z", "consumption_kwh": 19.8 }
        ]
      },
      "hh_comparison": {
        "month": "2026-05",
        "current": [
          { "ts": "2026-05-01T00:00:00Z", "consumption_kwh": 20.5 }
        ],
        "previous_year": [
          { "ts": "2025-05-01T00:00:00Z", "consumption_kwh": 18.3 }
        ]
      },
      "day_night": {
        "month": "2026-05",
        "day_start": "07:00",
        "day_end": "23:00",
        "records": [
          { "ts": "2026-05-01T00:00:00Z", "consumption_kwh": 20.5, "period": "night" },
          { "ts": "2026-05-01T07:00:00Z", "consumption_kwh": 33.2, "period": "day" }
        ]
      },
      "weekday_comparison": {
        "month": "2026-05",
        "days": [
          {
            "date": "2026-05-01",
            "day_name": "Friday",
            "records": [
              { "time": "00:00", "consumption_kwh": 19.8 },
              { "time": "00:30", "consumption_kwh": 18.9 }
            ]
          }
        ]
      },
      "weekend_comparison": {
        "month": "2026-05",
        "days": [
          {
            "date": "2026-05-02",
            "day_name": "Saturday",
            "records": [
              { "time": "00:00", "consumption_kwh": 19.1 }
            ]
          }
        ]
      }
    },
    {
      "id": 2,
      "utility_type": "gas",
      "meter_number": "9336780803",
      "name": "Gas Fiscal Meter",
      "available_capacity_kw": null,
      "monthly": {
        "months": ["2025-06", "2025-07"],
        "current_kwh":       [8055.91, 6782.76],
        "previous_year_kwh": [2495.03, 1834.14],
        "benchmark_kwh":     [5000.0,  5000.0],
        "table": [
          {
            "month": "2025-06",
            "current_kwh": 8055.91,
            "previous_year_kwh": 2495.03,
            "gross_variance_kwh": 5560.88,
            "relative_variance_pct": 2.23
          }
        ]
      },
      "hh_comparison": { "month": "2026-05", "current": [], "previous_year": [] },
      "day_night": null,
      "weekday_comparison": { "month": "2026-05", "days": [] },
      "weekend_comparison": { "month": "2026-05", "days": [] }
    },
    {
      "id": 3,
      "utility_type": "water",
      "meter_number": "3010332408W17",
      "name": "Water Fiscal Meter",
      "available_capacity_kw": null,
      "monthly": {
        "months": ["2025-06"],
        "current_m3":       [2328.89],
        "previous_year_m3": [748.00],
        "benchmark_m3":     [3000.0],
        "table": [
          {
            "month": "2025-06",
            "current_m3": 2328.89,
            "previous_year_m3": 748.00,
            "gross_variance_m3": 1580.89,
            "relative_variance_pct": 2.11
          }
        ]
      },
      "hh_comparison": null,
      "day_night": null,
      "weekday_comparison": null,
      "weekend_comparison": null
    }
  ]
}
```

---

## Field Definitions

### Top-level

| Field | Type | Notes |
|-------|------|-------|
| `site` | object | Basic site identity fields |
| `reporting_period` | object | Derived window boundaries |
| `overview` | object | Site-wide cost summary for the pie chart |
| `supplies` | array | One entry per `Supply` record for this site, sorted by `utility_type` in order: electricity → gas → water → other, then by `id` within each type |

### `overview.by_utility[]`

| Field | Type | Notes |
|-------|------|-------|
| `utility_type` | string | `electricity` / `gas` / `water` / `other` |
| `label` | string | Display name |
| `total_cost` | number | Sum of `InvoiceCost.cost` for all supplies of this type, for the reporting window |
| `percentage` | number | `total_cost / overview.total_cost * 100`, rounded to 2 dp |
| `meter_numbers` | string[] | `device_id` values (falling back to `name`, then `external_id`) for all supplies of this type |

### `supplies[].monthly`

| Field | Type | Notes |
|-------|------|-------|
| `months` | string[] | `YYYY-MM` values for each month in the 12-month window |
| `current_kwh` / `current_m3` | number[] | Monthly consumption — unit determined by `utility_type` (`kWh` for electricity/gas, `m3` for water) |
| `previous_year_kwh` / `previous_year_m3` | number\|null[] | Same month prior year; `null` if no data |
| `benchmark_kwh` / `benchmark_m3` | number\|null[] | From `Benchmark` model; `null` if not configured |
| `table` | object[] | One row per month; mirrors chart data plus computed variance fields |

### `supplies[].load_factor` (electricity only; `null` for gas/water)

| Field | Type | Notes |
|-------|------|-------|
| `month` | string | `YYYY-MM` of the most recent complete month |
| `max_demand_kw` | number | `max(HH.consumption) / 0.5` for the month |
| `load_factor_pct` | number | `total_monthly_kwh / (max_demand_kw * days * 24) * 100`, rounded to 2 dp |
| `available_capacity_kw` | number\|null | From `Supply.available_capacity`; `null` if not set |
| `halfhourly` | object[] | All HH records for the month; each has `ts` (ISO 8601 UTC) and `consumption_kwh` |

### `supplies[].hh_comparison` (electricity and gas; `null` for water)

| Field | Type | Notes |
|-------|------|-------|
| `month` | string | Most recent complete month |
| `current` | object[] | `{ ts, consumption_kwh }` for each HH interval in the month |
| `previous_year` | object[] | Same intervals from the prior year month; empty array if no data |

### `supplies[].day_night` (electricity only; `null` for gas/water)

| Field | Type | Notes |
|-------|------|-------|
| `month` | string | Most recent complete month |
| `day_start` | string | Always `"07:00"` |
| `day_end` | string | Always `"23:00"` |
| `records` | object[] | `{ ts, consumption_kwh, period }` where `period` is `"day"` or `"night"` based on local hour of `ts` |

### `supplies[].weekday_comparison` / `supplies[].weekend_comparison`

(electricity and gas; `null` for water)

| Field | Type | Notes |
|-------|------|-------|
| `month` | string | Most recent complete month |
| `days` | object[] | One entry per calendar day that falls on the relevant day type; each has `date` (ISO date), `day_name`, and `records` (array of `{ time: "HH:MM", consumption_kwh }`) |

---

## Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| `400 Bad Request` | `site_id` missing or non-integer | `{ "error": "site_id is required and must be an integer" }` |
| `400 Bad Request` | `end_month` missing or not `YYYY-MM` | `{ "error": "end_month is required in YYYY-MM format" }` |
| `404 Not Found` | No `Site` with given `site_id` | `{ "error": "Site not found" }` |
| `200 OK` (empty) | Site exists but has no supplies | `{ "site": {...}, "overview": { "total_cost": 0, "by_utility": [] }, "supplies": [] }` |
