# Feature Specification: Download as PPTX

**Feature Branch**: `006-download-pptx`

**Created**: 2026-07-20

**Status**: Draft

**Input**: User description: "I want to add a \"Download as PPTX\" feature right beside the \"Download as PDF\" button on the report page, to create report files also in editable PowerPoint format. Visuals, tables and headers should be transferred as image. They don't need to be editable. However, comment boxes, should be editable. Also, the page should also be editable, for example the size or the location of an image can be changed. The page layout should be landscape and its size should be 16:9."

## Clarifications

### Session 2026-07-20

- Q: How much of each exported slide should be natively editable? -> A: Hybrid text reconstruction. Headers and key labels should be rebuilt as editable text boxes, while visuals and tables remain image-based and comment boxes stay editable.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download a PPTX report from the report page (Priority: P1)

As a report user, I can click a Download as PPTX button beside Download as PDF and receive a PowerPoint file for the current report.

**Why this priority**: This is the core user value and the minimum viable feature.

**Independent Test**: Open a report, click the PPTX button, and confirm a PowerPoint file downloads and opens successfully.

**Acceptance Scenarios**:

1. **Given** a report page with report content visible, **When** I click Download as PPTX, **Then** the system downloads a PowerPoint file for that report.
2. **Given** a report page with no export errors, **When** I download the PPTX file, **Then** the file opens in a PowerPoint-compatible editor.

---

### User Story 2 - Preserve editable comments and headers in the exported deck (Priority: P1)

As a report user, I can edit exported comment boxes and key text labels after download so I can revise the report in PowerPoint.

**Why this priority**: Editable comments and labels are a primary reason to choose PPTX over PDF.

**Independent Test**: Download a PPTX, open it in a PowerPoint editor, and edit a comment box and a section header without recreating the file.

**Acceptance Scenarios**:

1. **Given** a report with comment text entered in one or more sections, **When** I export to PPTX, **Then** each comment box appears as editable text in the deck.
2. **Given** an exported PPTX with a comment box and section header, **When** I change the text in PowerPoint, **Then** the deck accepts the edit without converting those text elements to flat images.

---

### User Story 3 - Adjust slide content after export (Priority: P2)

As a report user, I can move or resize exported slide elements so I can fine-tune the presentation.

**Why this priority**: Editable slide composition is needed for practical reuse of the report in presentations.

**Independent Test**: Export a PPTX, open it, and confirm the slide image, header text, and other elements can be repositioned or resized.

**Acceptance Scenarios**:

1. **Given** a PPTX exported from a report, **When** I select a report image on a slide, **Then** I can move or resize it in the editor.
2. **Given** a PPTX exported from a report, **When** I adjust the slide layout, **Then** the exported content remains as separate editable objects rather than one locked image.

---

### User Story 4 - Keep report visuals readable and correctly laid out (Priority: P2)

As a report user, I can rely on the exported deck to preserve the report layout and visual appearance.

**Why this priority**: The deck must remain a faithful report copy, not just an editable shell.

**Independent Test**: Export a report with charts, tables, and headings, then compare the slide deck to the source report page.

**Acceptance Scenarios**:

1. **Given** a report containing visuals and tables, **When** I export to PPTX, **Then** those elements appear in the deck as images that match the source appearance.
2. **Given** the exported deck, **When** I inspect slide orientation and size, **Then** it uses landscape 16:9 layout.

---

### Edge Cases

- What happens when the report has many sections and the exported deck becomes large?
- What happens when comment text is long or spans multiple lines?
- What happens when a report section contains no comment text?
- How does the system behave if the export cannot be created?
- What happens if the user exports while the report content is still loading?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The report page MUST provide a Download as PPTX action next to the existing Download as PDF action.
- **FR-002**: The exported file MUST be a PowerPoint presentation that opens in standard PowerPoint-compatible software.
- **FR-003**: The exported presentation MUST use landscape orientation with a 16:9 slide layout.
- **FR-004**: Each report section MUST be exported as its own slide or equivalent page-sized slide unit.
- **FR-005**: Visuals and tables MUST be transferred as images that preserve their on-screen appearance.
- **FR-006**: Section headers and key labels MUST be exported as editable text elements rather than flattened images.
- **FR-007**: Comment boxes MUST be exported as editable text elements, and exported slide elements MUST remain individually editable so users can move or resize images and reposition content after download.
- **FR-008**: The export flow MUST not change the current PDF download behavior.
- **FR-009**: If the export cannot be generated, the user MUST receive a clear failure message and the report page MUST remain usable.
- **FR-010**: The exported deck SHOULD preserve the report’s visible order and structure so the PPTX matches the report the user viewed.

### Key Entities *(include if feature involves data)*

- **Report Export**: A generated PPTX file derived from the current report page.
- **Slide**: One page in the exported presentation, corresponding to a report section.
- **Visual Image Block**: A non-editable image version of report visuals, tables, and headings.
- **Header Text Block**: An editable text element for section titles and key labels.
- **Comment Box**: An editable text object that carries report comments into the presentation.
- **Editable Slide Content**: Individual slide elements that users can move or resize after export.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can start a PPTX download from the report page in no more than 2 clicks from the report screen.
- **SC-002**: 100% of report sections appear in the exported PPTX as separate slide content units.
- **SC-003**: 100% of exported comment boxes and section headers remain editable in a PowerPoint-compatible editor.
- **SC-004**: 100% of exported report visuals and tables appear as images with the expected on-screen layout while editable text remains editable.
- **SC-005**: In manual validation, at least 95% of exports for a typical report complete successfully without requiring a retry.
- **SC-006**: For a typical multi-section report, export completes in under 60 seconds in the supported desktop browser.

## Assumptions

- The report page already contains a stable section structure that can be reused for export.
- Users have access to a PowerPoint-compatible editor for opening and modifying the exported file.
- It is acceptable for visuals, tables, and headings to be image-based as long as they preserve the report appearance.
- The first version of the feature focuses on the desktop web experience; mobile-specific export behavior is out of scope unless already supported by the page.
- The existing PDF export button remains available and unchanged.
