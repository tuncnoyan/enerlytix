# Quickstart Validation Guide: Utility Usage Report Visuals Page

**Feature**: 003-report-visuals-page
**Date**: 2026-07-01

---

## Prerequisites

1. Django dev server running (`python manage.py runserver` from `django_app/`)
2. Migration `0004_supply_available_capacity_benchmark` applied (`python manage.py migrate`)
3. At least one `Site` with at least one `Supply` in the database (synced via the dashboard's "Refresh data" button)
4. At least 1 month of `HalfHourlyConsumption` and `MonthlyConsumption` records imported for that supply (via "Load Data")
5. At least 1 month of `InvoiceCost` records imported for that supply

---

## Validation Scenarios

### SC-001 — Report page opens in < 5 seconds

**Steps**:
1. Open the dashboard (`/`) and select exactly one site.
2. Set the month picker to the most recent complete calendar month.
3. Click **Create Report**.
4. Start a timer when the button is clicked; stop it when all chart canvases are fully drawn.

**Expected**: The report page is fully rendered (all charts visible, no spinners) within 5 seconds.

**Failure signal**: Charts remain empty or spinner is still visible after 5 seconds.

---

### SC-002 — All charts and tables render without errors

**Steps**:
1. Open the report page for a site that has electricity, gas, and water supplies with complete 12-month data.
2. Scroll through the entire report page.

**Expected**:
- A "Site Overview" section appears first with the Total Utility Usage pie chart and table.
- An "Electricity" section follows, containing for each electricity supply: Monthly Usage bar chart + table, Load Factor chart + KPI cards, HH Comparison chart, Day/Night chart, Weekday chart, Weekend chart.
- A "Gas" section follows with: Monthly Usage bar chart + table, HH Comparison chart, Weekday chart, Weekend chart.
- A "Water" section follows with: Monthly Usage bar chart + table.
- No console errors in browser DevTools.
- No "no data available" placeholders (given complete data).

---

### SC-003 — Utility section is skipped when no supplies exist for that type

**Steps**:
1. Ensure the test site has electricity and water supplies but NO gas supply.
2. Open the report page for that site.

**Expected**:
- The Gas section is absent from the page body.
- The left navigation pane has no "Gas" entry.
- Electricity and Water sections are present and correctly ordered.

---

### SC-004 — Multiple supplies of the same type render as separate visual sets

**Steps**:
1. Ensure the test site has two water supplies (e.g., two `Supply` records with `utility_type='water'`).
2. Open the report page.

**Expected**:
- Two sets of Water visuals appear within the Water section, one per supply.
- Each set is labelled with its meter number (`device_id`).
- The left navigation pane shows two entries under Water, each labelled by meter number.

---

### SC-005 — Create Report button is disabled with no site selected

**Steps**:
1. Open the dashboard with no site selected (fresh load).
2. Observe the "Create Report" button state.

**Expected**: Button is visually disabled (greyed out). Hovering shows a tooltip: "Select a site to create a report" (or similar). Clicking has no effect.

---

### SC-006 — Create Report button is disabled with multiple sites selected

**Steps**:
1. Open the dashboard and select two or more sites using the checkboxes.
2. Observe the "Create Report" button state.

**Expected**: Button becomes (or remains) disabled. Hovering shows a tooltip: "Select only one site to create a report" (or similar).

---

### SC-007 — Comment boxes accept text and retain it in session

**Steps**:
1. Open the report page.
2. Click the comment box beneath the Monthly Electricity Usage bar chart.
3. Type a paragraph of text.
4. Scroll down to another visual, then scroll back.

**Expected**: The typed text is still present in the comment box.

---

### SC-008 — PDF download includes all visuals and comments

**Steps**:
1. Open the report page.
2. Type a comment in at least two comment boxes (one near the top, one near the bottom).
3. Click **Download as PDF**.

**Expected**:
- A PDF file downloads automatically.
- The PDF opens in a PDF viewer without errors.
- The PDF contains all visible charts and tables in the correct order (Site Overview → Electricity → Gas → Water).
- Each comment appears directly below its corresponding visual in the PDF.
- The PDF is landscape-oriented.

---

### SC-009 — Load Factor KPI values are arithmetically correct

**Steps**:
1. Open the report page for a site with an electricity supply that has HH data for the most recent complete month.
2. Note the displayed **Maximum Demand (kW)**, **Load Factor (%)**, and **Available Capacity (kW)** cards.
3. Verify manually:

   ```
   max_demand_kw = max(HH.consumption for month) / 0.5
   load_factor_pct = sum(HH.consumption for month) / (max_demand_kw × days_in_month × 24) × 100
   ```

   Query the database directly:
   ```sql
   SELECT MAX(consumption) / 0.5 AS max_demand
   FROM sitesync_halfhourlyconsumption
   WHERE supply_id = <id> AND canonical_month_key = '2026-05';
   ```

**Expected**: Values displayed in the UI match the manually computed values (within rounding to 2 decimal places).

---

### SC-010 — "No data available" state for missing HH data

**Steps**:
1. Open the report page for an electricity supply that has monthly data but NO halfhourly data for the most recent complete month.

**Expected**:
- The Load Factor visual shows a "No halfhourly data available" placeholder (not blank, not an error).
- The HH Comparison, Day/Night, Weekday, and Weekend charts show the same placeholder.
- Monthly Usage chart and table still render correctly (they use `MonthlyConsumption`, not HH data).

---

## API Smoke Test

```bash
# From the Django project directory (django_app/)
# Requires a valid session cookie — use browser DevTools to copy the sessionid cookie value
# Replace SITE_ID and END_MONTH with real values

curl -s \
  -H "Cookie: sessionid=<your-session-id>" \
  "http://localhost:8000/api/report-data/?site_id=SITE_ID&end_month=2026-05" \
  | python -m json.tool | head -60
```

**Expected**: Valid JSON matching the structure defined in [contracts/report-data-api.md](contracts/report-data-api.md). `supplies` array is non-empty, `overview.total_cost` is > 0.

---

## References

- API contract: [contracts/report-data-api.md](contracts/report-data-api.md)
- Data model: [data-model.md](data-model.md)
- Feature spec: [spec.md](spec.md)
