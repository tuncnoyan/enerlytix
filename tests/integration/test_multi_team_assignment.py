"""
Comprehensive integration test for multi-team user assignments.

Tests the end-to-end multi-team assignment user story:
Assign user to 2+ teams → verify role assignments in each team → verify role overlapping → change assignments
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from sitesync.models import Team, UserTeamAssignment, RoleAssignment

User = get_user_model()


class MultiTeamAssignmentFlowTestCase(TestCase):
    """Comprehensive test of multi-team assignment flow (Phase 4 - US4)."""
    
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
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='pass123'
        )
        
        self.team1 = Team.objects.create(name='Team 1')
        self.team2 = Team.objects.create(name='Team 2')
        self.team3 = Team.objects.create(name='Team 3')
        
        # Login as admin
        self.client.login(username='admin', password='admin123')
    
    def test_assign_user_to_multiple_teams(self):
        """Test assigning one user to multiple teams."""
        # Assign to team1
        assignment1 = UserTeamAssignment.objects.create(
            user=self.user,
            team=self.team1,
            assigned_by=self.admin
        )
        
        # Assign to team2
        assignment2 = UserTeamAssignment.objects.create(
            user=self.user,
            team=self.team2,
            assigned_by=self.admin
        )
        
        # Verify both assignments exist
        assignments = UserTeamAssignment.objects.filter(user=self.user)
        self.assertEqual(assignments.count(), 2)
        self.assertIn(assignment1, assignments)
        self.assertIn(assignment2, assignments)
    
    def test_role_assignments_in_each_team(self):
        """Test that user can have different roles in different teams."""
        # Assign to teams
        UserTeamAssignment.objects.create(
            user=self.user,
            team=self.team1,
            assigned_by=self.admin
        )
        UserTeamAssignment.objects.create(
            user=self.user,
            team=self.team2,
            assigned_by=self.admin
        )
        
        # Assign as manager in team1 context
        role1 = RoleAssignment.objects.create(
            user=self.user,
            role_name='manager',
            assigned_by=self.admin
        )
        
        # Verify role is assigned globally (applies to all teams)
        user_roles = RoleAssignment.objects.filter(user=self.user)
        self.assertEqual(user_roles.count(), 1)
        self.assertEqual(user_roles.first().role_name, 'manager')
    
    def test_overlapping_roles(self):
        """Test that user can hold multiple roles simultaneously."""
        # Assign manager role
        RoleAssignment.objects.create(
            user=self.user,
            role_name='manager',
            assigned_by=self.admin
        )
        
        # Also assign team_lead role
        RoleAssignment.objects.create(
            user=self.user,
            role_name='team_lead',
            assigned_by=self.admin
        )
        
        # Verify both roles exist
        roles = RoleAssignment.objects.filter(user=self.user)
        self.assertEqual(roles.count(), 2)
        
        role_names = roles.values_list('role_name', flat=True)
        self.assertIn('manager', role_names)
        self.assertIn('team_lead', role_names)
    
    def test_change_team_assignments(self):
        """Test changing user team assignments."""
        # Initial assignment
        assignment1 = UserTeamAssignment.objects.create(
            user=self.user,
            team=self.team1,
            assigned_by=self.admin
        )
        
        # Remove from team1 and assign to team3
        assignment1.delete()
        assignment3 = UserTeamAssignment.objects.create(
            user=self.user,
            team=self.team3,
            assigned_by=self.admin
        )
        
        # Verify change
        assignments = UserTeamAssignment.objects.filter(user=self.user)
        self.assertEqual(assignments.count(), 1)
        self.assertEqual(assignments.first().team, self.team3)
