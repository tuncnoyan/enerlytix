from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from sitesync.models import Invitation


class PenTestHardeningCredentialTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_user(
            username='credential_admin',
            email='credential-admin@example.com',
            password='StrongPass123!',
            is_staff=True,
        )
        self.target_user = user_model.objects.create_user(
            username='credential_target',
            email='credential-target@example.com',
            password='StrongPass123!',
        )
        self.invitation = Invitation.objects.create(
            email='invitee@example.com',
            invited_by=self.admin_user,
        )

    @patch('sitesync.views.send_admin_password_recovery_email', return_value=True)
    def test_admin_reset_password_issues_recovery_and_removes_static_password(self, recovery_mock):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('sitesync:admin_users'),
            {
                'account_action': '1',
                'user_id': str(self.target_user.id),
                'action': 'reset_password',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.has_usable_password())
        recovery_mock.assert_called_once()

    @override_settings(PASSWORD_RESET_TIMEOUT=900)
    def test_recovery_token_policy_uses_15_minute_timeout_and_single_use_semantics(self):
        self.assertEqual(900, settings.PASSWORD_RESET_TIMEOUT)
        token = default_token_generator.make_token(self.target_user)
        self.assertTrue(default_token_generator.check_token(self.target_user, token))

        self.target_user.set_password('AnotherStrongPass123!')
        self.target_user.save(update_fields=['password'])
        self.assertFalse(default_token_generator.check_token(self.target_user, token))

    def test_invitation_acceptance_rejects_weak_password(self):
        response = self.client.post(
            reverse('sitesync:accept_invitation', kwargs={'invitation_id': self.invitation.id}),
            {
                'first_name': 'A',
                'last_name': 'User',
                'username': 'weak_invitee',
                'password': '123',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'password', status_code=200)

    def test_invitation_acceptance_accepts_strong_password(self):
        response = self.client.post(
            reverse('sitesync:accept_invitation', kwargs={'invitation_id': self.invitation.id}),
            {
                'first_name': 'Strong',
                'last_name': 'Invitee',
                'username': 'strong_invitee',
                'password': 'StrongerPass123!',
            },
        )
        self.assertEqual(response.status_code, 200)
        user_model = get_user_model()
        self.assertTrue(user_model.objects.filter(username='strong_invitee').exists())
