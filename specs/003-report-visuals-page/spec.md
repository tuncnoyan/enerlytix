# Feature Specification: Utility Usage Report Visuals Page

**Feature Branch**: `003-report-visuals-page`

**Created**: 2026-07-01

**Status**: Draft

**Input**: User description: "Add a visuals/report page to Enerlytix with charts and tables matching the sample report design, driven by existing data, accessible via a Create Report button on the dashboard, downloadable as PDF, with editable comment boxes per visual."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate and View Utility Report (Priority: P1)

An energy manager navigates to the Enerlytix dashboard and clicks the "Create Report" button. They are taken to the Report Visuals page, which automatically loads all available utility data for the site and displays the full suite of charts and tables — organised by utility type in the order Electricity, Gas, Water. Sections for utility types with no associated supply are skipped automatically.

**Why this priority**: This is the primary deliverable of the sprint. Without the ability to view the visuals, none of the supporting features have value.

**Independent Test**: Can be fully tested by navigating to the dashboard, clicking "Create Report", and confirming all expected visual sections render with real data from existing supplies.

**Acceptance Scenarios**:

1. **Given** a site with electricity, gas, and water supplies, **When** the user clicks "Create Report", **Then** the report page opens and all three utility sections are displayed in order: Electricity, Gas, Water.
2. **Given** a site with electricity supplies only (no gas), **When** the report page loads, **Then** the Gas section is absent and Water follows directly after Electricity.
3. **Given** a site with multiple supplies of the same utility type, **When** the report page loads, **Then** all supplies for that utility type are grouped within the same section.
4. **Given** the report page is open, **When** the user views the page, **Then** a left-side navigation pane lists all visual sections with anchor links, enabling single-click scroll-to-section.

---

### User Story 2 - Add Comments to Visuals (Priority: P2)

An energy manager reviews the report visuals and wants to annotate specific charts with interpretive commentary before sharing the report. Beneath each chart or table, they find an editable text area where they can type free-form text. Their comments persist as long as the report page remains open.

**Why this priority**: Comments are the key differentiator between a raw data page and a professional report. They enable the energy manager to add narrative context before downloading.

**Independent Test**: Can be fully tested independently by opening the report page, typing text into a comment box beneath any visual, and confirming the text is retained until the page session ends.

**Acceptance Scenarios**:

1. **Given** the report page is displayed, **When** the user clicks the comment area beneath any visual, **Then** a text input area becomes active and accepts free-form text entry.
2. **Given** the user has typed a comment, **When** they scroll away and return to that visual, **Then** the typed comment is still present (within the same session).
3. **Given** a comment box is empty, **When** the PDF is generated, **Then** the comment area is rendered as blank (no placeholder text visible in the PDF).

---

### User Story 3 - Download Report as PDF (Priority: P3)

After reviewing visuals and adding comments, the energy manager clicks a "Download as PDF" button. The system generates a formatted PDF file that includes all visible charts, tables, and any typed comments, formatted as a presentation-quality document. The download starts automatically.

**Why this priority**: PDF export is the primary output artefact that allows the report to be shared with stakeholders outside the application.

**Independent Test**: Can be fully tested by completing comments and clicking Download. The output PDF must contain all visible visuals and their corresponding comments.

**Acceptance Scenarios**:

1. **Given** the report page is displayed with charts loaded, **When** the user clicks "Download as PDF", **Then** a PDF file is generated and downloaded automatically.
2. **Given** the user has entered comments on multiple visuals, **When** the PDF is downloaded, **Then** each comment appears directly below its corresponding visual in the PDF.
3. **Given** the PDF is generated, **Then** each page of the PDF corresponds to a visual section, maintaining the same visual order (Electricity, Gas, Water) as the on-screen report.

---

### User Story 4 - Navigate Report Page (Priority: P4)

The energy manager can navigate within the report page using both the left navigation pane and the top ribbon. The top ribbon includes links back to the Dashboard and any other main navigation pages in the application.

**Why this priority**: Navigation usability is important for a polished experience but does not block core reporting functionality.

**Independent Test**: Can be fully tested independently by using only the left pane and top ribbon links and confirming all navigation destinations are reachable.

**Acceptance Scenarios**:

1. **Given** the report page is displayed, **When** the user clicks a section link in the left pane, **Then** the page scrolls to that visual section smoothly.
2. **Given** the report page is displayed, **When** the user clicks "Dashboard" in the top ribbon, **Then** the user is navigated back to the dashboard page.

