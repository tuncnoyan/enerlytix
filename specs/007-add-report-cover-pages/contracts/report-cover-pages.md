# Contract: Report Cover Pages

**Feature**: 007-add-report-cover-pages
**Date**: 2026-07-21
**Status**: Draft

---

## Report Composition Contract

```text
GET /report/?site_id=<id>&end_month=<YYYY-MM>
```

### Purpose

Render report pages with integrated cover-page sequence for the selected site/month context.

### Cover Sequence

1. Front cover page 1
2. Front cover page 2
3. Report body pages
4. Back cover page

### Rules

- Sequence is identical for draft and final report variants.
- Front cover 1 and front cover 2 expose editable fields.
- Back cover is static-image only.

---

## Front Cover 1 Field Contract

### Default Fields

- `site_title`: selected site name.
- `report_month_title`: `[Month Year] Energy Report`.
- `report_date`: fixed `DD MMMM YYYY` format.
- `client_logo_asset`: optional.
- `background_asset`: default image unless replaced per report.

### Upload Validation

Replacement background upload must satisfy all conditions:
- File type: JPG/JPEG/PNG/WebP.
- Maximum size: 10 MB.
- Scope: current report context only.

### Failure Behavior

- If upload type/size is invalid, reject upload with validation message.
- Keep default background image active after rejection.

---

## Front Cover 2 Field Contract

### Editable Blocks

- `scope_title`
- `scope_body`
- `contents_title`
- `contents_body` (generated from entries)

### Default Content Rules

- Scope body uses baseline wording with site name substitution.
- Contents entries list report visual titles in display order.
- Append meter name in parentheses for eligible entries.
- Do not append meter name for `Total Utility Usage (£)`.

---

## Export Contract

### PDF Export

- Export includes full cover sequence (front 1, front 2, body, back).
- Back cover remains static image.

### PPTX Export

- Export includes full cover sequence (front 1, front 2, body, back).
- Front cover editable fields remain editable in PowerPoint-compatible editors.
- Back cover remains static page content.

---

## Non-Goals

- This contract does not require editable field support on the back cover.
- This contract does not alter existing report data aggregation logic.
- This contract does not require a non-Docker runtime/test path.
