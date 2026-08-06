"""
Integration tests for the settings page.
"""

from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.urls import reverse
from openpyxl import Workbook

from sitesync.models import AppSettings, CapacityUploadRun
from sitesync.views import settings_panel_view


class SettingsViewIntegrationTest(TestCase):
    """Integration tests for the settings panel view."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(username='settingsuser', password='pass123')
        self.admin_user = get_user_model().objects.create_user(
            username='settingsadmin',
            password='pass123',
            is_staff=True,
        )
        self.settings = AppSettings.objects.create(
            etainabl_api_url='https://api.etainabl.com/2.0',
            page_size=50,
            api_timeout=30,
            electricity_benchmark_intensity=90.5,
            gas_benchmark_intensity=60.25,
            water_benchmark_intensity=1.75,
            invoice_page_limit=100,
            invoice_start_page=1,
        )

    def _build_workbook_bytes(self, rows):
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.append(['Name', 'eSight Meter Code', 'Av Cap (kVA)'])
        for row in rows:
            worksheet.append(row)

        buffer = BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    def _auth_get(self, path='/settings/', data=None):
        request = self.factory.get(path, data or {})
        request.user = self.user
        return request

    def _auth_post(self, path='/settings/', data=None):
        request = self.factory.post(path, data=data or {})
        request.user = self.user
        return request

    def test_settings_page_renders_current_values(self):
        request = self._auth_get('/settings/')
        response = settings_panel_view(request)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Settings', content)
        self.assertIn('https://api.etainabl.com/2.0', content)
        self.assertIn('50', content)
        self.assertIn('30', content)
        self.assertIn('90.5', content)
        self.assertIn('60.25', content)
        self.assertIn('1.75', content)
        self.assertIn('Invoice Data Page Limit', content)
        self.assertIn('Invoice Data Start Page Number', content)

    def test_settings_page_persists_valid_post(self):
        request = self._auth_post('/settings/', data={
            'electricity_benchmark_intensity': 95.5,
            'gas_benchmark_intensity': 63.75,
            'water_benchmark_intensity': 2.05,
            'etainabl_api_url': 'https://api.updated.example.com/2.0',
            'page_size': 75,
            'api_timeout': 45,
            'invoice_page_limit': 200,
            'invoice_start_page': 2,
        })
        response = settings_panel_view(request)

        self.assertEqual(response.status_code, 200)
        self.settings.refresh_from_db()
        self.assertEqual(self.settings.etainabl_api_url, 'https://api.updated.example.com/2.0')
        self.assertEqual(self.settings.page_size, 75)
        self.assertEqual(self.settings.api_timeout, 45)
        self.assertEqual(float(self.settings.electricity_benchmark_intensity), 95.5)
        self.assertEqual(float(self.settings.gas_benchmark_intensity), 63.75)
        self.assertEqual(float(self.settings.water_benchmark_intensity), 2.05)
        self.assertEqual(self.settings.invoice_page_limit, 200)
        self.assertEqual(self.settings.invoice_start_page, 2)

    def test_settings_page_rejects_invalid_post(self):
        request = self._auth_post('/settings/', data={
            'electricity_benchmark_intensity': -1,
            'gas_benchmark_intensity': -2,
            'water_benchmark_intensity': -3,
            'etainabl_api_url': 'not-a-url',
            'page_size': -1,
            'api_timeout': 0,
            'invoice_page_limit': 100,
            'invoice_start_page': 1,
        })
        response = settings_panel_view(request)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Enter a valid URL', content)
        self.assertIn('Electricity benchmark intensity must be zero or greater.', content)
        self.assertIn('Gas benchmark intensity must be zero or greater.', content)
        self.assertIn('Water benchmark intensity must be zero or greater.', content)

    def test_settings_page_shows_capacity_upload_validation_messages(self):
        payload = self._build_workbook_bytes([
            ['Meter A', 'MTR-001', -5],
        ])
        upload = SimpleUploadedFile(
            'capacity.xlsx',
            payload,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        request = self._auth_post(
            reverse('sitesync:settings_panel'),
            data={
                'capacity_upload_submit': '1',
                'capacity_upload_file': upload,
            },
        )
        response = settings_panel_view(request)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Capacity upload failed. No valid rows were imported.', content)
        self.assertNotIn('upload-errors', content)

    def test_settings_page_does_not_render_inline_upload_error_list(self):
        payload = self._build_workbook_bytes([
            ['Meter A', 'MTR-001', -5],
            ['', '', 'not-a-number'],
        ])
        upload = SimpleUploadedFile(
            'capacity-errors.xlsx',
            payload,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        request = self._auth_post(
            reverse('sitesync:settings_panel'),
            data={
                'capacity_upload_submit': '1',
                'capacity_upload_file': upload,
            },
        )
        response = settings_panel_view(request)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Capacity upload failed. No valid rows were imported.', content)
        self.assertNotIn('upload-errors', content)

    def test_settings_page_keeps_summary_and_download_action_for_admin(self):
        run = CapacityUploadRun.objects.create(
            uploaded_filename='capacity-latest.xlsx',
            total_rows=2,
            accepted_rows=1,
            rejected_rows=1,
            status=CapacityUploadRun.STATUS_PARTIAL_SUCCESS,
            error_summary=['Row 3: Sample error'],
        )
        run.row_results.create(
            source_row_number=2,
            outcome='success',
            explanation='',
            original_columns={
                'Name': 'Meter A',
                'eSight Meter Code': 'MTR-001',
                'Av Cap (kVA)': 20,
            },
        )

        request = self.factory.get(reverse('sitesync:settings_panel'))
        request.user = self.admin_user
        response = settings_panel_view(request)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Capacity upload completed with warnings.', content)
        self.assertIn('Latest file:', content)
        self.assertIn('capacity-latest.xlsx', content)
        self.assertIn('Download Upload Results (.xlsx)', content)

    def test_settings_page_shows_latest_upload_filename_summary(self):
        payload = self._build_workbook_bytes([
            ['Meter A', 'MTR-005', 10],
        ])
        upload = SimpleUploadedFile(
            'capacity-latest.xlsx',
            payload,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        request = self._auth_post(
            reverse('sitesync:settings_panel'),
            data={
                'capacity_upload_submit': '1',
                'capacity_upload_file': upload,
            },
        )
        response = settings_panel_view(request)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Latest file:', content)
        self.assertIn('capacity-latest.xlsx', content)
