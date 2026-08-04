from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from sitesync.models import Invitation


class InvitationModelTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='StrongPass123!',
        )

    def test_pending_invitation_is_valid(self):
        invitation = Invitation.objects.create(
            email='new-user@example.com',
            invited_by=self.admin_user,
        )

        self.assertTrue(invitation.is_valid())

    def test_accepted_invitation_is_invalid(self):
        invitation = Invitation.objects.create(
            email='accepted-user@example.com',
            invited_by=self.admin_user,
            status=Invitation.STATUS_ACCEPTED,
        )

        self.assertFalse(invitation.is_valid())

    def test_revoked_invitation_is_invalid(self):
        invitation = Invitation.objects.create(
            email='revoked-user@example.com',
            invited_by=self.admin_user,
            status=Invitation.STATUS_REVOKED,
        )

        self.assertFalse(invitation.is_valid())

    def test_invitation_acceptance_creates_user_and_marks_invitation_accepted(self):
        invitation = Invitation.objects.create(
            email='join-me@example.com',
            invited_by=self.admin_user,
        )

        response = self.client.post(
            reverse('sitesync:accept_invitation', kwargs={'invitation_id': invitation.id}),
            {
                'first_name': 'New',
                'last_name': 'Joiner',
                'username': 'new_joiner',
                'password': 'StrongPass123!',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(get_user_model().objects.filter(username='new_joiner').exists())
        created_user = get_user_model().objects.get(username='new_joiner')
        self.assertEqual(created_user.first_name, 'New')
        self.assertEqual(created_user.last_name, 'Joiner')
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, Invitation.STATUS_ACCEPTED)

    def test_revoked_invitation_link_is_rejected(self):
        invitation = Invitation.objects.create(
            email='blocked@example.com',
            invited_by=self.admin_user,
        )
        invitation.revoke()

        response = self.client.get(
            reverse('sitesync:accept_invitation', kwargs={'invitation_id': invitation.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This invitation is no longer valid.')
