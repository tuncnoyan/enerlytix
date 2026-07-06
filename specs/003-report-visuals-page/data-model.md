# Data Model: Utility Usage Report Visuals Page

**Feature**: 003-report-visuals-page
**Date**: 2026-07-01
**Status**: Final

---

## Existing Models (unchanged — used by this feature)

The following models are already in `django_app/sitesync/models.py` and require no modification beyond what is listed in the "Schema Changes" section below.

| Model | Key Fields Used by Report | Notes |
|-------|--------------------------|-------|
| `Site` | `id`, `name`, `external_id` | Site name and ID appear in chart titles |
| `Supply` | `id`, `site` (FK), `utility_type`, `device_id`, `name`, `external_id` | Utility type drives section ordering; `device_id` is the meter number label |
| `HalfHourlyConsumption` | `supply` (FK), `canonical_month_key`, `source_period_start`, `consumption` | Used for HH charts, Load Factor, Day/Night, Weekday/Weekend visuals |
| `MonthlyConsumption` | `supply` (FK), `canonical_month_key`, `source_period_start`, `consumption` | Used for Monthly Usage charts and variance tables |
| `InvoiceCost` | `supply` (FK), `canonical_month_key`, `cost` | Used for Total Utility Usage (£) overview — summed per utility type |

---

## Schema Changes

### 1. `Supply` model — add `available_capacity` field

**Field**: `available_capacity`
**Type**: `DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)`
**Unit**: kW
**Default**: `None` (null)
**Validation**: Must be ≥ 0 if provided. No upper bound enforced at DB level.

**Behaviour when null**:
- The "Available Capacity (kW)" KPI card on the Load Factor visual shows "N/A".
- The Available Capacity horizontal reference line is omitted from the Load Factor chart.

**Rationale**: Available Capacity is a static contracted property of an electricity supply meter. Nullable because not all supplies (especially gas and water) have a contracted capacity value, and not all electricity supplies may have it populated initially.

---

### 2. New `Benchmark` model

**Purpose**: Stores optional monthly benchmark consumption/usage targets per supply, displayed as a reference series on Monthly Usage charts.

**Django model**:

```python
class Benchmark(models.Model):
    UNIT_CHOICES = [
        ('kWh', 'kWh'),
        ('m3',  'm³'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supply = models.ForeignKey(
        Supply,
        on_delete=models.CASCADE,
        related_name='benchmarks',
    )
    canonical_month_key = models.CharField(
        max_length=7,
        db_index=True,
        help_text="YYYY-MM format, e.g. '2026-05'",
    )
    value = models.DecimalField(
        max_digits=16,
        decimal_places=6,
        help_text="Benchmark consumption value for this month",
    )
    unit = models.CharField(
        max_length=3,
        choices=UNIT_CHOICES,
        default='kWh',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['supply', 'canonical_month_key'],
                name='uniq_benchmark_supply_month',
            ),
        ]
        indexes = [
            models.Index(fields=['supply', 'canonical_month_key']),
        ]

    def __str__(self):
        return f"Benchmark {self.supply_id} {self.canonical_month_key} {self.value} {self.unit}"
```

**Behaviour when absent**: If no `Benchmark` record exists for a supply+month combination, the benchmark series for that month is omitted (rendered as `null` in the chart data array). Chart.js skips null data points by default.

---

## Computed / Derived Values (not persisted)

These values are calculated at query time by the report data API and are not stored in the database.

### Maximum Demand (kW)

- **Formula**: `max(consumption) / 0.5` where `consumption` is in kWh and the interval is 30 minutes
- **Scope**: Calculated per supply, per reporting month (the most recent complete month for the Load Factor visual)
- **Implementation**: Django ORM `Max()` aggregate on `HalfHourlyConsumption.consumption` filtered by `supply` and `canonical_month_key`, result divided by `Decimal('0.5')`

### Load Factor (%)

- **Formula**: `total_monthly_consumption / (max_demand_kw * days_in_month * 24)`
- **Where**:
  - `total_monthly_consumption` = sum of all `HalfHourlyConsumption.consumption` records for the supply in the month (kWh)
  - `max_demand_kw` = Maximum Demand as computed above
  - `days_in_month` = calendar days in the reporting month (28–31)
- **Result**: Decimal (0.0–1.0 range); multiplied by 100 for display as a percentage

### Gross Variance (kWh or m³)

- **Formula**: `current_consumption - previous_year_consumption`
- **Scope**: Per supply, per month in the 12-month window

### Relative Variance (%)

- **Formula**: `gross_variance / previous_year_consumption` (returns `null` if previous year = 0 or absent)
- **Display**: Rounded to 2 decimal places

---

## Transient / Session-Scoped Data (not persisted)

### VisualComment

Not stored in the database. Managed entirely in browser memory (JavaScript `Map` keyed by visual section ID). Lost on page refresh or navigation.

| Field | Type | Notes |
|-------|------|-------|
| `section_id` | string | e.g., `"electricity-1200061225556-monthly-chart"` |
| `text` | string | Free-form user-entered text |

---

## Migration

**File**: `django_app/sitesync/migrations/0004_supply_available_capacity_benchmark.py`

**Operations**:
1. `AddField` — `Supply.available_capacity` (nullable `DecimalField`)
2. `CreateModel` — `Benchmark` (with `UniqueConstraint` and index)

**Reversibility**: Both operations are fully reversible (`RemoveField`, `DeleteModel`).

**Zero-downtime safe**: `AddField` with `null=True` and `CreateModel` do not lock the table in PostgreSQL or SQLite.
