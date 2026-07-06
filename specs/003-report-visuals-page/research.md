# Research: Utility Usage Report Visuals Page

**Feature**: 003-report-visuals-page
**Date**: 2026-07-01
**Status**: Complete — all NEEDS CLARIFICATION items resolved

---

## 1. Chart Library Selection

**Decision**: Chart.js 4.x loaded from CDN

**Rationale**:
- Chart.js renders to `<canvas>` elements, which html2canvas captures accurately for PDF export — this is the single most important constraint for this feature.
- Chart.js 4.x supports all required chart types: bar (grouped/stacked), line (multi-series overlaid), pie/doughnut.
- No build step required; single script tag from CDN (`cdn.jsdelivr.net`).
- Large ecosystem, extensive documentation, compatible with vanilla JS pattern already used in Enerlytix.
- Chart.js 4 defaults to a responsive, retina-aware canvas sizing model that works at 1280px+ widths.

**CDN reference**:
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.9/dist/chart.umd.min.js"></script>
```

**Alternatives considered**:
- Apache ECharts: More powerful but heavier (~1 MB); canvas-based so PDF capture works, but overkill for this feature set.
- Plotly.js: SVG-based; html2canvas does not reliably capture SVG in all browsers. **Rejected.**
- D3.js: SVG-based; same html2canvas limitation. Also requires significant implementation effort for standard chart types. **Rejected.**

---

## 2. Client-Side PDF Generation

**Decision**: html2canvas 1.x + jsPDF 2.x, both loaded from CDN

**Rationale**:
- html2canvas converts a DOM subtree (including Chart.js canvas elements) to an image, which jsPDF embeds into a PDF page.
- Chart.js's `<canvas>` elements are natively supported by html2canvas — no SVG serialization issues.
- Both libraries are well-maintained and available as UMD bundles (no build step).
- jsPDF supports landscape A4 pages, which matches the spec requirement for landscape PDF output.
- Comment boxes (plain `<textarea>` or `<div contenteditable>`) are captured as part of the DOM snapshot.

**CDN references**:
```html
<script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/jspdf@2.5.2/dist/jspdf.umd.min.js"></script>
```

**Known limitations & mitigations**:
- html2canvas does not capture cross-origin images (e.g., Google Fonts). Mitigation: use `font-display: swap` with a local fallback font stack; all chart labels use system fonts only.
- html2canvas captures at screen resolution. Mitigation: use `scale: 2` option for retina-quality PDF output.
- Very large pages may be slow to capture. Mitigation: capture section-by-section (one section per PDF page) rather than the full page at once.

**Alternatives considered**:
- Print CSS + `window.print()`: Cannot reliably produce a PDF with consistent layout across browsers on Windows; user must manage the print dialog. **Rejected.**
- Server-side rendering (Puppeteer/WeasyPrint): Requires additional server process; violates least-privilege principle (Node.js or Python Playwright install); increases container complexity. **Rejected.**

---

## 3. Month Picker (Dashboard)

**Decision**: Native HTML `<input type="month">` element

**Rationale**:
- Supported by all modern browsers (Chrome, Edge, Firefox, Safari 14.1+). Enerlytix targets desktop at 1280px+, which means modern browsers.
- Zero dependencies; renders a native month selector dialog consistent with the OS.
- Value is a `YYYY-MM` string — exactly the format used by `canonical_month_key` throughout the codebase.
- Styled with CSS to match the existing input styling in `site_list.html`.

**Default value logic**: Set to the most recent complete calendar month on page load via JavaScript:
```js
const now = new Date();
const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
input.value = `${lastMonth.getFullYear()}-${String(lastMonth.getMonth() + 1).padStart(2, '0')}`;
```

**Alternatives considered**:
- Custom month picker widget: Adds JS code complexity with no UX benefit for a standard date selector. **Rejected.**

---

## 4. Report Data API Design

**Decision**: Single JSON endpoint `GET /api/report-data/` with query params `site_id` and `end_month`

**Rationale**:
- One round-trip per report load keeps implementation simple and matches the existing API pattern (`/api/consumption-display/`).
- The endpoint assembles all data server-side (monthly aggregations, HH records, load factor calculations, benchmark lookups) and returns a single JSON payload.
- Computed values (Maximum Demand, Load Factor) are calculated server-side in Python to keep JS light and to enable server-side unit testing of the calculations.
- The response payload is structured by supply, with per-utility-type visual data nested under each supply object.

**Performance estimate**: For a site with 3 supplies × 12 months × 2 years of monthly data (72 rows per supply), monthly data is < 1 ms to query. HH data for 1 month × 1 supply ≈ 1 488 records (31 days × 48 intervals) — single indexed query by `supply + canonical_month_key`, expected < 50 ms. Total response time < 500 ms for typical sites.

---

## 5. Benchmark Data Storage

**Decision**: New `Benchmark` model in `sitesync/models.py`

**Rationale**:
- Benchmarks are per-supply, per-month reference values. They are optional (absent = no benchmark series shown).
- Stored as a separate model (not a JSON field on `Supply`) to allow future management via Django admin or API.
- Unit field (`kWh` / `m3`) is stored explicitly to avoid ambiguity when displaying water vs. energy benchmarks.

**Model definition** (see `data-model.md` for full schema):
```python
class Benchmark(models.Model):
    supply = ForeignKey(Supply, ...)
    canonical_month_key = CharField(max_length=7)  # YYYY-MM
    value = DecimalField(max_digits=16, decimal_places=6)
    unit = CharField(choices=[('kWh', 'kWh'), ('m3', 'm³')])
