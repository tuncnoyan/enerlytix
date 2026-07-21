# Feature Specification: Report Cover Pages

**Feature Branch**: `007-add-report-cover-pages`

**Created**: 2026-07-21

**Status**: Draft

**Input**: User description: "I want to add three additional pages to the report as they are seen in the Powerpoint file I uploaded. The first two pages are front cover pages, and the last one is the back cover. The first two cover pages should have editable fields, whilst the back cover can remain as a static image. The first page contains editable fields for site name, reporting month + Energy Report, current date, and optional client logo, with a default background image that can be replaced per report. The second page has editable title/text blocks for scope and contents with site-specific variable text and visual title listings. All cover pages must be included in draft/final reports and both PDF and PPTX downloads, with PPTX editable fields remaining editable." 

## Clarifications

### Session 2026-07-21

- Q: What file types and size limits are allowed for replacing the first-cover background image? → A: Allow JPG/JPEG/PNG/WebP up to 10 MB.
- Q: What date format should the first-cover date field use? → A: Fixed format DD MMMM YYYY (for example, 21 July 2026).
- Q: What is the required page order for the three cover pages in generated outputs? → A: Front cover page 1 then front cover page 2 at the beginning, and back cover as the final page.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate reports with integrated cover pages (Priority: P1)

As a report user, I can generate a report that automatically includes two front cover pages and one back cover page so every report has a complete branded structure.

**Why this priority**: Without complete cover pages in every output, the feature does not meet its core business purpose.

**Independent Test**: Generate both draft and final versions of a report and verify all three cover pages are present in the expected order.

**Acceptance Scenarios**:

1. **Given** a report ready for generation, **When** I create a draft report, **Then** front cover page 1 and front cover page 2 are inserted at the beginning and the back cover page is appended as the final page.
2. **Given** a report ready for generation, **When** I create a final report, **Then** the same cover-page order is preserved: front cover page 1, front cover page 2, report body pages, back cover page.

---

### User Story 2 - Edit first front-cover content per report (Priority: P1)

As a report user, I can edit defined fields on the first front cover page so the cover reflects the current site and client context.

**Why this priority**: First-cover personalization is a required user-facing part of the request.

**Independent Test**: Open report cover settings, edit the first cover fields, generate the report, and verify the updated values appear correctly.

**Acceptance Scenarios**:

1. **Given** a report with a selected site, **When** first cover defaults are loaded, **Then** the top-left title field is prefilled with the site name.
2. **Given** a report month is selected, **When** first cover defaults are loaded, **Then** the subtitle field is prefilled in the format "[Month Year] Energy Report".
3. **Given** the report is being prepared today, **When** first cover defaults are loaded, **Then** the date field is prefilled with the current date in DD MMMM YYYY format.
4. **Given** the user wants different branding, **When** they upload a replacement background image for the current report, **Then** the first cover uses the uploaded image instead of the default image.
5. **Given** the user provides a client logo, **When** the report is generated, **Then** the logo appears in the optional logo region on the first cover.

---

### User Story 3 - Edit second front-cover scope and contents text (Priority: P1)

As a report user, I can edit the Scope and Contents text areas on the second front cover page so the narrative and visual index fit the selected site and report content.

**Why this priority**: The second page carries explanatory and navigational content that must remain report-specific.

**Independent Test**: Edit scope and contents fields, generate output, and confirm the rendered second cover reflects edited values and required default text behavior.

**Acceptance Scenarios**:

1. **Given** the second cover is opened for editing, **When** default scope text is shown, **Then** it matches the provided reference wording with the site reference as a variable value.
2. **Given** report visuals are available, **When** default contents text is generated, **Then** it lists the visual titles in report order.
3. **Given** visual titles are listed in contents, **When** meter names exist for those visuals, **Then** each listed line appends the meter name in parentheses except "Total Utility Usage (£)".
4. **Given** the user edits scope or contents text, **When** the report is generated, **Then** those edits appear on the second cover page.

---

### User Story 4 - Preserve cover content correctly across download formats (Priority: P2)

As a report user, I can download report outputs in PDF and PPTX with cover pages included, and editable cover fields remain editable in PPTX.

**Why this priority**: Format parity and PPTX editability are required for downstream client delivery workflows.

**Independent Test**: Download PDF and PPTX for the same report and verify page presence in both files and editability of designated cover text fields in PPTX.

**Acceptance Scenarios**:

1. **Given** a report includes configured cover content, **When** I download as PDF, **Then** both front covers and the back cover are included in the exported file.
2. **Given** the same report, **When** I download as PPTX, **Then** both front covers and the back cover are included in the exported deck.
3. **Given** a downloaded PPTX, **When** I select first/second cover editable text fields, **Then** I can edit their text directly in a PowerPoint-compatible editor.
4. **Given** a downloaded PPTX, **When** I view the back cover, **Then** it appears as a static image without editable field requirements.

