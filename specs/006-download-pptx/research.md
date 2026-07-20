# Research: Download as PPTX

**Feature**: 006-download-pptx
**Date**: 2026-07-20
**Status**: Complete

---

## 1. Export Implementation Strategy

**Decision**: Implement PPTX generation in the browser and reuse the existing report-page capture flow.

**Rationale**:
- The current PDF export is already client-side and uses the report page DOM as the source of truth.
- Keeping the export client-side avoids a new backend endpoint and preserves the existing report page architecture.
- Browser-side PPTX generation is a good fit for a feature that needs to preserve the currently visible report layout.

**Alternatives considered**:
- Server-side PPTX generation with Python tooling: rejected because it adds backend complexity and duplicates the DOM capture logic.
- A separate report-rendering service: rejected because it is unnecessary for a single-page export use case.

---

## 2. PPTX Library Choice

**Decision**: Use a browser-loadable PPTX generation library such as PptxGenJS.

**Rationale**:
- It supports slide creation, image placement, and editable text boxes in a single workflow.
- It fits the current no-build-step approach used by the report page.
- It can represent a 16:9 landscape slide layout and allow independently editable slide elements.

**Alternatives considered**:
- `python-pptx`: rejected because it would require a backend export service and server-side file generation.
- Building PPTX XML manually: rejected because it would be brittle and disproportionately complex.

---

## 3. Slide Composition Model

**Decision**: Build each report section as one PPTX slide, using raster images for visuals/tables and native text boxes for headers, labels, and comment boxes.

**Rationale**:
- The spec prioritizes fidelity for charts, tables, and layout while keeping text editable.
- Reusing `html2canvas` preserves the existing report appearance for image-based content.
- Separating editable text from image content satisfies the hybrid editability requirement without reconstructing every DOM element natively.

**Alternatives considered**:
- Fully rasterized slides: rejected because comment boxes and labels would not remain editable.
- Fully native slide reconstruction: rejected because it would be much more expensive and unnecessary for the first version.

---

## 4. Page Geometry and File Quality

**Decision**: Use a fixed 16:9 landscape slide size and preserve the current image compression approach used for the PDF export.

**Rationale**:
- The feature explicitly requires landscape 16:9.
- A fixed slide geometry keeps placement predictable and consistent with the report page layout.
- Reusing the existing image compression strategy keeps file size and render time manageable for multi-section reports.

**Alternatives considered**:
- A4 or 4:3 output: rejected because it does not match the requested deck format.
- Lossless image output for all slide content: rejected because it would produce unnecessarily large files.

---

## 5. Validation Strategy

**Decision**: Validate with focused browser/manual checks and preserve existing PDF/export regression coverage.

**Rationale**:
- The feature’s success depends on visual correctness in the browser and PowerPoint-compatible editing.
- The repository already relies on Django tests for backend behavior and manual QA for browser-only export details.
- Reusing the current report page means the key risks are rendering and interaction, not database state.

**Alternatives considered**:
- Adding a new automated browser test stack immediately: rejected because it is not required to define or plan the feature.
