"""
Comprehensive integration test for admin panel access and layout.

Tests the end-to-end admin panel user story:
Admin sees panel link and can access → non-admin cannot → verify all sections load
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from sitesync.models import Team, UserTeamAssignment

User = get_user_model()


class AdminPanelAccessFlowTestCase(TestCase):
    """Comprehensive test of admin panel access flow (Phase 5 - US5)."""
    
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
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='pass123'
        )
    
    def test_admin_can_access_panel(self):
        """Test that admin user can access admin panel."""
        self.client.login(username='admin', password='admin123')
        
        # Access admin panel
        response = self.client.get(reverse('sitesync:admin_panel'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
    
    def test_non_admin_denied_access(self):
        """Test that non-admin user cannot access admin panel."""
        self.client.login(username='user', password='pass123')
        
        # Try to access admin panel
        response = self.client.get(reverse('sitesync:admin_panel'), follow=True)
        # Should redirect or 403
        self.assertNotEqual(response.status_code, 200)
    
    def test_admin_panel_shows_all_sections(self):
        """Test that all panel sections are accessible."""
        self.client.login(username='admin', password='admin123')
        
        sections = [
            ('sitesync:admin_users', 'admin_users'),
            ('sitesync:admin_teams', 'admin_teams'),
            ('sitesync:admin_hierarchy', 'admin_hierarchy'),
            ('sitesync:admin_roles', 'admin_roles'),
        ]
        
        for url_name, section_text in sections:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200, f"Section {url_name} not accessible")
    
    def test_admin_panel_displays_statistics(self):
        """Test that admin panel dashboard shows statistics."""
        # Create some test data
        for i in range(5):
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@test.com',
                password='pass123'
            )
        
        for i in range(3):
            Team.objects.create(name=f'Team {i}')
        
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get(reverse('sitesync:admin_panel'))
        self.assertContains(response, 'Total Users')
        self.assertContains(response, 'Total Teams')
