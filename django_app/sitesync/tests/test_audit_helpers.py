from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from sitesync.forms import AuditLogFilterForm
from sitesync.models import AuditLogEntry, MonthlyReport, Site, Team, UserTeamAssignment
from sitesync.services import (
    AUDIT_ACTION_REPORT_BULK_DELETE,
    AUDIT_ACTION_REPORT_BULK_DELETE_DENIED,
    check_audit_export_threshold,
    create_audit_log_entry,
    get_filtered_audit_logs,
)


class AuditHelpersUnitTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_user(
            username='helper_admin',
            email='helper_admin@example.com',
            password='StrongPass123!',
            is_staff=True,
            is_superuser=True,
        )
        self.other_user = user_model.objects.create_user(
            username='helper_other',
            email='helper_other@example.com',
            password='StrongPass123!',
        )

    def test_create_audit_log_entry_requires_non_empty_required_fields(self):
        with self.assertRaises(ValueError):
            create_audit_log_entry(
                actor_user=self.admin_user,
                action_type='',
                action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
                target_entity_type='report',
                message='ok',
            )

        with self.assertRaises(ValueError):
            create_audit_log_entry(
                actor_user=self.admin_user,
                action_type='REPORT_SAVE_DRAFT',
                action_outcome='UNKNOWN',
                target_entity_type='report',
                message='ok',
            )

        with self.assertRaises(ValueError):
            create_audit_log_entry(
                actor_user=self.admin_user,
                action_type='REPORT_SAVE_DRAFT',
                action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
                target_entity_type='',
                message='ok',
            )

        with self.assertRaises(ValueError):
            create_audit_log_entry(
                actor_user=self.admin_user,
                action_type='REPORT_SAVE_DRAFT',
                action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
                target_entity_type='report',
                message='',
            )

    def test_create_audit_log_entry_normalizes_username_and_metadata(self):
        entry = create_audit_log_entry(
            actor_user=self.admin_user,
            actor_username_snapshot='   ',
            action_type='REPORT_SAVE_DRAFT',
            action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
            target_entity_type='report',
            message='Saved.',
            metadata_json=['not-a-dict'],
        )

        self.assertEqual(entry.actor_username_snapshot, self.admin_user.username)
        self.assertEqual(entry.metadata_json, {})

    def test_filter_form_rejects_start_after_end(self):
        start = timezone.now()
        end = start - timedelta(hours=1)
        form = AuditLogFilterForm(
            {
                'start': start.isoformat(),
                'end': end.isoformat(),
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn('end', form.errors)

    def test_filter_form_trims_keyword_and_action_type(self):
        form = AuditLogFilterForm({'keyword': '  abc  ', 'action_type': '  REPORT_SAVE_DRAFT  '})

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['keyword'], 'abc')
        self.assertEqual(form.cleaned_data['action_type'], 'REPORT_SAVE_DRAFT')

    def test_get_filtered_audit_logs_applies_combined_filters(self):
        now = timezone.now()
        matched = AuditLogEntry.objects.create(
            actor_user=self.admin_user,
            actor_username_snapshot=self.admin_user.username,
            action_type='REPORT_SAVE_DRAFT',
            action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
            target_entity_type='report',
            target_entity_id='r-1',
            target_entity_label='Matched report',
            message='Matched message',
            occurred_at_utc=now,
        )
        AuditLogEntry.objects.create(
            actor_user=self.other_user,
            actor_username_snapshot=self.other_user.username,
            action_type='ADMIN_DELETE_USER',
            action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
            target_entity_type='user',
            target_entity_id='u-2',
            target_entity_label='Non matched',
            message='Other message',
            occurred_at_utc=now - timedelta(days=2),
        )

        queryset = get_filtered_audit_logs(
            filters={
                'user': self.admin_user,
                'keyword': 'matched',
                'start': now - timedelta(hours=1),
                'end': now + timedelta(hours=1),
                'action_type': 'REPORT_SAVE_DRAFT',
            }
        )

        self.assertEqual(list(queryset), [matched])

    def test_export_threshold_guard_returns_expected_tuple(self):
        AuditLogEntry.objects.create(
            actor_user=self.admin_user,
            actor_username_snapshot=self.admin_user.username,
            action_type='REPORT_SAVE_DRAFT',
            action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
            target_entity_type='report',
            message='Threshold baseline',
        )
        queryset = AuditLogEntry.objects.all()

        allowed, row_count = check_audit_export_threshold(queryset=queryset, limit=50000)
        self.assertTrue(allowed)
        self.assertEqual(row_count, 1)

        allowed_small_limit, row_count_small_limit = check_audit_export_threshold(queryset=queryset, limit=0)
        self.assertFalse(allowed_small_limit)
        self.assertEqual(row_count_small_limit, 1)


class SavedReportsBulkDeleteAuditTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.client = Client()
        self.non_admin = user_model.objects.create_user(
            username='bulk_non_admin',
            email='bulk_non_admin@example.com',
            password='StrongPass123!',
        )
        self.owner = user_model.objects.create_user(
            username='bulk_owner',
            email='bulk_owner@example.com',
            password='StrongPass123!',
        )
        team = Team.objects.create(name='Audit Delete Team', level=1)
        site = Site.objects.create(external_id='audit-delete-site', name='Audit Delete Site', team=team)
        UserTeamAssignment.objects.create(user=self.owner, team=team)
        self.report = MonthlyReport.objects.create(
            site=site,
            reporting_month='2026-08',
            owner_user=self.owner,
            created_by_user=self.owner,
            last_modified_by_user=self.owner,
            last_modified_at=timezone.now(),
            current_status=MonthlyReport.STATUS_DRAFT,
            validation_status=MonthlyReport.VALIDATION_DRAFT,
        )

    def test_non_admin_direct_bulk_delete_attempt_is_denied_and_audited(self):
        self.client.force_login(self.non_admin)
        response = self.client.post(
            reverse('sitesync:saved_reports_bulk_delete') + '?format=json',
            {
                'selected_report_ids': [str(self.report.id)],
                'password_confirmation': 'StrongPass123!',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(response.status_code, 403)
        payload = response.json()
        self.assertEqual(payload['code'], 'access_denied')
        self.assertTrue(MonthlyReport.objects.filter(id=self.report.id).exists())
        entry = AuditLogEntry.objects.filter(
            action_type=AUDIT_ACTION_REPORT_BULK_DELETE_DENIED,
            action_outcome=AuditLogEntry.OUTCOME_DENIED,
            actor_user=self.non_admin,
        ).latest('occurred_at_utc')
        self.assertIn('Denied bulk report delete attempt by non-admin user.', entry.message)
        self.assertIn('Audit Delete Site 2026-08', entry.message)

    def test_atomic_delete_failure_audit_message_includes_report_names(self):
        self.non_admin.is_staff = True
        self.non_admin.save(update_fields=['is_staff'])
        self.client.force_login(self.non_admin)

        blocked_id = '00000000-0000-0000-0000-000000000000'
        response = self.client.post(
            reverse('sitesync:saved_reports_bulk_delete') + '?format=json',
            {
                'selected_report_ids': [str(self.report.id), blocked_id],
                'password_confirmation': 'StrongPass123!',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.client.logout()

        self.assertEqual(response.status_code, 409)
        entry = AuditLogEntry.objects.filter(
            action_type=AUDIT_ACTION_REPORT_BULK_DELETE,
            action_outcome=AuditLogEntry.OUTCOME_FAILED,
            actor_user=self.non_admin,
        ).latest('occurred_at_utc')
        self.assertIn('Resolved reports:', entry.message)
        self.assertIn('Audit Delete Site 2026-08', entry.message)
        self.assertIn('Blocked report references: 00000000-0000-0000-0000-000000000000.', entry.message)