---

### Edge Cases

- What happens when no halfhourly data is available for a supply in the selected reporting period? The Load Factor, HH Comparison, and Day/Night charts for that supply must show a clear "no data available" state rather than blank or broken visuals.
- What happens when a supply has data for the current period but no previous-year data? Previous Year series must render as empty/absent without breaking the chart.
- What happens when only one month of data exists for a supply? Monthly charts must render with a single bar/data point and not error.
- What happens if a site has no supplies at all? The report page must display a user-friendly "No data available" message rather than an empty visual area.
- What happens when the reporting period contains an incomplete month (e.g., the current month mid-stream)? Partial months must be shown without distorting benchmark comparisons.

---

## Requirements *(mandatory)*

### Functional Requirements

**Dashboard Entry Point**
- **FR-001**: The dashboard page MUST display a "Create Report" button positioned directly after the existing "Load Data" button.
- **FR-002**: Clicking "Create Report" MUST navigate the user to the Report Visuals page for the currently selected site.

**Report Page Layout**
- **FR-003**: The Report Visuals page MUST display a fixed left-side navigation pane listing all visual sections available for the site.
- **FR-004**: The top ribbon on the Report Visuals page MUST include navigation links consistent with other pages in the application (e.g., Dashboard link and any other existing navigation items).
- **FR-005**: Visual sections MUST be ordered as: Electricity first, Gas second, Water third.
- **FR-006**: If a utility type has no associated supply for the site, its entire section MUST be omitted from the report page and from the left navigation pane.
- **FR-007**: If a utility type has multiple supplies, all supplies for that type MUST be displayed within the same section, one after another.

**Colour Scheme**
- **FR-008**: All visual colours (chart series, highlights, backgrounds) MUST conform to the project colour scheme guideline already established for Enerlytix.

**Electricity Visuals** *(per electricity supply)*
- **FR-009**: The report MUST display a Total Utility Usage (£) summary showing a table of all utility meters with total costs and a pie chart showing cost distribution by utility type, labelled with utility name and percentage.
- **FR-010**: The report MUST display a Monthly Electricity Usage bar chart showing current consumption (kWh), previous year same month (kWh), and benchmark (kWh) series for each month in the 12-month reporting period.
- **FR-011**: The report MUST display a Monthly Electricity Usage table with columns: Date, Last 12 Months (kWh), Prev. 12 Months (kWh), Gross Variance (kWh), Relative Variance (%).
- **FR-012**: The report MUST display an Electricity Load Factor visual, showing a time-series line chart plotting halfhourly consumption (kWh), Maximum Demand (kW) as a constant line for the month, and Available Capacity (kW) as a constant line. Below the chart, three KPI cards MUST display: Load Factor (%), Maximum Demand (kW), and Available Capacity (kW). The Load Factor visual covers the most recent complete month by default.
- **FR-013**: Maximum Demand (kW) MUST be calculated as: the highest single halfhourly consumption value (kWh) in the reporting month divided by 0.5.
- **FR-014**: Load Factor (%) MUST be calculated as: monthly consumption (kWh) ÷ (Maximum Demand (kW) × number of days in month × 24).
- **FR-015**: Available Capacity (kW) is stored as a supply attribute and MUST be displayed as provided; it does not require calculation.
- **FR-016**: The report MUST display an HH Electricity Data Comparison – Last Month line chart showing halfhourly consumption for the current year (green) and previous year same month (grey) across all halfhour intervals in the most recent complete month.
- **FR-017**: The report MUST display an HH Electricity Day/Night Usage – Last Month bar chart showing all halfhourly consumption readings across the most recent complete month as a stacked or grouped bar chart (one bar per halfhour interval per day).
- **FR-018**: The report MUST display a Daily Comparison – Weekday Usage chart showing halfhourly consumption profiles for each individual weekday in the most recent complete month, rendered as overlaid line series, one per day.
- **FR-019**: The report MUST display a Daily Comparison – Weekend Usage chart showing halfhourly consumption profiles for each individual weekend day in the most recent complete month, rendered as overlaid line series, one per day.

