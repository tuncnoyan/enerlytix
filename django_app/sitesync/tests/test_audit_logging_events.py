from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from sitesync.models import AuditLogEntry


class AuditLoggingEventsIntegrationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='StrongPass123!',
            is_staff=True,
            is_superuser=True,
        )
        self.standard_user = user_model.objects.create_user(
            username='standard_user',
            email='standard@example.com',
            password='StrongPass123!',
        )

    def test_user_admin_invitation_creation_writes_audit_event(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse('sitesync:user_admin'),
            {'create_invitation': '1', 'email': 'invitee@example.com'},
        )

        self.assertEqual(response.status_code, 200)
        event = AuditLogEntry.objects.filter(action_type='ADMIN_CREATE_INVITATION').first()
        self.assertIsNotNone(event)
        self.assertEqual(event.action_outcome, AuditLogEntry.OUTCOME_SUCCESS)
        self.assertEqual(event.actor_user_id, self.admin_user.id)
        self.assertIn('invitee@example.com', event.message)

    def test_non_admin_panel_access_is_denied_and_logged(self):
        self.client.force_login(self.standard_user)

        response = self.client.get(reverse('sitesync:admin_panel'))

        self.assertEqual(response.status_code, 302)
        event = AuditLogEntry.objects.filter(action_type='ACCESS_DENIED').first()
        self.assertIsNotNone(event)
        self.assertEqual(event.action_outcome, AuditLogEntry.OUTCOME_DENIED)
        self.assertEqual(event.actor_user_id, self.standard_user.id)
        self.assertEqual(event.target_entity_type, 'admin_panel')

    def test_deleted_user_action_keeps_readable_snapshot_in_audit_log(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse('sitesync:user_admin'),
            {
                'account_action': '1',
                'user_id': self.standard_user.id,
                'action': 'delete',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(id=self.standard_user.id).exists())

        event = AuditLogEntry.objects.filter(action_type='ADMIN_DELETE_USER').first()
        self.assertIsNotNone(event)
        self.assertEqual(event.action_outcome, AuditLogEntry.OUTCOME_SUCCESS)
        self.assertEqual(event.target_entity_type, 'user')
        self.assertEqual(event.target_entity_label, 'standard_user')
        self.assertIn('Deleted user standard_user', event.message)
