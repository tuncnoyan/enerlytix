# Feature Specification: Etainabl Site & Supply Sync

**Feature Branch**: `001-etainabl-site-supply-sync`

**Created**: 2026-06-23

**Status**: Draft

**Input**: User description: "I am step by step building a modern web app to analyse electricity, gas and water usage data. In its initial version, the data should be downloaded from a data platform by using its API feature. I attached two sample working code samples, and an Excel file for the required API key and other details. These sample files can also be found in the \"sample_app\" subfolder. The new web app should use the same logic. It should first download all sites and supplies from the data platform (https://api.etainabl.com/2.0) and create or update the related tables in the database. Then, it can download the data for the site and supply in a format all selected by the user. The application should be containerised. The initial version should download site (asset) and supply (account) lists from the Etainabl platform, create and update sites and supplies tables in the database, then displays them on a web page. On the web page, promarily, sites names should be displayed. That list should be searchable. When user selects a site, the related supply list should be displayed just beside the site list. Supply list should include the name, utility type and device ID fields."

## Clarifications

- Q: Should the app sync site and supply data automatically on startup, manually only, or both? → A: Do an automatic initial sync, then allow a manual refresh button.
- Q: Should the settings page allow editing and saving configuration values, or only display them? → A: Editable settings page where users can change and save settings.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Load and Persist Etainabl Site/Supply Data (Priority: P1)

Users need the application to fetch the current site and supply catalog from the Etainabl platform and persist it for display.

**Why this priority**: The core value of the initial release is ensuring the web app has the latest site and supply data available locally for use.

**Independent Test**: Verify the app can successfully fetch the full site and supply catalog from Etainabl and store or update the corresponding database tables.

**Acceptance Scenarios**:

1. **Given** valid Etainabl API credentials and connectivity, **When** the application performs initial sync, **Then** it creates or updates a persistent site table and a supply table with the latest records.
2. **Given** a site or supply already exists in the database, **When** the same record is returned by the Etainabl API, **Then** the existing database row is updated rather than duplicated.

---

### User Story 2 - Searchable Site List Display (Priority: P2)

Users need to see a searchable list of site names and be able to choose a site to reveal its related supplies.

**Why this priority**: The primary user experience depends on easy discovery of sites and a direct view of associated supplies.

**Independent Test**: On the web page, verify the site list is displayed first, supports text search, and selecting a site updates the supply list beside it.

**Acceptance Scenarios**:

1. **Given** a populated site list, **When** the user enters text into the search field, **Then** the list of visible sites narrows to matches.
2. **Given** a user selects a site from the list, **When** the selection is made, **Then** the related supplies for that site appear adjacent to the site list.

---

### User Story 3 - Supply Detail Presentation (Priority: P3)

Users need the supply list to show the key supply details required for review and selection.

**Why this priority**: Users must understand the supply context before they can use the platform for report creation or further data selection.

**Independent Test**: Confirm that each supply row includes supply name, utility type, and device ID when a site is selected.

**Acceptance Scenarios**:

1. **Given** a selected site with associated supplies, **When** the supply list renders, **Then** each supply displays its name, utility type, and device ID.

---

### User Story 4 - Settings Panel for Runtime Configuration (Priority: P2)

Users need a single settings page that displays application parameters and runtime configuration values in one place.

**Why this priority**: Centralized visibility of integration settings and operational parameters reduces configuration errors and makes troubleshooting easier.

**Independent Test**: Verify the settings page loads and shows the configured Etainabl base URL, download page size, timeout values, and other runtime parameters.

**Acceptance Scenarios**:

1. **Given** a valid application configuration, **When** the user navigates to the settings page, **Then** the page displays Etainabl base URL, download page size, timeout values, and relevant API configuration settings.
2. **Given** the application is running in development or test, **When** configuration values are loaded, **Then** secret keys and similar sensitive parameters are sourced from the `.env` file and never displayed in plaintext on the settings panel (user edits override `.env` values only in the database, not in the file).
3. **Given** the application is deployed to production on a platform that supports secure secret management, **When** runtime configuration is resolved, **Then** the platform-native secret store is preferred over `.env` while still allowing `.env` as a documented fallback if no better method exists.

---

### Edge Cases

