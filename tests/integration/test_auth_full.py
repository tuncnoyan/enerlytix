"""
Comprehensive integration test for complete authentication flow.

Tests the end-to-end authentication user story:
Sign up via invitation → login → password reset → logout → profile access
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from sitesync.models import Invitation

User = get_user_model()


class AuthenticationFlowTestCase(TestCase):
    """Comprehensive test of authentication flow (Phase 1 - US1)."""
    
    def setUp(self):
        """Create test data."""
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
    
    def test_complete_auth_flow(self):
        """Test complete auth flow: create invitation → accept → login → profile."""
        # Step 1: Create invitation
        invitation = Invitation.objects.create(
            email='newuser@test.com',
            created_by=self.admin,
            status=Invitation.STATUS_PENDING
        )
        self.assertEqual(invitation.status, Invitation.STATUS_PENDING)
        
        # Step 2: Accept invitation
        response = self.client.post(
            reverse('sitesync:accept_invitation', args=[invitation.id]),
            {
                'password': 'newpassword123',
                'password_confirm': 'newpassword123',
                'first_name': 'Test',
                'last_name': 'User'
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify user was created
        user = User.objects.get(email='newuser@test.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        
        # Step 3: Login
        login_ok = self.client.login(username='newuser@test.com', password='newpassword123')
        self.assertTrue(login_ok)
        
        # Step 4: Access profile
        response = self.client.get(reverse('sitesync:profile'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test User')
        
        # Step 5: Logout
        response = self.client.get(reverse('sitesync:logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Step 6: Verify can't access profile after logout
        response = self.client.get(reverse('sitesync:profile'), follow=True)
        # Should redirect to login
        self.assertIn('/login/', response.request['PATH_INFO'])
