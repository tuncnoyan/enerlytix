from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from sitesync.models import Invitation


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

    def test_admin_can_create_invitation_from_user_admin_page(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse('sitesync:user_admin'),
            {'create_invitation': '1', 'email': 'invitee@example.com'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Invitation.objects.filter(email='invitee@example.com').exists())

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