- If the Etainabl API returns no sites, the application shows an empty site state with a clear message and does not crash.
- If a selected site has no related supplies, the supply section displays a message that no supplies are available for that site.
- If API pagination returns partial pages or repeated records, the sync process deduplicates and persists only the latest unique site and supply records.
- If the API key or connection fails, the UI surfaces a recoverable error message and preserves the last known database state.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The application MUST fetch all site (asset) and supply (account) records from the Etainabl API at `https://api.etainabl.com/2.0`.
- **FR-002**: The application MUST create or update a persistent `sites` table and a `supplies` table in the database.
- **FR-003**: The application MUST use a unique stable key for each site and supply to avoid duplicate rows during repeated syncs.
- **FR-004**: The site list MUST be displayed on the web page as the primary content element and support text search by site name.
- **FR-005**: Selecting a site MUST display the related supplies immediately beside the site list.
- **FR-006**: The supply list MUST include the supply name, utility type, and device ID fields.
- **FR-007**: The application MUST be containerised so it can be packaged and deployed in a container-native environment.
- **FR-008**: The application MUST handle API connectivity failures with retries and clear error feedback.
- **FR-009**: The data sync flow MUST support reconciliation so updated Etainabl data overwrites stale values without losing existing valid records.
- **FR-010**: The application MUST securely handle Etainabl API credentials and database connection strings using environment variables or secure secret management; credentials MUST NOT be stored in version control or hardcoded configuration files. **Exception**: `.env` files are acceptable in development and test environments as a local configuration method, provided they are never committed to version control (enforced by .gitignore).
- **FR-011**: In development and test environments, API keys and similar secret keys MUST be stored in a `.env` file and loaded from environment configuration.
- **FR-012**: In production, the application MUST prefer a platform-provided secure secret store when available (e.g., Kubernetes Secrets, Azure Key Vault, Docker Secrets), while still allowing `.env` as a documented fallback if the target platform does not provide a better method.
- **FR-013**: The application MUST include a settings page that displays key runtime parameters such as the Etainabl base URL, download page size, timeout values, and other configuration settings on a single panel.

### Key Entities *(include if feature involves data)*

- **Site (Asset)**: Represents a customer property or location, including the site name and the Etainabl site identifier.
- **Supply (Account)**: Represents a meter or service line associated with a site, including supply name, utility type, and device ID.
- **API Configuration**: Represents the Etainabl API key and request parameters required to authenticate and fetch site/supply data.
- **Application Settings**: Represents runtime parameters such as the Etainabl base URL, download page sizes, timeout values, and other operational configuration values.

## Success Criteria *(mandatory)*
### Measurable Outcomes

- **SC-001**: A user can load the searchable site list in under 3 seconds for a catalog of up to 100 sites.
- **SC-002**: At least 95% of valid Etainabl site and supply records are successfully persisted on the first sync attempt in a normal network environment. **Validation**: Integration test syncs a batch of known test records (minimum 100) and measures the percentage that successfully persist to the database.
- **SC-003**: Users can find a site using search text and select it to show related supplies in the same view.
- **SC-004**: When a site is selected, its related supplies render with name, utility type, and device ID visible on at least 90% of supported data rows.
- **SC-005**: The application can be built and run as a container image in the initial version.
- **SC-006**: The settings page displays the key configuration values within 2 seconds and makes the current runtime parameters visible in one place. **Note**: Sensitive values (API keys, passwords) are masked or hidden on display but may be edited. **Validation**: Performance test measures settings page load time on a standard development machine.

## Assumptions

- The initial release is intended as a web application with a local or remote database, not as a mobile app.
- The Etainabl API supports paginated retrieval of assets and accounts and returns stable identifiers for sync.
- The first version is focused on data synchronization and display; report generation and advanced filtering are out of scope.
- The sample Python code and Excel-based configuration in `sample_app` provide the required API access patterns and field mappings.
- The containerisation requirement means the application can be packaged and executed in a container environment, not necessarily orchestrated by Kubernetes in v1.
- **Retry Strategy**: API sync failures are retried up to 10 times with exponential backoff (initial 1s, max 120s interval). Transient errors (5xx, timeouts) trigger retries; permanent errors (4xx, auth failures) fail immediately.
- **Platform-Native Secret Stores**: Supported in production: Kubernetes Secrets, Azure Key Vault, Docker Secrets (Swarm mode). Other platforms default to `.env` with documented fallback policy per FR-012.
- **Security & Encryption**: All data in transit uses TLS/HTTPS; database connections require SSL; sensitive values in logs are redacted; credentials are never logged or exposed in error messages. Database encryption at rest is optional in v1 but supported via PostgreSQL pgcrypto extension.