**Gas Visuals** *(per gas supply)*
- **FR-020**: The report MUST display a Monthly Gas Usage bar chart showing current consumption (kWh), previous year same month (kWh), and benchmark (kWh) series for each month in the 12-month reporting period.
- **FR-021**: The report MUST display a Monthly Gas Usage table with columns: Date, Last 12 Months (kWh), Prev. 12 Months (kWh), Gross Variance (kWh), Relative Variance (%).
- **FR-022**: The report MUST display an HH Gas Data Comparison – Last Month chart showing halfhourly gas consumption for the current year and previous year same month.
- **FR-023**: The report MUST display a Daily Comparison – Weekday Usage (Gas) chart showing halfhourly gas consumption profiles per weekday in the most recent complete month.
- **FR-024**: The report MUST display a Daily Comparison – Weekend Usage (Gas) chart showing halfhourly gas consumption profiles per weekend day in the most recent complete month.

**Water Visuals** *(per water supply)*
- **FR-025**: The report MUST display a Monthly Water Usage bar chart showing current consumption (m³), previous year same month (m³), and benchmark (m³) series for each month in the 12-month reporting period.
- **FR-026**: The report MUST display a Monthly Water Usage table with columns: Date, Last 12 Months (m³), Prev. 12 Months (m³), Gross Variance (m³), Relative Variance (%).

**Comment Boxes**
- **FR-027**: Each chart and table visual MUST have an editable text area directly beneath it on the report page.
- **FR-028**: Comment boxes MUST accept free-form text and retain their content for the duration of the browser session.
- **FR-029**: Comment boxes MUST render their content in the downloaded PDF, positioned directly below the corresponding visual.

**PDF Download**
- **FR-030**: The report page MUST include a "Download as PDF" button that triggers a client-side PDF generation and download.
- **FR-031**: The generated PDF MUST include all visible charts, tables, and comments in the same visual order as the on-screen report.
- **FR-032**: The PDF presentation format MUST be landscape-oriented and styled for stakeholder distribution.

### Key Entities

- **Report**: A transient, session-scoped view aggregating visual data for one site and one 12-month reporting period. Not persisted in the database.
- **Supply**: An existing entity representing an electricity, gas, or water meter associated with a site, with attributes including utility type, meter number, and available capacity.
- **HalfHourlyConsumption**: An existing entity storing 30-minute interval energy readings per supply per timestamp.
- **MonthlyConsumption**: An existing entity storing aggregated monthly consumption per supply.
- **InvoiceCost**: An existing entity storing financial cost data per supply per billing period.
- **Benchmark**: A configured reference value (kWh or m³) per supply per month, used for benchmark series in charts.
- **VisualComment**: A transient, session-scoped text entry associated with a specific visual section on the report page. Not persisted.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can navigate from the dashboard to a fully rendered report page for any site in under 5 seconds after clicking "Create Report".
- **SC-002**: All charts and tables for a 12-month period (covering electricity, gas, and water) render without errors or missing series for any site that has complete data.
- **SC-003**: A user can add comments to all visible comment boxes and download a PDF that includes all visuals and comments within 2 minutes of arriving on the report page.
- **SC-004**: The downloaded PDF is a valid, openable PDF file that matches the on-screen report layout, suitable for sharing with external stakeholders.
- **SC-005**: Visual sections for utility types with no supplies are absent from both the on-screen report and the downloaded PDF with 100% consistency.
- **SC-006**: Load Factor, Maximum Demand, and Available Capacity KPI values on the Electricity Load Factor visual are arithmetically correct (verifiable by manual calculation from raw halfhourly data).
- **SC-007**: The report page is usable on standard desktop resolutions (1280×768 and above) without horizontal scroll or layout breakage.

---

## Assumptions

- All required data (halfhourly consumption, monthly consumption, invoice cost, benchmark, available capacity) is already stored in the existing Enerlytix database and accessible via the current data models.
- The "reporting period" defaults to the last 12 complete calendar months relative to today's date unless a future date-range selector is added.
- The "most recent complete month" used for load factor and HH charts is the last fully elapsed calendar month.
- Available Capacity (kW) is stored as an existing attribute on the Supply model; if no value is present, the Available Capacity KPI card shows "N/A" and the Available Capacity line is omitted from the Load Factor chart.
- Benchmark values are optional; if no benchmark is configured for a supply, the benchmark series is omitted from charts rather than shown as zero.
- Comment box content is session-only and is not persisted to the database in this feature iteration.
- The colour scheme guideline referenced is the one already defined and used in the existing Enerlytix UI; no new brand colours will be introduced.
- PDF generation will be handled client-side (browser-based) to avoid server-side rendering complexity.
- The report page is for authenticated users only; no additional access-control changes are needed beyond existing session authentication.
- Mobile or small-screen layouts are out of scope for this iteration.
