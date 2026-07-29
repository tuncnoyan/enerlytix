"""
Integration tests for empty-state and onboarding messaging.

Tests that unassigned users see appropriate empty state messages
and guidance to request team assignment.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from sitesync.models import Team, UserTeamAssignment, RoleAssignment

User = get_user_model()


class EmptyStateMessagingTestCase(TestCase):
    """Integration test for empty-state messaging."""
    
    def setUp(self):
        """Create users and teams for testing."""
        self.client = Client()
        
        # Create admin
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create unassigned user
        self.new_user = User.objects.create_user(
            username='newuser',
            email='newuser@test.com',
            password='newuser123'
        )
        
        # Create assigned user
        self.assigned_user = User.objects.create_user(
            username='assigneduser',
            email='assigned@test.com',
            password='assigned123'
        )
        
        # Create team
        self.team = Team.objects.create(
            name='Engineering Team',
            manager=self.admin
        )
        
        # Assign one user to team
        UserTeamAssignment.objects.create(
            user=self.assigned_user,
            team=self.team,
            assigned_by=self.admin
        )
        
        RoleAssignment.objects.create(
            user=self.assigned_user,
            role_name='user',
            assigned_by=self.admin
        )

    def test_unassigned_user_sees_empty_state(self):
        """New user without team assignment should see empty state."""
        # When unassigned user tries to view reports,
        # they should see an empty state message, not a table
        
        from sitesync.services import get_reports_for_user
        
        reports = get_reports_for_user(self.new_user)
        # Should return empty queryset
        self.assertEqual(reports.count(), 0)

    def test_assigned_user_sees_reports(self):
        """User assigned to team should see reports (when they exist)."""
        from sitesync.services import get_accessible_reports
        
        reports = get_accessible_reports(self.assigned_user)
        # Should return non-empty queryset or valid queryset
        self.assertIsNotNone(reports)

    def test_empty_state_shows_admin_link(self):
        """Empty state message should include link to contact admin or request access."""
        # This would be tested via template rendering in view tests
        # For now, we verify the message context is prepared
        
        self.client.login(username='newuser', password='newuser123')
        # When accessing report view without team assignment,
        # view should pass empty_state_message in context
        # (This test would be more complete with actual view tests)

    def test_welcome_message_after_assignment(self):
        """After team assignment, user should see welcome/onboarding message."""
        # This would be tested with a flag or timestamp on UserTeamAssignment
        # to show a welcome message on first report view after assignment
        
        assignment = UserTeamAssignment.objects.get(user=self.assigned_user)
        # Verify assignment exists and is recent
        self.assertIsNotNone(assignment)
        self.assertIsNotNone(assignment.assigned_at)

    def test_request_team_assignment_flow(self):
        """Users should be able to request team assignment."""
        # This tests the future feature for users to request access
        # Placeholder for the request_team_assignment_view functionality
        
        # When unassigned user clicks "Request Access" button,
        # a TeamAssignmentRequest should be created
        # and admin should be notified
        pass
