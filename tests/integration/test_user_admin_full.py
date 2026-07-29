"""
Comprehensive integration test for complete user administration flow.

Tests the end-to-end user admin user story:
Create user via invitation → list users → enable/disable → rename → reset password → delete
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from sitesync.models import Invitation

User = get_user_model()


class UserAdminFlowTestCase(TestCase):
    """Comprehensive test of user admin flow (Phase 3 - US3)."""
    
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
        
        # Login as admin
        self.client.login(username='admin', password='admin123')
    
    def test_create_user_via_invitation(self):
        """Test creating user through invitation process."""
        # Create invitation via admin view
        response = self.client.post(
            reverse('sitesync:user_admin'),
            {
                'action': 'send_invitation',
                'email': 'newadmin@test.com'
            },
            follow=True
        )
        
        # Verify invitation was created
        invitation = Invitation.objects.get(email='newadmin@test.com')
        self.assertEqual(invitation.status, Invitation.STATUS_PENDING)
    
    def test_user_enable_disable(self):
        """Test disabling and enabling user accounts."""
        # Create user
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='pass123'
        )
        
        # Disable user
        response = self.client.post(
            reverse('sitesync:user_admin'),
            {
                'action': 'disable_user',
                'user_id': user.id
            },
            follow=True
        )
        
        # Verify user is inactive
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        
        # Re-enable user
        response = self.client.post(
            reverse('sitesync:user_admin'),
            {
                'action': 'enable_user',
                'user_id': user.id
            },
            follow=True
        )
        
        # Verify user is active again
        user.refresh_from_db()
        self.assertTrue(user.is_active)
    
    def test_list_users_with_pagination(self):
        """Test listing users with pagination."""
        # Create multiple users
        for i in range(25):
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@test.com',
                password='pass123'
            )
        
        # Access user list
        response = self.client.get(reverse('sitesync:user_admin'))
        
        # Verify pagination present
        self.assertIn('paginator', response.context)
