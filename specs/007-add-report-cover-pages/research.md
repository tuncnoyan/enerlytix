# Research: Report Cover Pages

**Feature**: 007-add-report-cover-pages
**Date**: 2026-07-21
**Status**: Complete

---

## 1. Cover Integration Strategy Across Report Variants

**Decision**: Integrate the three cover pages into the shared report composition flow so the same page sequence is used for draft view, final view, PDF export, and PPTX export.

**Rationale**:
- The specification requires strict parity across draft/final/PDF/PPTX variants.
- A single composition source of truth reduces order drift and duplicated logic.
- The required fixed order (front cover 1, front cover 2, body, back cover) is easiest to enforce centrally.

**Alternatives considered**:
- Separate per-format cover logic: rejected because it increases regression risk and parity failures.
- Inject covers only at export time: rejected because draft/final output must also include covers.

---

## 2. Editable Front-Cover Field Representation

**Decision**: Represent front-cover fields as explicit, named report-level values (site title, month title, date, scope title/body, contents title/body, optional logo asset) and map these values into both on-screen rendering and PPTX editable text boxes.

**Rationale**:
- The feature requires editable fields in two places: UI/report composition and editable PPTX output.
- Named fields improve deterministic mapping and simplify tests.
- The second cover requires controlled default text plus user overrides, which aligns with structured field values.

**Alternatives considered**:
- Free-form HTML block editing only: rejected because it complicates PPTX editability mapping and validation.
- Hardcoded static text for scope/contents: rejected because the user explicitly requested editable fields.

---

## 3. First-Cover Background Upload Constraints

**Decision**: Enforce JPG/JPEG/PNG/WebP uploads up to 10 MB for first-cover replacement images, with clear validation failure behavior and fallback to default image.

**Rationale**:
- Constraint was clarified in the specification session.
- Limiting file type/size protects runtime stability and avoids oversized export artifacts.
- Explicit failure handling prevents broken cover output.

**Alternatives considered**:
- No size/type limits: rejected due to reliability and security concerns.
- More restrictive 5 MB/format list: rejected because clarified requirement chose broader acceptance.

---

## 4. Date and Locale Consistency

**Decision**: Render front-cover date in fixed `DD MMMM YYYY` format independently of browser locale.

**Rationale**:
- Specification clarification explicitly requires fixed formatting.
- Avoids environment-dependent output changes across users/containers.
- Keeps PDF/PPTX output stable for regression tests.

**Alternatives considered**:
- Browser locale formatting: rejected because it causes inconsistent outputs.
- Numeric date format (`DD/MM/YYYY`): rejected because clarified format was textual month.

---

## 5. Docker-Only Execution and Testing Path

**Decision**: Use Docker compose as the canonical run/test workflow for this feature, including Django checks/tests and manual export validation runs.

**Rationale**:
- User requirement explicitly mandates Docker runtime and test execution.
- Repository already documents Docker compose usage and service topology.
- Keeps environment parity between development verification and containerized deployment expectations.

**Alternatives considered**:
- Host-Python test execution: rejected because user requested Docker-only test path.
- New container/service split for export: rejected because unnecessary complexity for current scope.
