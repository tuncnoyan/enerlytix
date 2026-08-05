# Research Notes: Homepage Refresh

## 1. Public home page simplification

- Decision: Keep `site_list_view` as the public landing page and remove the import/report controls from the public template path.
- Rationale: The home page already owns site search, site selection, and supply loading. Reusing that entry point avoids introducing another public landing route and keeps the most common user flow simple.
- Alternatives considered: A role-based single page with collapsed sections was rejected because it would still leave admin actions in the public surface and preserve visual clutter.

## 2. Admin-only import review page

- Decision: Add a new admin-panel page under the existing `panel/` namespace for usage and invoice import review, and keep the old `consumption-display` URL as a compatibility redirect or shim.
- Rationale: The repository already separates admin pages with `admin_panel_required`, `panel_base.html`, and dedicated admin routes. A new panel route fits the existing architecture and makes the move away from the public page explicit.
- Alternatives considered: Reusing the public `consumption_display_view` without a panel route was rejected because it would keep an admin workflow attached to a public URL and make navigation inconsistent.

## 3. Supply filtering and inactive-meter handling

- Decision: Extend the supply-list request flow to support a supply search term and an `include_inactive` toggle, with inactive supplies filtered out by default.
- Rationale: The supply panel is already rendered through a dedicated endpoint and client-side reload cycle, so the cleanest implementation is to treat the new controls as first-class filter inputs rather than doing ad hoc DOM filtering only.
- Alternatives considered: Client-only filtering was rejected because the supply response already depends on server-side site and meter type filters, and the inactive state should be enforced consistently in the rendered HTML fragment.

## 4. Export scope

- Decision: Export the current filtered view only for the admin import review page, in both CSV and XLSX formats.
- Rationale: This matches the user's review workflow and aligns with the existing admin audit-log export pattern, where exports reflect the filters currently applied on the page.
- Alternatives considered: Full dataset export was rejected because it would not match what the admin is actively reviewing and would add a second, less predictable export mode.

## 5. Shared dashboard logic

- Decision: Keep the existing site-selection JavaScript as the base interaction layer, but make the import/report controls mode-aware so the public home page and admin import page can share site selection while exposing different actions.
- Rationale: `site_selection.js` already owns site selection, supply loading, import triggering, and report triggering. Reusing it avoids duplicating the most complex interaction logic and reduces the chance of diverging behavior between the home and admin versions of the dashboard.
- Alternatives considered: Duplicating the page logic in a second script for the admin page was rejected because it would fragment the source of truth for supply loading and selection state.