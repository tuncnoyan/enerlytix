# Validation Workflow Test Data Notes

Feature: 012-report-validation-workflow
Created: 2026-08-04

## Persona Coverage Matrix

| Persona | Required for Scenarios | Minimum Fixtures |
|---|---|---|
| Owner | SC-001, SC-002, SC-004, SC-005 | Active user owning the target monthly report |
| Contributor (write-granted) | SC-004, SC-005 | Active user with report write grant |
| Validator | SC-001, SC-003, SC-004, SC-006 | Active non-owner eligible user (same team or supervisory chain) |
| Team Lead | SC-007 | Active user in owner supervisory chain with lead authority |
| Manager | SC-007 | Active user in owner supervisory chain with manager authority |
| Admin | SC-007 | Active user in owner supervisory chain with admin authority |
| Read-only viewer | Visibility checks | Active user with report read access only |
| Ineligible outsider | SC-002 | Active user outside owner team and outside owner supervisory chain |

## Required Data Relationships

- Owner must be linked to a site with a valid team assignment.
- Validator candidate must be active and must not equal the owner.
- At least one ineligible candidate must exist for negative assignment checks.
- Report should include at least two canonical page keys (for all-pages-validated transitions).
- Existing draft version should contain business comments to test reset behavior.

## Suggested Fixture Values

- reporting_month: 2026-11
- canonical page keys: overview-table, usage-chart
- sample business comments:
  - overview-table: Alpha
  - usage-chart: Beta
- sample validation comment text:
  - overview-table: "Please confirm baseline assumptions."

## Docker Verification Mapping

Use these tests to validate fixture sufficiency:

- sitesync.tests.test_report_validation_assignment
- sitesync.tests.test_report_validation_comments
- sitesync.tests.test_report_validation_page_status
- sitesync.tests.test_report_validation_final_gate
- sitesync.tests.test_report_validation_regrant_reopen
- sitesync.tests.test_saved_reports_validation_metadata
