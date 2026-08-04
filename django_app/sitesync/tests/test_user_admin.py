from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from sitesync.models import AuditLogEntry, Invitation


class UserAdminTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.admin_user = self.user_model.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='StrongPass123!',
            is_staff=True,
            is_superuser=True,
        )
        self.standard_user = self.user_model.objects.create_user(
            username='standard_user',
            email='standard@example.com',
            password='StrongPass123!',
        )

    def test_admin_user_list_requires_admin_role(self):
        self.client.force_login(self.standard_user)

        response = self.client.get(reverse('sitesync:user_admin'))

        self.assertEqual(response.status_code, 302)

    def test_admin_user_list_is_available_for_admin(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse('sitesync:user_admin'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'standard_user')

    @patch('sitesync.views.EmailMessage.send', return_value=1)
    def test_admin_can_create_invitation_from_user_admin_page(self, mocked_send):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse('sitesync:user_admin'),
            {'create_invitation': '1', 'email': 'invitee@example.com'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Invitation.objects.filter(email='invitee@example.com').exists())
        mocked_send.assert_called_once()

    def test_mailtrap_backend_class_is_configured(self):
        self.assertEqual(settings.CONFIGURED_EMAIL_BACKEND, 'anymail.backends.mailtrap.EmailBackend')
        self.assertEqual(settings.MAILTRAP_EMAIL_BACKEND, 'anymail.backends.mailtrap.EmailBackend')

    @patch('sitesync.views.EmailMessage.send', return_value=1)
    def test_invitation_email_send_is_attempted_and_logged_successfully(self, mocked_send):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse('sitesync:user_admin'),
            {'create_invitation': '1', 'email': 'mailtrap-success@example.com'},
        )

        self.assertEqual(response.status_code, 200)
        mocked_send.assert_called_once()
        email_event = AuditLogEntry.objects.filter(action_type='ADMIN_SEND_INVITATION_EMAIL').first()
        self.assertIsNotNone(email_event)
        self.assertEqual(email_event.action_outcome, AuditLogEntry.OUTCOME_SUCCESS)
        self.assertIn('mailtrap-success@example.com', email_event.message)

    @patch('sitesync.views.EmailMessage.send', side_effect=Exception('simulated-mail-failure'))
    def test_invitation_email_send_failure_is_logged(self, mocked_send):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse('sitesync:user_admin'),
            {'create_invitation': '1', 'email': 'mailtrap-fail@example.com'},
        )

        self.assertEqual(response.status_code, 200)
        mocked_send.assert_called_once()
        self.assertTrue(Invitation.objects.filter(email='mailtrap-fail@example.com').exists())
        email_event = AuditLogEntry.objects.filter(action_type='ADMIN_SEND_INVITATION_EMAIL').first()
        self.assertIsNotNone(email_event)
        self.assertEqual(email_event.action_outcome, AuditLogEntry.OUTCOME_FAILED)
        self.assertIn('mailtrap-fail@example.com', email_event.message)
        self.assertEqual(email_event.metadata_json.get('error'), 'simulated-mail-failure')

    def test_admin_can_disable_and_enable_user_account(self):
        self.client.force_login(self.admin_user)

        self.client.post(
            reverse('sitesync:user_admin'),
            {'account_action': '1', 'user_id': self.standard_user.id, 'action': 'disable'},
        )
        self.standard_user.refresh_from_db()
        self.assertFalse(self.standard_user.is_active)

        self.client.post(
            reverse('sitesync:user_admin'),
            {'account_action': '1', 'user_id': self.standard_user.id, 'action': 'enable'},
        )
        self.standard_user.refresh_from_db()
        self.assertTrue(self.standard_user.is_active)
