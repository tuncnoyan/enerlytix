"""
Performance integration test for large team hierarchies.

Tests performance of access control with large organization structures:
100 users × 10 teams × 5-level hierarchy = 5000 potential access relationships
Verifies that report filtering completes in <1 second for any user
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.test.utils import override_settings
import time

from sitesync.models import Team, UserTeamAssignment, RoleAssignment, MonthlyReport, Site
from sitesync.services import get_accessible_reports

User = get_user_model()


@override_settings(DEBUG=True)  # Allow query counting
class LoadHierarchyPerformanceTestCase(TestCase):
    """Performance test for hierarchical team structures (Phase 7 - T082)."""
    
    @classmethod
    def setUpClass(cls):
        """Create large test dataset."""
        super().setUpClass()
        
        cls.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
            is_staff=True
        )
        
        # Create organization structure:
        # 10 teams total, 5-level deep hierarchy
        # 100 users assigned across teams
        
        # Create 10 root teams
        cls.teams = []
        for t in range(10):
            root = Team.objects.create(
                name=f'Division {t}',
                manager=cls.admin
            )
            cls.teams.append(root)
            
            # Create 4 levels of sub-teams
            parent = root
            for level in range(4):
                sub = Team.objects.create(
                    name=f'Division {t} - Level {level+1}',
                    parent_team=parent,
                    manager=cls.admin
                )
                cls.teams.append(sub)
                parent = sub
        
        # Create 100 users and assign to random teams
        cls.users = []
        for u in range(100):
            user = User.objects.create_user(
                username=f'user{u}',
                email=f'user{u}@test.com',
                password='pass123'
            )
            cls.users.append(user)
            
            # Assign to 1-3 random teams
            num_teams = (u % 3) + 1
            for i in range(num_teams):
                team_idx = (u * (i+1)) % len(cls.teams)
                UserTeamAssignment.objects.create(
                    user=user,
                    team=cls.teams[team_idx],
                    assigned_by=cls.admin
                )
        
        # Create managers and team leads
        for i, user in enumerate(cls.users[:20]):
            role = 'manager' if i % 2 == 0 else 'team_lead'
            RoleAssignment.objects.create(
                user=user,
                role_name=role,
                assigned_by=cls.admin
            )
        
        # Create test site and reports (100 reports)
        cls.site = Site.objects.create(name='Test Site')
        cls.reports = []
        for r in range(100):
            report = MonthlyReport.objects.create(
                site=cls.site,
                reporting_month=f'2024-{(r % 12) + 1:02d}'
            )
            cls.reports.append(report)
    
    def test_admin_loads_all_reports_fast(self):
        """Test that admin can load all reports in <500ms."""
        start = time.time()
        reports = get_accessible_reports(self.admin)
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        # Should load in reasonable time
        self.assertLess(elapsed, 500, f"Admin loading took {elapsed}ms, expected <500ms")
        self.assertGreaterEqual(reports.count(), 100)
    
    def test_manager_filters_team_hierarchy_fast(self):
        """Test that manager can filter to team hierarchy in <300ms."""
        # Get a manager user
        manager = None
        for user in self.users:
            if user.roleassignment_set.filter(role_name='manager').exists():
                manager = user
                break
        
        if not manager:
            self.skipTest("No manager users created")
        
        start = time.time()
        reports = get_accessible_reports(manager)
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        # Should filter in reasonable time despite hierarchy
        self.assertLess(elapsed, 300, f"Manager filtering took {elapsed}ms, expected <300ms")
    
    def test_regular_user_filters_team_fast(self):
        """Test that regular user can filter to team in <100ms."""
        # Get a regular user
        regular = self.users[0]
        
        start = time.time()
        reports = get_accessible_reports(regular)
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        # Should be very fast for single team access
        self.assertLess(elapsed, 100, f"User filtering took {elapsed}ms, expected <100ms")
    
    def test_deep_hierarchy_traversal_completes(self):
        """Test that deep hierarchy traversal completes successfully."""
        # Get a team from deep in hierarchy
        deep_team = self.teams[-1]  # Deepest team
        
        # Traverse up to root
        parents = deep_team.get_parent_teams()
        self.assertGreater(len(parents), 0, "Should find parent teams")
        
        # Traverse down from root
        root = self.teams[0]
        children = root.get_sub_teams()
        self.assertGreater(len(children), 0, "Should find sub-teams")
