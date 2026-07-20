# Contract: Report PPTX Export

**Feature**: 006-download-pptx
**Date**: 2026-07-20
**Status**: Draft

---

## Report Page Action

```text
GET /report/?site_id=<id>&end_month=<YYYY-MM>
```

### Purpose

Open the monthly report page and provide an export action that produces a PowerPoint file for the currently viewed report.

### Behaviour

- The report page must show a Download as PPTX button beside Download as PDF.
- The PPTX export must use the currently visible report content.
- The export must not change the existing PDF export behavior.

---

## Export Output

### Deck Shape

- Landscape orientation.
- 16:9 slide size.
- One slide per visible report section.

### Content Rules

- Charts, tables, and other report visuals are exported as images.
- Section headers and key labels are exported as editable text.
- Comment boxes are exported as editable text.
- Exported images and text objects remain individually movable and resizable in the presentation editor.

---

## Error Behaviour

- If the export cannot be generated, the user should receive a clear failure message.
- The report page must remain usable after a failed export attempt.

---

## Non-Goals

- The contract does not require server-side PPTX generation.
- The contract does not require all report visuals to become native editable shapes.
- The contract does not change the existing PDF export route or behavior.
