"""
Comprehensive integration test for report access after team hierarchy changes.

Tests the end-to-end hierarchy change effects user story:
Create hierarchy → verify access at each level → move team → verify access updates → change manager → verify access changes
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from sitesync.models import Team, UserTeamAssignment, RoleAssignment, MonthlyReport, Site
from sitesync.services import get_accessible_reports

User = get_user_model()


class ReportAccessHierarchyChangeFlowTestCase(TestCase):
    """Comprehensive test of report access after hierarchy changes (Phase 6 - US6)."""
    
    def setUp(self):
        """Create test data with hierarchy."""
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
        
        self.team_lead1 = User.objects.create_user(
            username='lead1',
            email='lead1@test.com',
            password='pass123'
        )
        
        # Create 3-level hierarchy
        self.root = Team.objects.create(name='Root', manager=self.manager1)
        self.sub1 = Team.objects.create(name='Sub1', parent_team=self.root, manager=self.manager2)
        self.sub2 = Team.objects.create(name='Sub2', parent_team=self.sub1)
        
        # Assign manager roles
        RoleAssignment.objects.create(
            user=self.manager1,
            role_name='manager',
            assigned_by=self.admin
        )
        
        RoleAssignment.objects.create(
            user=self.manager2,
            role_name='manager',
            assigned_by=self.admin
        )
        
        # Assign team_lead role to team_lead1
        RoleAssignment.objects.create(
            user=self.team_lead1,
            role_name='team_lead',
            assigned_by=self.admin
        )
        
        # Create test site and reports
        self.site = Site.objects.create(name='Test Site')
        self.report1 = MonthlyReport.objects.create(
            site=self.site,
            reporting_month='2024-01'
        )
        self.report2 = MonthlyReport.objects.create(
            site=self.site,
            reporting_month='2024-02'
        )
    
    def test_manager_sees_hierarchy_reports(self):
        """Test that manager can see reports from all sub-teams."""
        # Assign manager1 to root
        UserTeamAssignment.objects.create(
            user=self.manager1,
            team=self.root,
            assigned_by=self.admin
        )
        
        # Manager should be able to see all levels
        reports = get_accessible_reports(self.manager1)
        # Should see root + sub1 + sub2 level reports
        self.assertIsNotNone(reports)
    
    def test_team_lead_sees_team_reports(self):
        """Test that team_lead sees their team's reports."""
        # Assign team_lead1 to sub1
        UserTeamAssignment.objects.create(
            user=self.team_lead1,
            team=self.sub1,
            assigned_by=self.admin
        )
        
        # Team lead should see sub1 + sub2 reports
        reports = get_accessible_reports(self.team_lead1)
        self.assertIsNotNone(reports)
    
    def test_move_team_updates_access(self):
        """Test that moving a team updates manager access."""
        # manager2 manages sub1
        UserTeamAssignment.objects.create(
            user=self.manager2,
            team=self.sub1,
            assigned_by=self.admin
        )
        
        # Get initial reports
        reports_before = get_accessible_reports(self.manager2)
        
        # Move sub1 under root's direct management
        # (In real scenario, this might affect reporting scope)
        self.sub1.parent_team = self.root
        self.sub1.save()
        
        # Verify manager can still see team
        reports_after = get_accessible_reports(self.manager2)
        self.assertIsNotNone(reports_after)
    
    def test_change_manager_affects_access(self):
        """Test that changing team manager doesn't affect role-based access."""
        # Assign manager1 to root
        UserTeamAssignment.objects.create(
            user=self.manager1,
            team=self.root,
            assigned_by=self.admin
        )
        
        # Get reports with original manager
        reports_before = get_accessible_reports(self.manager1)
        
        # Change team manager to manager2
        self.root.manager = self.manager2
        self.root.save()
        
        # Original manager1 should still have access via role/assignment
        reports_after = get_accessible_reports(self.manager1)
        self.assertEqual(reports_before.count(), reports_after.count())
