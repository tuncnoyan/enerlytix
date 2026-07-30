from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from sitesync.models import AuditLogEntry


class AuditLogViewerFilterIntegrationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_user(
            username='admin_filters',
            email='admin_filters@example.com',
            password='StrongPass123!',
            is_staff=True,
            is_superuser=True,
        )
        self.non_admin_user = user_model.objects.create_user(
            username='non_admin_filters',
            email='non_admin_filters@example.com',
            password='StrongPass123!',
        )
        self.actor_a = user_model.objects.create_user(
            username='actor_a',
            email='actor_a@example.com',
            password='StrongPass123!',
        )
        self.actor_b = user_model.objects.create_user(
            username='actor_b',
            email='actor_b@example.com',
            password='StrongPass123!',
        )

        now = timezone.now()
        AuditLogEntry.objects.create(
            actor_user=self.actor_a,
            actor_username_snapshot=self.actor_a.username,
            action_type='REPORT_SAVE_DRAFT',
            action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
            target_entity_type='report',
            target_entity_id='r-1',
            target_entity_label='Report 1',
            message='Energy anomaly found and saved.',
            occurred_at_utc=now - timedelta(hours=1),
        )
        AuditLogEntry.objects.create(
            actor_user=self.actor_b,
            actor_username_snapshot=self.actor_b.username,
            action_type='ADMIN_DELETE_USER',
            action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
            target_entity_type='user',
            target_entity_id='u-2',
            target_entity_label='legacy_user',
            message='Deleted user account.',
            occurred_at_utc=now - timedelta(days=5),
        )

    def test_non_admin_access_is_redirected(self):
        self.client.force_login(self.non_admin_user)

        response = self.client.get(reverse('sitesync:admin_audit_logs'))

        self.assertEqual(response.status_code, 302)

    def test_combined_filters_return_expected_subset(self):
        self.client.force_login(self.admin_user)
        start = (timezone.now() - timedelta(days=1)).isoformat()
        end = timezone.now().isoformat()

        response = self.client.get(
            reverse('sitesync:admin_audit_logs'),
            {
                'user': str(self.actor_a.id),
                'keyword': 'anomaly',
                'action_type': 'REPORT_SAVE_DRAFT',
                'start': start,
                'end': end,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'REPORT_SAVE_DRAFT')
        self.assertContains(response, 'actor_a')
        self.assertNotContains(response, 'Deleted user account.')
