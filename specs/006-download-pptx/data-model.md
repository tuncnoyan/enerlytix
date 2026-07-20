# Data Model: Download as PPTX

**Feature**: 006-download-pptx
**Date**: 2026-07-20
**Status**: Draft

---

## Scope Note

This feature does not add persistent database entities. The data model below describes the transient export structures that are assembled from the existing report page DOM and report data.

---

## Export Entities

### 1. `ReportExportRequest`

Represents one user-triggered export action from the report page.

| Field | Type | Notes |
|-------|------|-------|
| `site_id` | identifier | Source site for the report |
| `end_month` | YYYY-MM string | Report month being exported |
| `report_sections` | ordered collection | Visible report sections included in the deck |
| `export_format` | string | Expected value: `pptx` |
| `slide_size` | string | Fixed value: `16:9` |
| `orientation` | string | Fixed value: `landscape` |

**Behaviour**:
- One export request corresponds to one downloaded PPTX file.
- The request uses the currently rendered report page as the source of truth.

---

### 2. `ReportSectionSlide`

Represents one exported slide for one visible report section.

| Field | Type | Notes |
|-------|------|-------|
| `section_id` | string | The source report section identifier |
| `slide_index` | integer | Order in the exported deck |
| `visual_blocks` | collection | Charts, tables, and other non-editable section visuals |
| `header_text_blocks` | collection | Editable section labels and headings |
| `comment_boxes` | collection | Editable comment boxes carried into the deck |
| `layout_bounds` | geometry | Positioning within the slide canvas |

**Behaviour**:
- Each visible report section becomes one slide.
- The slide preserves visible order from top to bottom in the report page.

---

### 3. `VisualImageBlock`

Represents a rasterized visual element in the exported deck.

| Field | Type | Notes |
|-------|------|-------|
| `image_data` | binary/image data | Captured from the rendered report section |
| `source_element` | DOM section reference | Source chart/table/header area |
| `quality_hint` | string | Export fidelity and compression settings |

**Behaviour**:
- Used for charts, tables, and other visual report content.
- Not intended to be edited independently as text, but can be resized or moved as a slide object.

---

### 4. `HeaderTextBlock`

Represents editable text that must remain selectable in PowerPoint.

| Field | Type | Notes |
|-------|------|-------|
| `text` | string | Section title or key label |
| `position` | geometry | Slide placement |
| `font_style` | styling metadata | Matches the report page as closely as practical |

**Behaviour**:
- Used for headers and key labels that must remain editable after export.

---

### 5. `CommentBox`

Represents editable commentary copied into the export.

| Field | Type | Notes |
|-------|------|-------|
| `text` | string | Current comment text |
| `position` | geometry | Slide placement within the section |
| `is_editable` | boolean | Must remain true in the exported deck |

**Behaviour**:
- Comment text remains editable after download.
- The comment box can be moved or resized in the presentation editor.

---

## Relationships

- One `ReportExportRequest` produces many `ReportSectionSlide` entries.
- One `ReportSectionSlide` contains one or more `VisualImageBlock` objects and zero or more `HeaderTextBlock` / `CommentBox` objects.
- The exported PPTX file is the final artifact produced from the assembled request + slide content.
