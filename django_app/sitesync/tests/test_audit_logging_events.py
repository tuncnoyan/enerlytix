from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from sitesync.models import AuditLogEntry, MonthlyReport, ReportWriteDelegationEvent, Site, Team, UserTeamAssignment


class AuditLoggingEventsIntegrationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='StrongPass123!',
            is_staff=True,
            is_superuser=True,
        )
        self.standard_user = user_model.objects.create_user(
            username='standard_user',
            email='standard@example.com',
            password='StrongPass123!',
        )

    def test_user_admin_invitation_creation_writes_audit_event(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse('sitesync:user_admin'),
            {'create_invitation': '1', 'email': 'invitee@example.com'},
        )

        self.assertEqual(response.status_code, 200)
        event = AuditLogEntry.objects.filter(action_type='ADMIN_CREATE_INVITATION').first()
        self.assertIsNotNone(event)
        self.assertEqual(event.action_outcome, AuditLogEntry.OUTCOME_SUCCESS)
        self.assertEqual(event.actor_user_id, self.admin_user.id)
        self.assertIn('invitee@example.com', event.message)

    def test_non_admin_panel_access_is_denied_and_logged(self):
        self.client.force_login(self.standard_user)

        response = self.client.get(reverse('sitesync:admin_panel'))

        self.assertEqual(response.status_code, 302)
        event = AuditLogEntry.objects.filter(action_type='ACCESS_DENIED').first()
        self.assertIsNotNone(event)
        self.assertEqual(event.action_outcome, AuditLogEntry.OUTCOME_DENIED)
        self.assertEqual(event.actor_user_id, self.standard_user.id)
        self.assertEqual(event.target_entity_type, 'admin_panel')

    def test_deleted_user_action_keeps_readable_snapshot_in_audit_log(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse('sitesync:user_admin'),
            {
                'account_action': '1',
                'user_id': self.standard_user.id,
                'action': 'delete',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(id=self.standard_user.id).exists())

        event = AuditLogEntry.objects.filter(action_type='ADMIN_DELETE_USER').first()
        self.assertIsNotNone(event)
        self.assertEqual(event.action_outcome, AuditLogEntry.OUTCOME_SUCCESS)
        self.assertEqual(event.target_entity_type, 'user')
        self.assertEqual(event.target_entity_label, 'standard_user')
        self.assertIn('Deleted user standard_user', event.message)

    def test_delegation_revoke_writes_conflict_resolution_metadata(self):
        owner = get_user_model().objects.create_user(
            username='owner_audit',
            email='owner_audit@example.com',
            password='StrongPass123!',
        )
        delegate = get_user_model().objects.create_user(
            username='delegate_audit',
            email='delegate_audit@example.com',
            password='StrongPass123!',
        )
        team = Team.objects.create(name='Audit Team', level=1)
        site = Site.objects.create(external_id='site-audit-1', name='Audit Site', team=team)
        UserTeamAssignment.objects.create(user=owner, team=team)
        UserTeamAssignment.objects.create(user=delegate, team=team)
        report = MonthlyReport.objects.create(
            site=site,
            reporting_month='2026-07',
            owner_user=owner,
            created_by_user=owner,
            last_modified_by_user=owner,
            last_modified_at=timezone.now(),
        )

        self.client.force_login(owner)
        self.client.post(
            reverse('sitesync:report_delegation_grant', kwargs={'report_id': report.id}),
            {'granted_user_id': str(delegate.id)},
        )
        revoke_response = self.client.post(
            reverse('sitesync:report_delegation_revoke', kwargs={'report_id': report.id}),
            {'granted_user_id': str(delegate.id)},
        )
        self.client.logout()

        self.assertEqual(revoke_response.status_code, 200)
        revoke_event = ReportWriteDelegationEvent.objects.filter(
            report=report,
            delegate_user=delegate,
            action=ReportWriteDelegationEvent.ACTION_REVOKE,
        ).first()
        self.assertIsNotNone(revoke_event)
        self.assertEqual(revoke_event.resolution_basis, ReportWriteDelegationEvent.RESOLUTION_LAST_WRITE_WINS)
