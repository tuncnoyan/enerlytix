# Quickstart Validation Guide: Download as PPTX

**Feature**: 006-download-pptx
**Date**: 2026-07-20

---

## Prerequisites

1. Django development server running from `django_app/`.
2. Database migrations applied.
3. A report page with at least one site and a populated report month.
4. A PowerPoint-compatible editor installed for opening the downloaded deck.

## Export Assumptions

- PPTX export uses the currently rendered report page as its source of truth.
- The export is browser-based and does not require a backend generation service.
- The downloaded deck is landscape 16:9 and is intended to be edited in a PowerPoint-compatible editor.

---

## Validation Scenarios

### SC-001 - Download a PPTX from the report page

**Steps**:
1. Open a report page.
2. Locate the Download as PDF and Download as PPTX buttons.
3. Click Download as PPTX.

**Expected**:
- A `.pptx` file downloads.
- The file opens successfully in a PowerPoint-compatible editor.

---

### SC-002 - Confirm editable comments and headers

**Steps**:
1. Open the downloaded PPTX in PowerPoint or a compatible editor.
2. Select a comment box.
3. Select a section header or key label.
4. Edit the text.

**Expected**:
- The comment box remains editable.
- The header/key label remains editable.
- The text is not locked into a flat image.

---

### SC-003 - Confirm slide content can be repositioned

**Steps**:
1. Open the exported deck.
2. Select one of the section images or exported slide objects.
3. Move or resize it.

**Expected**:
- The object can be moved or resized in the editor.
- The slide remains in landscape 16:9 format.

---

### SC-004 - Confirm report fidelity

**Steps**:
1. Export a report that contains charts, tables, headings, and comments.
2. Compare the deck to the on-screen report page.

**Expected**:
- Charts and tables appear as images that match the source layout.
- Comments and key labels remain editable.
- The slide order matches the report order.

---

## Commands

From `django_app/`:

```powershell
python manage.py migrate
python manage.py runserver 0.0.0.0:8080
python manage.py test
```

---

## References

- Plan: [plan.md](plan.md)
- Data model: [data-model.md](data-model.md)
- Export contract: [contracts/report-pptx-export.md](contracts/report-pptx-export.md)
