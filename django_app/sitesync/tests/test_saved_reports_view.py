"""Tests for the saved reports browser view."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from uuid import uuid4

from sitesync.models import AuditLogEntry, MonthlyReport, ReportWriteGrant, RoleAssignment, Site, Team, UserTeamAssignment
from sitesync.services import AUDIT_ACTION_REPORT_BULK_DELETE, AUDIT_ACTION_REPORT_BULK_DELETE_DENIED
from sitesync.services import create_report_version, get_or_create_monthly_report


class SavedReportsViewTest(TestCase):
    """Validate saved reports list and open links."""

    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='savedreportsadmin',
            password='pass123',
            is_staff=True,
            is_superuser=True,
        )
        self.validator = get_user_model().objects.create_user(
            username='savedreportsvalidator',
            password='pass123',
        )
        self.client.force_login(self.user)
        self.site = Site.objects.create(
            external_id='site-ext-saved-1',
            name='Saved Reports Site',
            description='Saved reports demo site',
        )

    def _create_report(self, month, kind='draft'):
        report = get_or_create_monthly_report(self.site, month)
        create_report_version(
            report=report,
            version_kind=kind,
            comments={'overview': f'{month} note'},
            derived_from_version=None,
        )
        return report

    def test_saved_reports_page_renders_rows(self):
        self._create_report('2026-05', kind='final')
        self._create_report('2026-06', kind='draft')

        response = self.client.get('/reports/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Saved Reports')
        self.assertContains(response, '2026-05')
        self.assertContains(response, '2026-06')
        self.assertContains(response, 'final')
        self.assertContains(response, 'draft')

    def test_saved_reports_json_includes_open_url(self):
        report = self._create_report('2026-05', kind='final')
        report.current_version.selected_supply_ids = ['supply-a', 'supply-b']
        report.current_version.save(update_fields=['selected_supply_ids'])

        response = self.client.get('/reports/?format=json')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('reports', payload)
        self.assertEqual(len(payload['reports']), 1)
        row = payload['reports'][0]
        self.assertEqual(row['reporting_month'], '2026-05')
        self.assertIn('site_id=', row['open_url'])
        self.assertIn('end_month=2026-05', row['open_url'])
        self.assertIn('supply_ids=supply-a,supply-b', row['open_url'])

    def test_saved_reports_json_returns_default_selected_filters(self):
        self._create_report('2026-05', kind='final')

        response = self.client.get('/reports/?format=json')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('selected_filters', payload)
        selected = payload['selected_filters']
        self.assertEqual(selected['report_statuses'], ['draft', 'final'])
        self.assertEqual(selected['validation_statuses'], ['draft', 'awaiting_validation', 'validated'])

    def test_saved_reports_json_invalid_month_range_returns_contract_error(self):
        self._create_report('2026-05', kind='final')

        response = self.client.get('/reports/?format=json&start_month=2026-07&end_month=2026-06')

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload['code'], 'invalid_month_range')
        self.assertIn('detail', payload)
        self.assertIn('selected_filters', payload)

    def test_saved_reports_page_renders_default_status_checkboxes_checked(self):
        self._create_report('2026-05', kind='final')

        response = self.client.get('/reports/')

        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        self.assertIn('name="report_status" value="draft" checked', html)
        self.assertIn('name="report_status" value="final" checked', html)
        self.assertIn('name="validation_status" value="draft" checked', html)
        self.assertIn('name="validation_status" value="awaiting_validation" checked', html)
        self.assertIn('name="validation_status" value="validated" checked', html)

    def test_saved_reports_admin_only_controls_visibility(self):
        self._create_report('2026-05', kind='final')

        response = self.client.get('/reports/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'saved-reports-bulk-delete-form')
        self.assertContains(response, 'saved-reports-select-all')

        non_admin = get_user_model().objects.create_user(
            username='savedreportsmember',
            password='pass123',
        )
        self.client.force_login(non_admin)
        member_response = self.client.get('/reports/')
        self.client.force_login(self.user)

        self.assertEqual(member_response.status_code, 200)
        self.assertNotContains(member_response, 'saved-reports-bulk-delete-form')
        self.assertNotContains(member_response, 'saved-reports-select-all')

    def test_saved_reports_role_assigned_admin_sees_admin_controls(self):
        self._create_report('2026-05', kind='final')
        team = Team.objects.create(name='Saved Reports Role Admin Team', level=1)
        self.site.team = team
        self.site.save(update_fields=['team'])

        role_admin = get_user_model().objects.create_user(
            username='savedreportsroleadmin',
            password='pass123',
            is_staff=False,
            is_superuser=False,
        )
        RoleAssignment.objects.create(user=role_admin, role_name=RoleAssignment.ROLE_ADMIN)
        UserTeamAssignment.objects.create(user=role_admin, team=team)

        self.client.force_login(role_admin)
        response = self.client.get('/reports/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'saved-reports-bulk-delete-form')
        self.assertContains(response, 'saved-reports-select-all')
        self.assertContains(response, 'isAdmin: true')

    def test_saved_reports_sort_unknown_field_falls_back_to_reporting_month(self):
        self._create_report('2026-04', kind='final')
        self._create_report('2026-06', kind='final')

        response = self.client.get('/reports/?format=json&sort_field=not-a-field')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['sort']['field'], 'reporting_month')
        self.assertTrue(payload['sort']['applied_fallback'])
        self.assertEqual([row['reporting_month'] for row in payload['reports']], ['2026-06', '2026-04'])

    def test_saved_reports_bulk_delete_success_with_correct_password(self):
        report_one = self._create_report('2026-05', kind='final')
        report_two = self._create_report('2026-06', kind='draft')

        response = self.client.post(
            reverse('sitesync:saved_reports_bulk_delete') + '?format=json',
            {
                'selected_report_ids': [str(report_one.id), str(report_two.id)],
                'password_confirmation': 'pass123',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['deleted_count'], 2)
        self.assertFalse(MonthlyReport.objects.filter(id=report_one.id).exists())
        self.assertFalse(MonthlyReport.objects.filter(id=report_two.id).exists())
        entry = AuditLogEntry.objects.filter(
            action_type=AUDIT_ACTION_REPORT_BULK_DELETE,
            action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
        ).latest('occurred_at_utc')
        self.assertIn('Deleted 2 reports from saved reports page:', entry.message)
        self.assertIn('Saved Reports Site 2026-05', entry.message)
        self.assertIn('Saved Reports Site 2026-06', entry.message)

    def test_saved_reports_bulk_delete_denied_with_invalid_password(self):
        report = self._create_report('2026-05', kind='final')

        response = self.client.post(
            reverse('sitesync:saved_reports_bulk_delete') + '?format=json',
            {
                'selected_report_ids': [str(report.id)],
                'password_confirmation': 'wrong-password',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['code'], 'invalid_password')
        self.assertTrue(MonthlyReport.objects.filter(id=report.id).exists())
        entry = AuditLogEntry.objects.filter(
            action_type=AUDIT_ACTION_REPORT_BULK_DELETE_DENIED,
            action_outcome=AuditLogEntry.OUTCOME_DENIED,
        ).latest('occurred_at_utc')
        self.assertIn('invalid password confirmation', entry.message)
        self.assertIn('Saved Reports Site 2026-05', entry.message)

    def test_saved_reports_bulk_delete_requires_selection(self):
        self._create_report('2026-05', kind='final')

        response = self.client.post(
            reverse('sitesync:saved_reports_bulk_delete') + '?format=json',
            {
                'password_confirmation': 'pass123',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['code'], 'no_reports_selected')
        entry = AuditLogEntry.objects.filter(
            action_type=AUDIT_ACTION_REPORT_BULK_DELETE_DENIED,
            action_outcome=AuditLogEntry.OUTCOME_DENIED,
        ).latest('occurred_at_utc')
        self.assertIn('empty report selection', entry.message)


class SavedReportsDelegationModeConsistencyTest(TestCase):
    """Validate listing-to-editor access mode consistency for delegated users."""

    def setUp(self):
        self.client = Client()
        self.owner = get_user_model().objects.create_user(
            username='saved_owner',
            password='pass123',
        )
        self.delegate = get_user_model().objects.create_user(
            username='saved_delegate',
            password='pass123',
        )
        self.team = Team.objects.create(name='Saved Reports Team', level=1)
        self.site = Site.objects.create(
            external_id='site-ext-saved-delegation',
            name='Saved Delegation Site',
            description='Saved reports delegation demo site',
            team=self.team,
        )
        UserTeamAssignment.objects.create(user=self.owner, team=self.team)
        UserTeamAssignment.objects.create(user=self.delegate, team=self.team)
        self.report = MonthlyReport.objects.create(
            site=self.site,
            reporting_month='2026-07',
            owner_user=self.owner,
            created_by_user=self.owner,
            last_modified_by_user=self.owner,
            last_modified_at=timezone.now(),
        )

    def test_listing_and_editor_show_collaborator_mode_for_active_delegate(self):
        ReportWriteGrant.objects.create(
            report=self.report,
            granted_user=self.delegate,
            granted_by=self.owner,
            is_active=True,
        )

        self.client.force_login(self.delegate)
        list_response = self.client.get(reverse('sitesync:saved_reports'), {'format': 'json'})
        self.assertEqual(list_response.status_code, 200)
        list_payload = list_response.json()['reports']
        self.assertEqual(list_payload[0]['access_mode'], 'collaborator')

        editor_response = self.client.get(
            reverse('sitesync:report'),
            {'site_id': str(self.site.id), 'end_month': self.report.reporting_month},
        )
        self.client.logout()

        self.assertEqual(editor_response.status_code, 200)
        self.assertEqual(editor_response.context['report_access_mode'], 'collaborator')

    def test_listing_and_editor_switch_to_read_only_after_revoke(self):
        grant = ReportWriteGrant.objects.create(
            report=self.report,
            granted_user=self.delegate,
            granted_by=self.owner,
            is_active=True,
        )
        grant.is_active = False
        grant.revoked_by = self.owner
        grant.revoked_at = timezone.now()
        grant.save(update_fields=['is_active', 'revoked_by', 'revoked_at'])

        self.client.force_login(self.delegate)
        list_response = self.client.get(reverse('sitesync:saved_reports'), {'format': 'json'})
        self.assertEqual(list_response.status_code, 200)
        list_payload = list_response.json()['reports']
        self.assertEqual(list_payload[0]['access_mode'], 'read_only')

        editor_response = self.client.get(
            reverse('sitesync:report'),
            {'site_id': str(self.site.id), 'end_month': self.report.reporting_month},
        )
        self.client.logout()

        self.assertEqual(editor_response.status_code, 200)
        self.assertEqual(editor_response.context['report_access_mode'], 'read_only')
