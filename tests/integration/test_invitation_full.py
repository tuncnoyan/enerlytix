"""
Comprehensive integration test for complete invitation flow.

Tests the end-to-end invitation user story:
Create invitation → expires → create new one → accept → verify user created
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from sitesync.models import Invitation

User = get_user_model()


class InvitationFlowTestCase(TestCase):
    """Comprehensive test of invitation flow (Phase 2 - US2)."""
    
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
    
    def test_invitation_expiry_and_renewal(self):
        """Test invitation expiry and creating new invitation."""
        # Create invitation
        invitation1 = Invitation.objects.create(
            email='test@test.com',
            created_by=self.admin,
            status=Invitation.STATUS_PENDING
        )
        
        # Verify it's valid
        self.assertTrue(invitation1.is_valid())
        
        # Manually expire it by setting expires_at to past
        invitation1.expires_at = timezone.now() - timedelta(days=1)
        invitation1.save()
        
        # Verify it's no longer valid
        self.assertFalse(invitation1.is_valid())
        
        # Create new invitation (old one still pending, this is ok in real flow)
        invitation2 = Invitation.objects.create(
            email='test@test.com',
            created_by=self.admin,
            status=Invitation.STATUS_PENDING
        )
        
        # Verify new one is valid
        self.assertTrue(invitation2.is_valid())
    
    def test_invitation_acceptance_creates_user(self):
        """Test that accepting invitation creates user account."""
        invitation = Invitation.objects.create(
            email='newuser@test.com',
            created_by=self.admin,
            status=Invitation.STATUS_PENDING
        )
        
        # Accept invitation
        self.client.post(
            reverse('sitesync:accept_invitation', args=[invitation.id]),
            {
                'password': 'testpass123',
                'password_confirm': 'testpass123',
                'first_name': 'New',
                'last_name': 'User'
            }
        )
        
        # Verify user was created
        user = User.objects.get(email='newuser@test.com')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'User')
        self.assertTrue(user.is_active)
        
        # Verify can login with new user
        login_ok = self.client.login(username='newuser@test.com', password='testpass123')
        self.assertTrue(login_ok)
