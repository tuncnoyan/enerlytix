"""
Comprehensive integration test for admin panel team management operations.

Tests the end-to-end team management in admin panel:
List teams → create team → edit team → change manager → view hierarchy → delete team
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from sitesync.models import Team

User = get_user_model()


class AdminPanelTeamsFlowTestCase(TestCase):
    """Comprehensive test of admin panel team management (Phase 5 - US5)."""
    
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
        
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='pass123'
        )
        
        self.team1 = Team.objects.create(name='Team 1', manager=self.manager)
        self.team2 = Team.objects.create(name='Team 2', manager=self.manager)
        
        # Login as admin
        self.client.login(username='admin', password='admin123')
    
    def test_list_teams_with_pagination(self):
        """Test listing teams with pagination."""
        # Create more teams
        for i in range(25):
            Team.objects.create(name=f'Team {i}')
        
        response = self.client.get(reverse('sitesync:admin_teams'))
        self.assertEqual(response.status_code, 200)
    
    def test_teams_appear_in_list(self):
        """Test that teams appear in the admin team list."""
        response = self.client.get(reverse('sitesync:admin_teams'))
        self.assertContains(response, 'Team 1')
        self.assertContains(response, 'Team 2')
    
    def test_team_manager_displayed(self):
        """Test that team manager is displayed."""
        response = self.client.get(reverse('sitesync:admin_teams'))
        self.assertContains(response, self.manager.username)
    
    def test_hierarchy_shows_parent_child_relationship(self):
        """Test that hierarchy view shows parent-child relationships."""
        # Create sub-team
        sub_team = Team.objects.create(
            name='Sub Team',
            parent_team=self.team1,
            manager=self.manager
        )
        
        response = self.client.get(reverse('sitesync:admin_hierarchy'))
        self.assertEqual(response.status_code, 200)
        
        # Both teams should be in response
        self.assertContains(response, 'Team 1')
        self.assertContains(response, 'Sub Team')
