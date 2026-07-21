"""Integration checks for report cover export payload compatibility."""

from django.test import Client, TestCase
from django.urls import reverse

from sitesync.models import Site


class ReportCoverExportContractTest(TestCase):
    """Verify export-oriented cover defaults are present in report payload."""

    def setUp(self):
        self.client = Client()
        self.site = Site.objects.create(
            external_id='cover-export-site',
            name='4 Lakeside Business Park',
            description='Integration test site',
        )

    def test_report_data_payload_contains_cover_sequence_for_pdf_and_pptx(self):
        response = self.client.get(
            reverse('sitesync:report_data_api'),
            {'site_id': self.site.id, 'end_month': '2026-06'},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertIn('cover_defaults', payload)
        self.assertEqual(
            payload['cover_defaults']['sequence'],
            ['front_cover_1', 'front_cover_2', 'body_pages', 'back_cover'],
        )
