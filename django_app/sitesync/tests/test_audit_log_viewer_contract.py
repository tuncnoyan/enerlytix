from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from sitesync.models import AuditLogEntry


class AuditLogViewerContractTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_user(
            username='viewer_admin',
            email='viewer_admin@example.com',
            password='StrongPass123!',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.admin_user)
        AuditLogEntry.objects.create(
            actor_user=self.admin_user,
            actor_username_snapshot=self.admin_user.username,
            action_type='REPORT_SAVE_DRAFT',
            action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
            target_entity_type='report',
            message='Saved report draft.',
            occurred_at_utc=timezone.now(),
        )

    def test_invalid_filter_combination_returns_200_with_inline_errors(self):
        start = timezone.now()
        end = start - timedelta(days=1)

        response = self.client.get(
            reverse('sitesync:admin_audit_logs'),
            {'start': start.isoformat(), 'end': end.isoformat()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please fix filter errors before retrying.')

    def test_start_only_filter_is_accepted(self):
        response = self.client.get(
            reverse('sitesync:admin_audit_logs'),
            {'start': timezone.now().isoformat()},
        )

        self.assertEqual(response.status_code, 200)

    def test_end_only_filter_is_accepted(self):
        response = self.client.get(
            reverse('sitesync:admin_audit_logs'),
            {'end': timezone.now().isoformat()},
        )

        self.assertEqual(response.status_code, 200)
