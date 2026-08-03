from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from sitesync.models import MonthlyReport, ReportWriteGrant, RoleAssignment, Site, Team, UserTeamAssignment


User = get_user_model()


class ReportWriteDelegationAuthorityTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.owner = User.objects.create_user(username='owner_auth', email='owner_auth@example.com', password='pw123456')
        self.delegate = User.objects.create_user(username='delegate_auth', email='delegate_auth@example.com', password='pw123456')
        self.other_scope_user = User.objects.create_user(username='outscope_auth', email='outscope_auth@example.com', password='pw123456')
        self.team_lead = User.objects.create_user(username='lead_auth', email='lead_auth@example.com', password='pw123456')
        self.other_team_lead = User.objects.create_user(username='other_lead_auth', email='other_lead_auth@example.com', password='pw123456')
        self.manager = User.objects.create_user(username='manager_auth', email='manager_auth@example.com', password='pw123456')
        self.sibling_user = User.objects.create_user(username='sibling_auth', email='sibling_auth@example.com', password='pw123456')

        self.parent_team = Team.objects.create(name='Authority Parent Team', level=0, manager=self.manager)
        self.team = Team.objects.create(
            name='Authority Team',
            level=1,
            parent_team=self.parent_team,
            team_lead=self.team_lead,
            manager=self.manager,
        )
        self.sibling_team = Team.objects.create(
            name='Authority Sibling Team',
            level=1,
            parent_team=self.parent_team,
            team_lead=self.other_team_lead,
            manager=self.manager,
        )
        self.site = Site.objects.create(external_id='site-auth-1', name='Authority Site', team=self.team)

        UserTeamAssignment.objects.create(user=self.owner, team=self.team)
        UserTeamAssignment.objects.create(user=self.delegate, team=self.team)
        UserTeamAssignment.objects.create(user=self.team_lead, team=self.team)
        UserTeamAssignment.objects.create(user=self.other_team_lead, team=self.sibling_team)
        UserTeamAssignment.objects.create(user=self.manager, team=self.team)
        UserTeamAssignment.objects.create(user=self.sibling_user, team=self.sibling_team)

        other_team = Team.objects.create(name='Other Team', level=1)
        UserTeamAssignment.objects.create(user=self.other_scope_user, team=other_team)

        RoleAssignment.objects.create(user=self.team_lead, role_name='team_lead')
        RoleAssignment.objects.create(user=self.other_team_lead, role_name='team_lead')
        RoleAssignment.objects.create(user=self.manager, role_name='manager')

        self.report = MonthlyReport.objects.create(
            site=self.site,
            reporting_month='2026-07',
            owner_user=self.owner,
            created_by_user=self.owner,
            last_modified_by_user=self.owner,
            last_modified_at=timezone.now(),
        )

    def test_owner_grant_requires_same_team_delegate(self):
        self.client.force_login(self.owner)
        bad_response = self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.other_scope_user.id)},
        )
        self.client.logout()

        self.assertEqual(bad_response.status_code, 400)

        self.client.force_login(self.owner)
        ok_response = self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.delegate.id)},
        )
        self.client.logout()
        self.assertEqual(ok_response.status_code, 200)

    def test_team_lead_and_manager_can_grant_in_scope_including_self(self):
        self.client.force_login(self.team_lead)
        lead_self = self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.team_lead.id)},
        )
        self.client.logout()
        self.assertEqual(lead_self.status_code, 200)

        self.client.force_login(self.manager)
        manager_delegate = self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.delegate.id)},
        )
        self.client.logout()
        self.assertEqual(manager_delegate.status_code, 200)

        self.client.force_login(self.team_lead)
        lead_cross_team = self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.sibling_user.id)},
        )
        self.client.logout()
        self.assertEqual(lead_cross_team.status_code, 400)

        self.client.force_login(self.other_team_lead)
        cross_team_report_grant = self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.sibling_user.id)},
        )
        self.client.logout()
        self.assertEqual(cross_team_report_grant.status_code, 403)

        self.client.force_login(self.manager)
        manager_cross_team = self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.sibling_user.id)},
        )
        self.client.logout()
        self.assertEqual(manager_cross_team.status_code, 200)

        self.client.force_login(self.manager)
        cross_scope = self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.other_scope_user.id)},
        )
        self.client.logout()
        self.assertEqual(cross_scope.status_code, 400)

    def test_original_grantor_and_lead_manager_can_revoke(self):
        self.client.force_login(self.team_lead)
        self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.delegate.id)},
        )
        self.client.logout()

        self.client.force_login(self.team_lead)
        lead_revoke = self.client.post(
            reverse('sitesync:report_delegation_revoke', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.delegate.id)},
        )
        self.client.logout()
        self.assertEqual(lead_revoke.status_code, 200)

        self.client.force_login(self.manager)
        self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.delegate.id)},
        )
        self.client.logout()

        self.client.force_login(self.owner)
        owner_revoke = self.client.post(
            reverse('sitesync:report_delegation_revoke', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.delegate.id)},
        )
        self.client.logout()
        self.assertEqual(owner_revoke.status_code, 200)

        self.assertFalse(ReportWriteGrant.objects.filter(report=self.report, granted_user=self.delegate, is_active=True).exists())

    def test_parent_team_manager_can_grant_for_child_team_report(self):
        parent_manager = User.objects.create_user(
            username='parent_manager_auth',
            email='parent_manager_auth@example.com',
            password='pw123456',
        )
        parent_team = Team.objects.create(name='Authority Parent Team', level=0, manager=parent_manager)
        self.team.parent_team = parent_team
        self.team.save(update_fields=['parent_team'])

        self.client.force_login(parent_manager)
        response = self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.delegate.id)},
        )
        self.client.logout()

        self.assertEqual(response.status_code, 200)

    def test_admin_user_can_grant_in_scope(self):
        admin_user = User.objects.create_user(
            username='admin_auth',
            email='admin_auth@example.com',
            password='pw123456',
            is_staff=True,
            is_superuser=True,
        )

        self.client.force_login(admin_user)
        response = self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.delegate.id)},
        )
        self.client.logout()

        self.assertEqual(response.status_code, 200)

    def test_manager_can_grant_when_site_team_is_missing_using_owner_scope(self):
        self.site.team = None
        self.site.save(update_fields=['team'])

        self.client.force_login(self.manager)
        response = self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.delegate.id)},
        )
        self.client.logout()

        self.assertEqual(response.status_code, 200)

    def test_admin_can_grant_any_active_user_when_site_team_is_missing(self):
        self.site.team = None
        self.site.save(update_fields=['team'])

        admin_user = User.objects.create_user(
            username='admin_any_auth',
            email='admin_any_auth@example.com',
            password='pw123456',
            is_staff=True,
            is_superuser=True,
        )

        self.client.force_login(admin_user)
        response = self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': self.report.id}),
            {'granted_user_id': str(self.other_scope_user.id)},
        )
        self.client.logout()

        self.assertEqual(response.status_code, 200)
