# Data Model: Etainabl Site & Supply Sync

## Entities

### Site
Represents a customer property or asset downloaded from the Etainabl platform.

- `id` (PK): internal database identifier
- `external_id`: stable Etainabl asset identifier
- `name`: site name
- `description`: optional description or external metadata
- `created_at`: timestamp when the site record was first persisted
- `updated_at`: timestamp when the site record was last synced or changed

### Supply
Represents a supply/account associated with a site.

- `id` (PK): internal database identifier
- `site_id` (FK): reference to `Site`
- `external_id`: stable Etainabl account identifier
- `name`: supply name
- `utility_type`: utility category such as electricity, gas, water
- `device_id`: device identifier returned by the Etainabl platform
- `created_at`: timestamp when the supply record was first persisted
- `updated_at`: timestamp when the supply record was last synced or changed

## Relationships

- One `Site` can have many `Supply` records.
- Each `Supply` belongs to exactly one `Site`.

## Validation & Sync Rules

- `external_id` is unique for both `Site` and `Supply`.
- `Supply.external_id` must be deduplicated across repeated syncs.
- The sync process must update an existing record when the `external_id` matches, rather than inserting a duplicate.
- The UI must treat `Site.name` as the searchable field for site discovery.
- The supply list must render `Supply.name`, `Supply.utility_type`, and `Supply.device_id`.

## Storage Notes

- For the initial version, the data model is implemented in Django models and persisted in a containerized database.
- Production should use a containerized SQL database with network isolation and secure credential injection.
