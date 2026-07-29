"""
Comprehensive integration test for team hierarchy creation and changes.

Tests the end-to-end team hierarchy user story:
Create root team → add sub-team → change manager → change hierarchy → move team → delete team with cascade
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from sitesync.models import Team, UserTeamAssignment, RoleAssignment

User = get_user_model()


class TeamHierarchyFlowTestCase(TestCase):
    """Comprehensive test of team hierarchy flow (Phase 4 - US4)."""
    
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
        
        self.manager1 = User.objects.create_user(
            username='manager1',
            email='manager1@test.com',
            password='pass123'
        )
        
        self.manager2 = User.objects.create_user(
            username='manager2',
            email='manager2@test.com',
            password='pass123'
        )
        
        # Login as admin
        self.client.login(username='admin', password='admin123')
    
    def test_create_root_team(self):
        """Test creating a root team."""
        team = Team.objects.create(
            name='Root Team',
            manager=self.manager1
        )
        
        self.assertIsNone(team.parent_team)
        self.assertEqual(team.manager, self.manager1)
        self.assertEqual(str(team), 'Root Team')
    
    def test_create_team_hierarchy(self):
        """Test creating multi-level team hierarchy."""
        root = Team.objects.create(
            name='Root',
            manager=self.manager1
        )
        
        sub1 = Team.objects.create(
            name='Sub Team 1',
            parent_team=root,
            manager=self.manager2
        )
        
        sub2 = Team.objects.create(
            name='Sub Team 2',
            parent_team=sub1
        )
        
        # Verify hierarchy
        self.assertEqual(sub1.parent_team, root)
        self.assertEqual(sub2.parent_team, sub1)
        
        # Verify traversal
        parents = sub2.get_parent_teams()
        self.assertIn(sub1, parents)
        self.assertIn(root, parents)
    
    def test_change_team_manager(self):
        """Test changing team manager."""
        team = Team.objects.create(
            name='Test Team',
            manager=self.manager1
        )
        
        # Change manager
        team.manager = self.manager2
        team.save()
        
        # Verify change
        team.refresh_from_db()
        self.assertEqual(team.manager, self.manager2)
    
    def test_move_team_in_hierarchy(self):
        """Test moving a team in the hierarchy."""
        root = Team.objects.create(name='Root', manager=self.manager1)
        sub1 = Team.objects.create(name='Sub1', parent_team=root)
        sub2 = Team.objects.create(name='Sub2', parent_team=root)
        sub1_child = Team.objects.create(name='Sub1-Child', parent_team=sub1)
        
        # Move sub1_child from sub1 to sub2
        sub1_child.parent_team = sub2
        sub1_child.save()
        
        # Verify move
        self.assertEqual(sub1_child.parent_team, sub2)
        self.assertNotIn(sub1_child, sub1.get_sub_teams())
        self.assertIn(sub1_child, sub2.get_sub_teams())
    
    def test_team_cascade_deletion(self):
        """Test that deleting team cascades to assignments."""
        team = Team.objects.create(name='Team to Delete')
        
        # Assign user to team
        assignment = UserTeamAssignment.objects.create(
            user=self.admin,
            team=team,
            assigned_by=self.admin
        )
        
        # Delete team
        team.delete()
        
        # Verify assignment was cascade-deleted
        self.assertFalse(UserTeamAssignment.objects.filter(id=assignment.id).exists())
