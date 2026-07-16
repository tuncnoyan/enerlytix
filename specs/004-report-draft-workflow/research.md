# Research: Monthly Report Draft and Final Workflow

**Feature**: 004-report-draft-workflow
**Date**: 2026-07-16
**Status**: Complete

---

## 1. Report Persistence Strategy

**Decision**: Model each monthly report as a single persisted identity per site and reporting month, with separate version rows for draft, original final, and replacement final saves.

**Rationale**:
- The spec requires one report per site per month, so the monthly identity must be unique.
- Final reports must remain editable after a warning, but the original final must stay immutable, so direct in-place overwrite is not sufficient.
- A separate version table preserves the original final while still allowing the latest final to become the client-facing copy.
- This approach fits Django's relational model and makes unique constraints and audit history straightforward.

**Alternatives considered**:
- Overwrite the final report in place: rejected because it breaks the immutable original-final requirement.
- Create a separate report record for each save: rejected because it weakens the one-report-per-month rule and complicates browsing.

---

## 2. Saved Reports Page Delivery

**Decision**: Implement the saved reports browser as a server-rendered Django page, using the existing app's template and view pattern.

**Rationale**:
- The current application already uses server-rendered pages for dashboard and report flows.
- A browser page listing drafts and finals does not need a client-side application framework.
- Server rendering keeps the change small and consistent with the current codebase.

**Alternatives considered**:
- SPA-style report management screen: rejected because it would add frontend complexity without a clear product gain.
- Admin-only browsing: rejected because the feature is user-facing and must be accessible from the product UI.

---

## 3. Final Edit Warning Flow

**Decision**: When a user opens a final report for editing, show a warning and then create a replacement final version after confirmation rather than modifying the original final row.

**Rationale**:
- This preserves the historical final document that was already generated and shared.
- It keeps the current report identity stable while still allowing corrections.
- It gives the saved reports page a simple status model: draft or final, with the latest final exposed as current.

**Alternatives considered**:
- Silent edit of the final report: rejected because it hides the historical version.
- Separate branch record outside the monthly report identity: rejected because it would make monthly browsing ambiguous.

---

## 4. Carry-Forward Comment Behaviour

**Decision**: Seed a new month's draft from the previous month's final report comments for the same site, and mark each copied comment as a reference comment with visible provenance.

**Rationale**:
- The spec explicitly requires previous final comments to appear in the next month.
- Copying from the previous month's final report, not from drafts, prevents unfinished notes from leaking forward.
- Storing provenance metadata with each copied comment allows the UI to show a clear warning in the comment box.

**Alternatives considered**:
- Carry comments from the latest report of any status: rejected because only final reports are authoritative.
- Store a single shared comment template across months: rejected because comments must remain month-specific and editable.

---

## 5. Month Key and Uniqueness Model

**Decision**: Use `YYYY-MM` as the canonical reporting month key throughout the workflow and enforce uniqueness at the database level for `(site, reporting_month)`.

**Rationale**:
- The existing codebase already uses canonical month keys for utility data.
- A string month key is simple to compare, display, and pass through forms and URLs.
- Database-level uniqueness is the safest way to prevent duplicate reports under concurrent edits.

**Alternatives considered**:
- Store a date range only: rejected because the workflow is month-based and must be easy to browse.
- Rely only on application-level checks: rejected because concurrent requests could still create duplicates.

---

## 6. Validation Strategy

**Decision**: Cover the workflow with Django request/model tests in `django_app/sitesync/tests/`, using existing `python manage.py test` execution.

**Rationale**:
- The feature spans models, views, and page rendering, so request-level tests best verify the workflow end to end.
- Django's built-in test runner already matches the repository's current setup.
- No additional test framework is needed to validate the browser page and save flows.

**Alternatives considered**:
- Add a new browser automation stack: rejected because the current repo does not require it for this sprint.