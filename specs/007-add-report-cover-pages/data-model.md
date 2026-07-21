# Data Model: Report Cover Pages

**Feature**: 007-add-report-cover-pages
**Date**: 2026-07-21
**Status**: Draft

---

## Scope Note

This feature does not require mandatory new persistent database tables in v1. The model below describes report-level composition objects and validation rules that drive draft/final rendering and PDF/PPTX exports.

---

## Entities

### 1. `ReportCoverSet`

Represents the full cover package attached to one generated report instance.

| Field | Type | Notes |
|-------|------|-------|
| `report_context_id` | identifier | Binds covers to the current report context (site + month + variant) |
| `front_cover_1` | object | First front-cover definition |
| `front_cover_2` | object | Second front-cover definition |
| `back_cover` | object | Back-cover definition |
| `sequence` | ordered list | Fixed order: front_cover_1, front_cover_2, body_pages, back_cover |

**Validation Rules**:
- Sequence order is mandatory and immutable for generated output.
- Draft/final/PDF/PPTX variants must consume the same sequence.

---

### 2. `FrontCoverOneFields`

Editable field set for first front cover.

| Field | Type | Notes |
|-------|------|-------|
| `site_title` | string | Default from selected site name |
| `report_month_title` | string | Default format: `[Month Year] Energy Report` |
| `report_date` | string | Fixed format `DD MMMM YYYY` |
| `client_logo_asset` | nullable asset reference | Optional logo shown in reserved logo area |
| `background_asset` | asset reference | Default image or user-replaced image |

**Validation Rules**:
- `report_date` must be generated in fixed format independent of user locale.
- If `client_logo_asset` is null, report still generates with an empty logo region.

---

### 3. `CoverBackgroundUpload`

Represents a user-provided first-cover background replacement.

| Field | Type | Notes |
|-------|------|-------|
| `filename` | string | Uploaded file name |
| `mime_type` | enum | Allowed: `image/jpeg`, `image/png`, `image/webp` |
| `extension` | enum | Allowed: `.jpg`, `.jpeg`, `.png`, `.webp` |
| `size_bytes` | integer | Maximum 10 MB |
| `report_context_id` | identifier | Upload scoped to currently edited report |

**Validation Rules**:
- Reject files outside allowed type/extension set.
- Reject files larger than 10 MB.
- On rejection, keep default first-cover background active.

---

### 4. `FrontCoverTwoFields`

Editable field set for second front cover.

| Field | Type | Notes |
|-------|------|-------|
| `scope_title` | string | Default title text (`SCOPE`) with user-editable override |
| `scope_body` | string | Baseline scope wording with variable site reference |
| `contents_title` | string | Default title text (`CONTENTS`) with user-editable override |
| `contents_entries` | ordered collection | Visual title list in report display order |

**Validation Rules**:
- `contents_entries` preserve visual display order.
- Meter name suffix format applies to each entry except `Total Utility Usage (£)`.

---

### 5. `VisualContentsEntry`

Line item in second-cover contents section.

| Field | Type | Notes |
|-------|------|-------|
| `visual_title` | string | Visual section title from report |
| `meter_name` | nullable string | Optional meter name |
| `display_line` | string | Rendered line text with conditional meter suffix |
| `position_index` | integer | Stable ordering index |

**Validation Rules**:
- For `visual_title = Total Utility Usage (£)`, `display_line` excludes meter suffix.
- For other entries with a meter name, append ` (meter_name)`.
- For entries without a meter name, render title-only line.

---

### 6. `BackCoverAsset`

Static back-cover page definition.

| Field | Type | Notes |
|-------|------|-------|
| `image_asset` | asset reference | Provided static back-cover image |
| `is_editable` | boolean | Always `false` for field-level edits |

**Validation Rules**:
- Back cover remains static in all output variants.
- No editable text field requirements apply to this page.

---

## Relationships

- One `ReportCoverSet` contains one `FrontCoverOneFields`, one `FrontCoverTwoFields`, and one `BackCoverAsset`.
- One `FrontCoverTwoFields` contains many `VisualContentsEntry` values.
- Zero or one `CoverBackgroundUpload` can override `FrontCoverOneFields.background_asset` for a report context.

---

## State Transitions

### Cover Composition State

1. `defaults_loaded` -> cover defaults populated from report context.
2. `user_edits_applied` -> user text/logo/background edits captured.
3. `validated` -> type/size/date/order constraints pass.
4. `rendered` -> covers assembled into report body for draft/final.
5. `exported_pdf` and/or `exported_pptx` -> variant output generated with shared cover sequence.
