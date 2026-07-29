from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from sitesync.models import Invitation


class InvitationModelTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='StrongPass123!',
        )

    def test_invitation_is_valid_until_expiry(self):
        invitation = Invitation.objects.create(
            email='new-user@example.com',
            invited_by=self.admin_user,
            expires_at=timezone.now() + timedelta(days=7),
        )

        self.assertTrue(invitation.is_valid())

    def test_expired_invitation_is_invalid(self):
        invitation = Invitation.objects.create(
            email='expired-user@example.com',
            invited_by=self.admin_user,
            expires_at=timezone.now() - timedelta(days=1),
        )

        self.assertFalse(invitation.is_valid())

    def test_invitation_acceptance_creates_user_and_marks_invitation_accepted(self):
        invitation = Invitation.objects.create(
            email='join-me@example.com',
            invited_by=self.admin_user,
            expires_at=timezone.now() + timedelta(days=7),
        )

        response = self.client.post(
            reverse('sitesync:accept_invitation', kwargs={'invitation_id': invitation.id}),
            {'username': 'new_joiner', 'password': 'StrongPass123!'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(get_user_model().objects.filter(username='new_joiner').exists())
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, Invitation.STATUS_ACCEPTED)