---

### Edge Cases

- What happens if no replacement first-cover image is uploaded? The default image remains in use.
- What happens if an uploaded replacement image has a different aspect ratio? The output still renders a full-page cover without clipping required text fields.
- What happens if a user uploads an unsupported image type or a file larger than 10 MB? The upload is rejected with a clear validation message and the default image remains active.
- What happens if report generation runs in a different user locale? The first-cover date still uses the fixed DD MMMM YYYY format.
- What happens if no client logo is provided? The optional logo area remains empty without blocking report generation.
- What happens if a site name or meter name is unusually long? Text remains visible and readable without overlapping other cover elements.
- What happens if a report has no available meter name for a visual line? The line is still shown without parentheses content.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST include three additional cover pages in each generated report: front cover page 1, front cover page 2, and a back cover page.
- **FR-001a**: The system MUST place front cover page 1 and front cover page 2 at the start of the report and place the back cover as the final page.
- **FR-002**: The three cover pages MUST be included in both draft and final report versions.
- **FR-003**: Front cover page 1 MUST provide editable fields for site name, report month/title text, report date, and an optional client logo area.
- **FR-004**: Front cover page 1 MUST default the site field to the selected site name for the report.
- **FR-005**: Front cover page 1 MUST default the report month/title field to "[Month Year] Energy Report" based on the report period.
- **FR-006**: Front cover page 1 MUST default the date field to the current date at the time of report generation.
- **FR-006a**: Front cover page 1 date MUST be rendered in fixed DD MMMM YYYY format (for example, 21 July 2026), independent of user locale.
- **FR-007**: Front cover page 1 MUST use the provided default background image unless the user uploads a replacement image for the current report.
- **FR-008**: The system MUST allow a user to upload a replacement first-cover background image scoped to the report they are currently editing.
- **FR-009**: Replacement first-cover background uploads MUST accept only JPG, JPEG, PNG, or WebP files up to 10 MB.
- **FR-010**: If a replacement first-cover upload is invalid due to type or size, the system MUST reject the upload with a clear validation message and preserve the default background image.
- **FR-011**: Front cover page 2 MUST provide editable title and body text areas for both Scope and Contents sections.
- **FR-012**: Front cover page 2 scope body text MUST use the provided baseline wording and substitute the site reference with a variable value.
- **FR-013**: Front cover page 2 contents section MUST list report visual titles in display order.
- **FR-014**: For front cover page 2 contents entries, meter names MUST be appended in parentheses for each line except "Total Utility Usage (£)".
- **FR-015**: The back cover page MUST use the provided static image content without requiring editable fields.
- **FR-016**: PDF downloads MUST include all three cover pages.
- **FR-017**: PPTX downloads MUST include all three cover pages.
- **FR-018**: In PPTX outputs, editable fields on front cover pages 1 and 2 MUST remain editable after download.
- **FR-019**: If any optional cover content is omitted (such as client logo), report generation MUST still succeed with a valid layout.

### Key Entities *(include if feature involves data)*

- **Report Cover Set**: The three-page cover package attached to each report output (first front cover, second front cover, back cover).
- **Cover Field Value**: User-editable text or image input bound to a specific cover field for a specific report.
- **Cover Template Asset**: Default visual assets used on covers, including default first-cover background and static back-cover image.
- **Visual Contents Entry**: A line item on the second cover contents section composed of visual title and optional meter name suffix.
- **Report Output Variant**: A generated report artifact type (draft, final, PDF, PPTX) that must consistently include cover pages.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of newly generated draft and final reports include all three required cover pages in the defined order.
- **SC-002**: 100% of PDF and PPTX downloads for covered reports include the same three cover pages.
- **SC-003**: At least 95% of users can complete first-cover field edits (site/title/date/logo) without assistance on first attempt.
- **SC-004**: 100% of PPTX exports preserve editability of designated first- and second-cover text fields.
- **SC-005**: 100% of second-cover default contents entries reflect report visual titles, with meter-name suffix behavior correctly applied for all eligible lines.
- **SC-006**: At least 95% of report generations with covers complete without layout-breaking text or missing required cover content.

## Assumptions

- The provided first-cover and back-cover reference images are approved for use in generated reports.
- Existing report generation flows already distinguish draft and final outputs and can accept additional pages.
- The current report context always includes a selected site and report period to prefill first-cover defaults.
- Visual titles used in the report are available for reuse in the second-cover contents section.
- When meter names are unavailable for a visual title, the contents line is shown without a meter-name suffix.
- Editable fields are limited to the explicitly requested front-cover areas; no additional cover objects are required to be editable.
