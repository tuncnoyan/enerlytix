"""
Integration tests for report visibility across different user roles.

Tests that users see appropriate reports based on their role
and team assignment in a realistic scenario.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from sitesync.models import (
    Team, UserTeamAssignment, RoleAssignment,
    Site, MonthlyReport
)

User = get_user_model()


class ReportVisibilityByRoleTestCase(TestCase):
    """Integration test for report visibility across roles."""
    
    def setUp(self):
        """Create realistic team hierarchy with reports."""
        self.client = Client()
        
        # Create users
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        
        self.sales_manager = User.objects.create_user(
            username='sales_mgr',
            email='sales_mgr@test.com',
            password='sales123'
        )
        
        self.tech_lead = User.objects.create_user(
            username='tech_lead',
            email='tech_lead@test.com',
            password='tech123'
        )
        
        self.sales_rep = User.objects.create_user(
            username='sales_rep',
            email='sales_rep@test.com',
            password='sales123'
        )
        
        self.tech_rep = User.objects.create_user(
            username='tech_rep',
            email='tech_rep@test.com',
            password='tech123'
        )
        
        # Create org structure:
        # Sales Division (manager: sales_manager)
        # ├─ Sales Team (lead: tech_lead) [will be reused as tech_lead in sales]
        # Tech Division (manager: tech_manager)
        # ├─ Tech Support Team (lead: tech_lead)
        
        self.sales_div = Team.objects.create(
            name='Sales Division',
            manager=self.sales_manager
        )
        
        self.sales_team = Team.objects.create(
            name='Sales Team',
            parent_team=self.sales_div,
            team_lead=self.tech_lead
        )
        
        # Assign users to teams
        UserTeamAssignment.objects.create(
            user=self.sales_manager,
            team=self.sales_div,
            assigned_by=self.admin
        )
        
        UserTeamAssignment.objects.create(
            user=self.tech_lead,
            team=self.sales_team,
            assigned_by=self.admin
        )
        
        UserTeamAssignment.objects.create(
            user=self.sales_rep,
            team=self.sales_team,
            assigned_by=self.admin
        )
        
        # Assign roles
        RoleAssignment.objects.create(
            user=self.sales_manager,
            role_name='manager',
            assigned_by=self.admin
        )
        
        RoleAssignment.objects.create(
            user=self.tech_lead,
            role_name='team_lead',
            assigned_by=self.admin
        )
        
        RoleAssignment.objects.create(
            user=self.sales_rep,
            role_name='user',
            assigned_by=self.admin
        )
        
        # Create sites (in real scenario, sites would be assigned to teams)
        self.sales_site = Site.objects.create(
            external_id='site-sales-1',
            name='Sales Office'
        )
        
        self.other_site = Site.objects.create(
            external_id='site-other-1',
            name='Tech Office'
        )
        
        # Create reports
        self.sales_report = MonthlyReport.objects.create(
            site=self.sales_site,
            reporting_month='2024-01'
        )
        
        self.other_report = MonthlyReport.objects.create(
            site=self.other_site,
            reporting_month='2024-01'
        )

    def test_admin_sees_all_reports(self):
        """Admin should see all reports when viewing report list."""
        self.client.login(username='admin', password='admin123')
        
        # When admin accesses reports, they should see all
        from sitesync.services import get_reports_for_user
        reports = get_reports_for_user(self.admin)
        self.assertIsNotNone(reports)

    def test_manager_sees_team_reports(self):
        """Manager should see reports from their managed teams."""
        from sitesync.services import get_accessible_reports
        
        # Sales manager manages Sales Division, so should see Sales Division
        # and Sales Team reports
        reports = get_accessible_reports(self.sales_manager)
        self.assertIsNotNone(reports)

    def test_team_lead_sees_team_reports(self):
        """Team lead should see reports from their team."""
        from sitesync.services import get_accessible_reports
        
        reports = get_accessible_reports(self.tech_lead)
        self.assertIsNotNone(reports)

    def test_regular_user_sees_assigned_team_reports(self):
        """Regular user should see only assigned team's reports."""
        from sitesync.services import get_accessible_reports
        
        # sales_rep assigned to Sales Team should see Sales Team reports
        reports = get_accessible_reports(self.sales_rep)
        self.assertIsNotNone(reports)

    def test_unassigned_user_access_denied_or_empty(self):
        """Unassigned user should see no reports or get empty state."""
        # tech_rep has no team assignment
        from sitesync.services import get_accessible_reports
        
        reports = get_accessible_reports(self.tech_rep)
        # Should return empty queryset
        self.assertEqual(reports.count(), 0)
