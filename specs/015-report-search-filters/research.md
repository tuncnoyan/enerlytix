# Research: Saved Reports Search and Filters

Feature: 015-report-search-filters  
Date: 2026-08-06  
Status: Complete

## Decision 1: Implement filtering server-side on the saved reports endpoint

- Decision: Extend `saved_reports_view` to apply Site/User/month/status filters in the Django queryset/payload generation flow, and pass active filter state back to the template/JSON response.
- Rationale: The saved reports page already centralizes report listing logic in one route (`GET /reports/`) and returns both HTML + JSON style payloads. Server-side filtering keeps authorization and team scoping intact and avoids exposing extra rows to client-side scripts before filtering.
- Alternatives considered:
  - Client-side filtering only on preloaded `reports_json`: rejected because all candidate rows must still be shipped to browser and could weaken privacy expectations for large/role-scoped datasets.
  - New dedicated API endpoint for filters: rejected for this scope because existing `saved_reports_view` already owns listing behavior and can be evolved without interface sprawl.

## Decision 2: Use month-year range semantics aligned with normalized reporting month keys

- Decision: Treat reporting month filters as month-year selectors and apply inclusive bounds (`start_month <= reporting_month <= end_month`) when both bounds are provided.
- Rationale: Product clarification explicitly selected month-year precision and inclusive range boundaries. Existing report model values are month keys (for example `2026-07`) and already map naturally to this comparison pattern.
- Alternatives considered:
  - Day-level date range controls: rejected because it introduces ambiguity for month-based rows and was explicitly clarified out of scope.
  - Exclusive end boundary: rejected because user clarification selected inclusive boundaries.

## Decision 3: Keep status filters checkbox-based with permissive empty selections

- Decision: Represent report status (`draft`, `final`) and validation status (`draft`, `awaiting_validation`, `validated`) as checkbox groups that default to all selected and allow all options to be unticked.
- Rationale: Feature clarification requires both default-all behavior and explicit zero-result behavior when users untick all options. This is deterministic and easy to test.
- Alternatives considered:
  - Enforce at least one selected checkbox: rejected because it conflicts with accepted clarification.
  - Auto-reset to all when fully unticked: rejected because it hides user intent and conflicts with accepted clarification.

## Decision 4: Match Site/User search with case-insensitive contains rules

- Decision: Implement case-insensitive partial matching for Site and User filters; User search spans `owner_name`, `last_edited_by_name`, and `validator_name`.
- Rationale: Clarified behavior is case-insensitive contains. The saved reports payload already includes those user-attribution fields, so matching can be applied consistently in server-side query building and response shaping.
- Alternatives considered:
  - Prefix-only matching: rejected because it is less discoverable for partial names.
  - Exact-only matching: rejected because it is too strict for operational workflows.

## Decision 5: Execute development and validation in Docker containers only

- Decision: Use `django_app/docker/docker-compose.yml` as the mandatory runtime and test environment for this feature, including migrations and all automated checks.
- Rationale: Project constitution requires containerized maintainability and the user explicitly requested Docker-only development/testing. Existing project docs and scripts already standardize on Docker Compose for `web` and `db` services.
- Alternatives considered:
  - Local host Python/SQLite runs: rejected for this feature because environment parity is required.
  - Hybrid host/container workflow: rejected because it introduces drift and violates the explicit request.