```

---

## 6. Available Capacity Data Storage

**Decision**: Add `available_capacity` nullable `DecimalField` to `Supply` model

**Rationale**:
- Available Capacity (kW) is a static property of a supply (its contracted maximum), not a time-series value.
- Adding it directly to `Supply` avoids a join and is the simplest storage pattern.
- Nullable (`null=True, blank=True`) because not all supplies have a contracted capacity; absence is explicitly handled in the UI (shows "N/A" card, omits line from Load Factor chart).

---

## 7. Day/Night Boundary Constants

**Decision**: Day = 07:00–22:59 (inclusive), Night = 23:00–06:59 (inclusive); derived from `source_period_start` hour

**Rationale**: Confirmed in clarification session (Q2). The boundary 07:00–23:00 is the standard UK commercial electricity tariff split. For halfhourly data, a record starting at 07:00 is "Day"; a record starting at 23:00 is "Night". This is evaluated purely on the local time component of `source_period_start`.

**Implementation note**: `source_period_start` is stored as UTC in the database. The report API must convert to the site's local time (assumed UK/Europe London) before applying the day/night boundary. For this sprint, local time is assumed to be the same as UTC+0/+1 (UK); a `timezone` field on `Site` is a future enhancement.

---

## 8. Previous Year Same Month Logic

**Decision**: Previous year = same `canonical_month_key` with year decremented by 1

**Rationale**: Consistent with the existing data model's `canonical_month_key = YYYY-MM` convention. A previous-year lookup for `2026-05` fetches records with `canonical_month_key = 2025-05`. If no data exists for that key, the previous year series is absent (null array) — the chart renders without it rather than erroring.

---

## 9. Meter Number Display

**Decision**: Use `device_id` field from `Supply` as the meter number label in chart titles and nav pane

**Rationale**: The sample PDF shows meter numbers (e.g., `1200061225556`) in chart subtitles. In the existing `Supply` model, `device_id` stores the meter/sensor identifier. `external_id` stores the Etainabl platform account ID (not the meter number). `name` stores a human-readable supply name. `device_id` matches the sample PDF meter number pattern.

**Fallback**: If `device_id` is blank/null, fall back to `name`, then `external_id`.
