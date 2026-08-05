from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from sitesync.models import ImportRun, MonthlyConsumption, Site, Supply
from sitesync.services import get_monthly_window


class AdminImportReviewTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username='admin-user',
            password='pass123',
            is_staff=True,
        )
        self.client.force_login(self.admin_user)

        self.site = Site.objects.create(external_id='site-1', name='Alpha Site')
        self.electric_fiscal = Supply.objects.create(
            site=self.site,
            external_id='sup-elec-main',
            name='Electric Fiscal',
            utility_type='electricity',
            status='active',
            parent_account_id='',
        )
        self.electric_sub = Supply.objects.create(
            site=self.site,
            external_id='sup-elec-sub',
            name='Electric Submeter',
            utility_type='electricity',
            status='active',
            parent_account_id='sup-elec-main',
        )
        self.water_fiscal = Supply.objects.create(
            site=self.site,
            external_id='sup-water-main',
            name='Water Fiscal',
            utility_type='water',
            status='active',
            parent_account_id='',
        )

        self.reporting_month = '2026-05'
        self.import_run = ImportRun.objects.create(
            selected_supply_ids=[self.electric_fiscal.external_id],
            reporting_month=self.reporting_month,
            status=ImportRun.STATUS_SUCCESS,
            affected_supply_count=1,
        )
        month_start, month_end = get_monthly_window(self.reporting_month)
        MonthlyConsumption.objects.create(
            import_run=self.import_run,
            supply=self.electric_fiscal,
            canonical_month_key=month_end.strftime('%Y-%m'),
            source_period_start=month_start,
            source_period_end=month_start + timedelta(days=30),
            consumption=Decimal('10.5'),
            breakdown={},
            sources=[],
        )

    def test_import_selection_page_has_new_filters(self):
        response = self.client.get(reverse('sitesync:admin_import_review'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Utility Type', content)
        self.assertIn('Include sub meters', content)
        self.assertIn('Include inactive', content)
        self.assertIn('Load Data', content)

    def test_results_page_has_back_to_data_import(self):
        response = self.client.get(
            reverse('sitesync:admin_import_review_results'),
            {
                'reporting_month': '2026-05',
                'data_type': 'monthly',
                'site_ids': str(self.site.id),
                'supply_ids': self.electric_fiscal.external_id,
            },
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Back to Data Import', content)
        self.assertIn('Export CSV', content)
        self.assertIn('Export XLSX', content)

    def test_import_review_supplies_excludes_submeters_by_default(self):
        response = self.client.get(
            reverse('sitesync:admin_import_review_supplies_api'),
            {'site_ids': str(self.site.id)},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        returned_ids = {item['external_id'] for item in payload['supplies']}
        self.assertIn(self.electric_fiscal.external_id, returned_ids)
        self.assertIn(self.water_fiscal.external_id, returned_ids)
        self.assertNotIn(self.electric_sub.external_id, returned_ids)

    def test_import_review_supplies_includes_submeters_when_enabled(self):
        response = self.client.get(
            reverse('sitesync:admin_import_review_supplies_api'),
            {
                'site_ids': str(self.site.id),
                'include_submeters': '1',
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        returned_ids = {item['external_id'] for item in payload['supplies']}
        self.assertIn(self.electric_sub.external_id, returned_ids)

    def test_import_review_supplies_filters_by_utility_type(self):
        response = self.client.get(
            reverse('sitesync:admin_import_review_supplies_api'),
            {
                'site_ids': str(self.site.id),
                'include_submeters': '1',
                'utility_type': 'water',
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        returned_ids = {item['external_id'] for item in payload['supplies']}
        self.assertEqual(returned_ids, {self.water_fiscal.external_id})

    def test_xlsx_export_handles_timezone_aware_datetimes(self):
        response = self.client.get(
            reverse('sitesync:admin_import_review_export_xlsx'),
            {
                'reporting_month': self.reporting_month,
                'data_type': 'monthly',
                'supply_ids': self.electric_fiscal.external_id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            response['Content-Type'],
        )
        self.assertTrue(response.content.startswith(b'PK'))
