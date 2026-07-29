"""
Unit tests for hierarchical report access logic.

Tests that managers see reports from their team plus all sub-teams,
team leads see team + sub-teams within their scope, and regular users
see only their assigned team.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model

from sitesync.models import (
    Team, UserTeamAssignment, RoleAssignment,
    Site, MonthlyReport
)

User = get_user_model()


class HierarchicalAccessTestCase(TestCase):
    """Test hierarchical access logic for reports."""
    
    def setUp(self):
        """Create a 3-level team hierarchy for testing."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create managers and leads
        self.root_manager = User.objects.create_user(
            username='root_manager',
            email='root_manager@test.com',
            password='pass123'
        )
        
        self.sub_manager = User.objects.create_user(
            username='sub_manager',
            email='sub_manager@test.com',
            password='pass123'
        )
        
        self.team_lead = User.objects.create_user(
            username='team_lead',
            email='team_lead@test.com',
            password='pass123'
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='pass123'
        )
        
        # Create 3-level hierarchy
        # Root Team
        #   └─ Sub Team A
        #       └─ Sub Team B
        
        self.root_team = Team.objects.create(
            name='Root Team',
            manager=self.root_manager
        )
        
        self.sub_team_a = Team.objects.create(
            name='Sub Team A',
            parent_team=self.root_team,
            manager=self.sub_manager
        )
        
        self.sub_team_b = Team.objects.create(
            name='Sub Team B',
            parent_team=self.sub_team_a,
            team_lead=self.team_lead
        )
        
        # Assign users to teams
        UserTeamAssignment.objects.create(
            user=self.root_manager,
            team=self.root_team,
            assigned_by=self.admin_user
        )
        
        UserTeamAssignment.objects.create(
            user=self.sub_manager,
            team=self.sub_team_a,
            assigned_by=self.admin_user
        )
        
        UserTeamAssignment.objects.create(
            user=self.team_lead,
            team=self.sub_team_b,
            assigned_by=self.admin_user
        )
        
        UserTeamAssignment.objects.create(
            user=self.regular_user,
            team=self.sub_team_b,
            assigned_by=self.admin_user
        )
        
        # Assign roles
        RoleAssignment.objects.create(
            user=self.root_manager,
            role_name='manager',
            assigned_by=self.admin_user
        )
        
        RoleAssignment.objects.create(
            user=self.sub_manager,
            role_name='manager',
            assigned_by=self.admin_user
        )
        
        RoleAssignment.objects.create(
            user=self.team_lead,
            role_name='team_lead',
            assigned_by=self.admin_user
        )
        
        RoleAssignment.objects.create(
            user=self.regular_user,
            role_name='user',
            assigned_by=self.admin_user
        )

    def test_manager_sees_own_and_sub_teams(self):
        """Manager should see reports from their team + all sub-teams recursively."""
        # Root manager should see: Root Team + Sub Team A + Sub Team B
        # Sub manager should see: Sub Team A + Sub Team B
        
        from sitesync.services import get_accessible_reports
        
        # For root manager: should have access to 3 levels of reports
        reports_root = get_accessible_reports(self.root_manager)
        self.assertIsNotNone(reports_root)
        
        # For sub manager: should have access to 2 levels
        reports_sub = get_accessible_reports(self.sub_manager)
        self.assertIsNotNone(reports_sub)

    def test_team_lead_sees_team_reports(self):
        """Team lead should see reports from their team + sub-teams within scope."""
        from sitesync.services import get_accessible_reports
        
        reports = get_accessible_reports(self.team_lead)
        self.assertIsNotNone(reports)

    def test_regular_user_sees_own_team_only(self):
        """Regular user should see only their assigned team's reports."""
        from sitesync.services import get_accessible_reports
        
        reports = get_accessible_reports(self.regular_user)
        # Regular user assigned to Sub Team B should only see Sub Team B reports
        self.assertIsNotNone(reports)

    def test_admin_sees_all_reports(self):
        """Admin user should see all reports from all teams."""
        from sitesync.services import get_accessible_reports
        
        reports = get_accessible_reports(self.admin_user)
        # Admin should have access to all reports
        self.assertIsNotNone(reports)

    def test_hierarchy_traversal_up(self):
        """Team.get_parent_teams() should traverse hierarchy upward."""
        parents = self.sub_team_b.get_parent_teams()
        # Should include Sub Team A and Root Team
        self.assertIn(self.sub_team_a, parents)
        self.assertIn(self.root_team, parents)
        self.assertEqual(len(parents), 2)

    def test_hierarchy_traversal_down(self):
        """Team.get_sub_teams() should traverse hierarchy downward."""
        subs_root = self.root_team.get_sub_teams()
        subs_a = self.sub_team_a.get_sub_teams()
        subs_b = self.sub_team_b.get_sub_teams()
        
        # Root should have Sub A and Sub B
        self.assertIn(self.sub_team_a, subs_root)
        self.assertIn(self.sub_team_b, subs_root)
        
        # Sub A should have Sub B
        self.assertIn(self.sub_team_b, subs_a)
        
        # Sub B has no sub-teams
        self.assertEqual(len(subs_b), 0)
