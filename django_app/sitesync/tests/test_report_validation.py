"""Feature-focused regression tests for report validator UI fixes (spec 018)."""

import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from sitesync.models import MonthlyReport, ReportValidationComment, Site, Team, UserTeamAssignment
from sitesync.services import (
    assign_report_validator,
    create_report_version,
    get_or_create_monthly_report,
    get_report_validation_page_keys,
    mark_report_page_validation_state,
)


User = get_user_model()


class ReportValidatorUiFixesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='rvf_owner', password='pass123')
        self.validator = User.objects.create_user(username='rvf_validator', password='pass123')
        self.dual_role_validator = User.objects.create_user(
            username='rvf_dual_validator',
            password='pass123',
            is_staff=True,
            is_superuser=True,
        )

        self.team = Team.objects.create(name='Validator UI Team', level=1)
        self.site = Site.objects.create(external_id='site-rvf-1', name='Validator UI Site', team=self.team)
        for user in [self.owner, self.validator, self.dual_role_validator]:
            UserTeamAssignment.objects.create(user=user, team=self.team)

        self.report = get_or_create_monthly_report(self.site, '2026-08', actor_user=self.owner)
        create_report_version(
            report=self.report,
            version_kind='draft',
            comments={
                'overview-table': 'Overview table note',
                'overview-chart': 'Overview chart note',
                'usage-chart': 'Usage note',
            },
            derived_from_version=None,
            actor_user=self.owner,
        )

    def test_report_context_exposes_validator_restricted_flags(self):
        assign_report_validator(report=self.report, validator_user=self.validator, assigned_by_user=self.owner)

        self.client.force_login(self.validator)
        response = self.client.get(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-08',
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.content.decode('utf-8')
        self.assertIn('"validatorRestrictedSession": true', body)
        self.assertIn('"canSaveReportContent": false', body)
        self.assertIn('"canEditValidationNotes": true', body)
        self.assertIn('"canTogglePageValidation": true', body)
        self.assertIn('"validationCommentsDebounceMs": 300', body)

    def test_dual_role_assigned_validator_is_still_validator_restricted(self):
        assign_report_validator(
            report=self.report,
            validator_user=self.dual_role_validator,
            assigned_by_user=self.owner,
        )

        self.client.force_login(self.dual_role_validator)
        response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-08',
                'save_mode': 'draft',
                'comments': json.dumps({'overview-table': 'Attempted edit'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json().get('code'), 'validator_restricted_session')

    def test_validation_note_upsert_persists_for_assigned_validator(self):
        assign_report_validator(report=self.report, validator_user=self.validator, assigned_by_user=self.owner)

        self.client.force_login(self.validator)
        response = self.client.post(
            reverse('sitesync:report_validation_comment_upsert', kwargs={'report_id': self.report.id}),
            {
                'page_key': 'overview-chart',
                'comment_text': 'Autosaved validator note',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('success'), True)
        self.assertEqual(
            ReportValidationComment.objects.get(
                report=self.report,
                page_key='overview-chart',
                authored_by_user=self.validator,
            ).comment_text,
            'Autosaved validator note',
        )

    def test_validation_note_upsert_failure_does_not_overwrite_existing_note(self):
        assign_report_validator(report=self.report, validator_user=self.validator, assigned_by_user=self.owner)
        ReportValidationComment.objects.create(
            report=self.report,
            page_key='overview-chart',
            authored_by_user=self.validator,
            comment_text='Existing note should remain',
        )

        self.client.force_login(self.validator)
        response = self.client.post(
            reverse('sitesync:report_validation_comment_upsert', kwargs={'report_id': self.report.id}),
            {
                'page_key': 'unknown-page-key',
                'comment_text': 'Should not be persisted',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Unknown report page key', response.json().get('detail', ''))
        existing = ReportValidationComment.objects.get(
            report=self.report,
            page_key='overview-chart',
            authored_by_user=self.validator,
        )
        self.assertEqual(existing.comment_text, 'Existing note should remain')

    def test_overview_validation_keys_are_deduplicated(self):
        page_keys = get_report_validation_page_keys(self.report)
        overview_like = {
            key for key in page_keys
            if ''.join(ch for ch in str(key).lower() if ch.isalnum()) in {'overview', 'overviewtable', 'overviewchart'}
        }

        self.assertEqual(len(overview_like), 1)

    def test_report_save_ignores_stale_validation_comment_keys(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-08',
                'save_mode': 'draft',
                'comments': json.dumps({'overview-table': 'Owner edit on overview'}),
                'validation_comments': json.dumps({'stale-page-key': 'Stale key must not break draft save'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.current_status, MonthlyReport.STATUS_DRAFT)

    def test_validator_toggle_accepts_existing_state_key_after_comment_key_drift(self):
        assign_report_validator(report=self.report, validator_user=self.validator, assigned_by_user=self.owner)
        mark_report_page_validation_state(
            report=self.report,
            page_key='usage-chart',
            is_validated=True,
            actor_user=self.validator,
        )

        self.client.force_login(self.owner)
        save_response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-08',
                'save_mode': 'draft',
                # Simulate a sparse post payload where not all legacy keys are carried forward.
                'comments': json.dumps({'overview-table': 'Owner changed only one page'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(save_response.status_code, 200)

        self.client.force_login(self.validator)
        toggle_response = self.client.post(
            reverse(
                'sitesync:report_validation_page_toggle',
                kwargs={'report_id': self.report.id, 'page_key': 'usage-chart'},
            ),
            {'is_validated': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(toggle_response.status_code, 200)
        payload = toggle_response.json()
        self.assertTrue(payload.get('success'))
