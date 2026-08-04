"""End-to-end validation workflow coverage."""

import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from sitesync.models import MonthlyReport, ReportValidationComment, Site, Team, UserTeamAssignment
from sitesync.services import assign_report_validator, create_report_version, get_or_create_monthly_report, mark_report_page_validation_state


User = get_user_model()


class ReportValidationEndToEndTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username='e2e_owner', password='pass123')
        self.supervisor = User.objects.create_user(username='e2e_supervisor', password='pass123')
        self.validator = User.objects.create_user(username='e2e_validator', password='pass123')
        self.contributor = User.objects.create_user(username='e2e_contributor', password='pass123')
        self.team = Team.objects.create(name='E2E Team', level=1, team_lead=self.supervisor)
        self.site = Site.objects.create(external_id='site-e2e-1', name='E2E Site', team=self.team)
        for user in [self.owner, self.supervisor, self.validator, self.contributor]:
            UserTeamAssignment.objects.create(user=user, team=self.team)

        self.report = get_or_create_monthly_report(self.site, '2026-09', actor_user=self.owner)
        create_report_version(
            report=self.report,
            version_kind='draft',
            comments={
                'overview-table': 'Alpha',
                'usage-chart': 'Beta',
            },
            derived_from_version=None,
            actor_user=self.owner,
        )

    def test_end_to_end_validation_flow(self):
        self.client.force_login(self.owner)
        assign_response = self.client.post(
            reverse('sitesync:report_validation_assign', kwargs={'report_id': self.report.id}),
            {'validator_user_id': str(self.validator.id)},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(assign_response.status_code, 200)
        self.client.logout()

        mark_url = reverse('sitesync:report_validation_page_toggle', kwargs={'report_id': self.report.id, 'page_key': 'overview-table'})
        self.client.force_login(self.validator)
        self.assertEqual(self.client.post(mark_url, {'is_validated': 'true'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest').status_code, 200)
        mark_url = reverse('sitesync:report_validation_page_toggle', kwargs={'report_id': self.report.id, 'page_key': 'usage-chart'})
        self.assertEqual(self.client.post(mark_url, {'is_validated': 'true'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest').status_code, 200)
        self.client.logout()

        self.client.force_login(self.owner)
        draft_response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-09',
                'save_mode': 'draft',
                'comments': json.dumps({'overview-table': 'Alpha', 'usage-chart': 'Beta'}),
                'validation_comments': json.dumps({'overview-table': 'Ready for final sign-off.'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(draft_response.status_code, 200)

        final_response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-09',
                'save_mode': 'final',
                'comments': json.dumps({'overview-table': 'Alpha', 'usage-chart': 'Beta'}),
                'validation_comments': json.dumps({'usage-chart': 'Looks good.'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(final_response.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.current_status, MonthlyReport.STATUS_FINAL)
        self.assertEqual(self.report.validation_status, MonthlyReport.VALIDATION_VALIDATED)
        self.assertEqual(ReportValidationComment.objects.filter(report=self.report).count(), 2)
        self.client.logout()

        self.client.force_login(self.supervisor)
        regrant_response = self.client.post(
            reverse('sitesync:report_validation_regrant_write', kwargs={'report_id': self.report.id}),
            {'target_user_id': str(self.contributor.id), 'reason': 'Need a final wording edit'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(regrant_response.status_code, 200)
        self.client.logout()

        self.client.force_login(self.contributor)
        reopen_response = self.client.post(
            reverse('sitesync:report'),
            {
                'site_id': str(self.site.id),
                'end_month': '2026-09',
                'save_mode': 'draft',
                'comments': json.dumps({'overview-table': 'Alpha adjusted', 'usage-chart': 'Beta'}),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(reopen_response.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.validation_status, MonthlyReport.VALIDATION_AWAITING)
        self.assertFalse(self.report.page_validation_states.get(page_key='overview-table').is_validated)
        self.assertTrue(self.report.page_validation_states.get(page_key='usage-chart').is_validated)
