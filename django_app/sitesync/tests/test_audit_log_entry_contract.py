from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from sitesync.models import AuditLogEntry


class AuditLogEntryContractTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='audit_admin',
            email='audit_admin@example.com',
            password='StrongPass123!',
            is_staff=True,
        )

    def test_audit_log_entry_persists_required_fields(self):
        entry = AuditLogEntry.objects.create(
            actor_user=self.user,
            actor_username_snapshot=self.user.username,
            source_ip='127.0.0.1',
            action_type='ADMIN_ENABLE_USER',
            action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
            target_entity_type='user',
            target_entity_id='42',
            target_entity_label='target_user',
            message='Enabled target user.',
            request_path='/panel/users/',
            metadata_json={'from': 'contract_test'},
        )

        self.assertIsNotNone(entry.id)
        self.assertIsNotNone(entry.occurred_at_utc)
        self.assertEqual(entry.actor_username_snapshot, 'audit_admin')
        self.assertEqual(entry.action_type, 'ADMIN_ENABLE_USER')
        self.assertEqual(entry.action_outcome, AuditLogEntry.OUTCOME_SUCCESS)
        self.assertEqual(entry.target_entity_type, 'user')
        self.assertEqual(entry.target_entity_id, '42')
        self.assertEqual(entry.target_entity_label, 'target_user')
        self.assertEqual(entry.message, 'Enabled target user.')
        self.assertEqual(entry.request_path, '/panel/users/')
        self.assertEqual(entry.metadata_json['from'], 'contract_test')

    def test_audit_log_outcome_values_cover_success_denied_failed(self):
        outcomes = {choice[0] for choice in AuditLogEntry.OUTCOME_CHOICES}
        self.assertEqual(
            outcomes,
            {
                AuditLogEntry.OUTCOME_SUCCESS,
                AuditLogEntry.OUTCOME_DENIED,
                AuditLogEntry.OUTCOME_FAILED,
            },
        )

    def test_occurred_at_defaults_to_current_utc_window(self):
        before = timezone.now()
        entry = AuditLogEntry.objects.create(
            actor_user=self.user,
            actor_username_snapshot=self.user.username,
            action_type='ADMIN_VIEW_AUDIT_LOG',
            action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
            target_entity_type='audit_log',
            message='Viewed audit logs.',
        )
        after = timezone.now()

        self.assertGreaterEqual(entry.occurred_at_utc, before)
        self.assertLessEqual(entry.occurred_at_utc, after)
