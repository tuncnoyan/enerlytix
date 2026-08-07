from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from sitesync.models import ImportRun, RoleAssignment, Site, Supply


class PenTestHardeningAccessTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_user(
            username='security_admin',
            email='admin@example.com',
            password='StrongPass123!',
            is_staff=True,
        )
        self.standard_user = user_model.objects.create_user(
            username='security_user',
            email='user@example.com',
            password='StrongPass123!',
        )
        RoleAssignment.objects.create(user=self.standard_user, role_name=RoleAssignment.ROLE_USER)

        self.site = Site.objects.create(external_id='site-pen-test', name='Pen Test Site')
        self.supply = Supply.objects.create(
            site=self.site,
            external_id='supply-pen-test',
            name='Pen Test Supply',
            utility_type='electricity',
            parent_account_id='',
        )
        self.import_run = ImportRun.objects.create(
            selected_supply_ids=[self.supply.external_id],
            reporting_month='2026-07',
            status=ImportRun.STATUS_SUCCESS,
            affected_supply_count=1,
        )

    def test_consumption_import_requires_authentication(self):
        response = self.client.post(
            reverse('sitesync:consumption_import'),
            {'supply_ids': [self.supply.external_id], 'reporting_month': '2026-07'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)

    def test_consumption_import_requires_admin(self):
        self.client.force_login(self.standard_user)
        response = self.client.post(
            reverse('sitesync:consumption_import'),
            {'supply_ids': [self.supply.external_id], 'reporting_month': '2026-07'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

    @patch('sitesync.views.ConsumptionImportService')
    def test_consumption_import_admin_success(self, service_cls):
        self.client.force_login(self.admin_user)
        service = service_cls.return_value
        service.run.return_value = SimpleNamespace(
            id='run-1',
            status='success',
            affected_supply_count=1,
            started_at=None,
            completed_at=None,
            records_imported=10,
            records_failed=0,
            retry_count=0,
            error_details={},
            outcome_details=[],
        )

        response = self.client.post(
            reverse('sitesync:consumption_import'),
            {'supply_ids': [self.supply.external_id], 'reporting_month': '2026-07'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)

    def test_consumption_display_requires_authentication(self):
        response = self.client.get(reverse('sitesync:consumption_display_api'), {'reporting_month': '2026-07'})
        self.assertEqual(response.status_code, 401)

    def test_consumption_display_allows_authenticated_user(self):
        self.client.force_login(self.standard_user)
        response = self.client.get(reverse('sitesync:consumption_display_api'), {'reporting_month': '2026-07'})
        self.assertEqual(response.status_code, 200)

    def test_report_data_requires_authentication(self):
        response = self.client.get(reverse('sitesync:report_data_api'), {'site_id': self.site.id, 'end_month': '2026-07'})
        self.assertEqual(response.status_code, 401)

    def test_report_data_allows_authenticated_user(self):
        self.client.force_login(self.standard_user)
        response = self.client.get(reverse('sitesync:report_data_api'), {'site_id': self.site.id, 'end_month': '2026-07'})
        self.assertEqual(response.status_code, 200)

    def test_import_run_detail_requires_authentication(self):
        response = self.client.get(reverse('sitesync:import_run_detail', kwargs={'import_run_id': self.import_run.id}))
        self.assertEqual(response.status_code, 401)

    def test_import_run_detail_allows_authenticated_user(self):
        self.client.force_login(self.standard_user)
        response = self.client.get(reverse('sitesync:import_run_detail', kwargs={'import_run_id': self.import_run.id}))
        self.assertEqual(response.status_code, 200)

    def test_manual_sync_requires_authentication(self):
        response = self.client.post(reverse('sitesync:manual_sync'))
        self.assertEqual(response.status_code, 401)

    def test_manual_sync_requires_admin(self):
        self.client.force_login(self.standard_user)
        response = self.client.post(reverse('sitesync:manual_sync'))
        self.assertEqual(response.status_code, 403)

    @patch('sitesync.views.EtainaibleSyncService')
    def test_manual_sync_allows_admin(self, service_cls):
        self.client.force_login(self.admin_user)
        service_cls.return_value.sync_all.return_value = {
            'sites_created': 0,
            'sites_updated': 0,
            'sites_deleted': 0,
            'supplies_created': 0,
            'supplies_updated': 0,
            'supplies_deleted': 0,
        }
        response = self.client.post(reverse('sitesync:manual_sync'))
        self.assertEqual(response.status_code, 302)

    def test_settings_post_requires_authentication(self):
        response = self.client.post(reverse('sitesync:settings_panel'), {'page_size': 50})
        self.assertEqual(response.status_code, 401)

    def test_settings_post_requires_admin(self):
        self.client.force_login(self.standard_user)
        response = self.client.post(reverse('sitesync:settings_panel'), {'page_size': 50})
        self.assertEqual(response.status_code, 403)

    def test_capacity_results_export_requires_authentication(self):
        response = self.client.get(reverse('sitesync:capacity_upload_results_export'))
        self.assertEqual(response.status_code, 401)

    def test_capacity_results_export_requires_admin(self):
        self.client.force_login(self.standard_user)
        response = self.client.get(reverse('sitesync:capacity_upload_results_export'))
        self.assertEqual(response.status_code, 403)
