"""Tests for report cover page defaults and payload structure."""

import re

from django.test import Client, TestCase
from django.urls import reverse

from sitesync.models import Site, Supply


class ReportCoverPagesTest(TestCase):
    """Validate report cover defaults and sequence contracts."""

    def setUp(self):
        self.client = Client()
        self.site = Site.objects.create(
            external_id='cover-site-1',
            name='Unit 4, Lakeside Business Park',
            description='Cover defaults test site',
        )
        Supply.objects.create(
            site=self.site,
            external_id='supply-cover-elec',
            name='Electricity Main',
            utility_type='electricity',
            device_id='EM-001',
        )

    def test_report_data_includes_cover_defaults(self):
        response = self.client.get(
            reverse('sitesync:report_data_api'),
            {'site_id': self.site.id, 'end_month': '2026-06'},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('cover_defaults', payload)
        cover_defaults = payload['cover_defaults']

        self.assertEqual(
            cover_defaults['sequence'],
            ['front_cover_1', 'front_cover_2', 'body_pages', 'back_cover'],
        )
        self.assertEqual(
            cover_defaults['front_cover_1']['site_title'],
            'Unit 4, Lakeside Business Park',
        )
        self.assertEqual(
            cover_defaults['front_cover_1']['report_month_title'],
            'June 2026 Energy Report',
        )
        self.assertRegex(
            cover_defaults['front_cover_1']['report_date'],
            r'^\d{2}\s+[A-Za-z]+\s+\d{4}$',
        )
        self.assertEqual(
            cover_defaults['back_cover']['image_asset'],
            '/static/sitesync/images/Report%20Back%20Cover%20Page.jpg',
        )

    def test_scope_body_uses_canonical_text_with_site_substitution(self):
        response = self.client.get(
            reverse('sitesync:report_data_api'),
            {'site_id': self.site.id, 'end_month': '2026-06'},
        )

        self.assertEqual(response.status_code, 200)
        scope_body = response.json()['cover_defaults']['front_cover_2']['scope_body']
        self.assertIn('Unit 4, Lakeside Business Park', scope_body)
        self.assertIn('monthly invoice data', scope_body)
        self.assertIn('half-hourly electricity profiles', scope_body)

    def test_contents_entries_start_with_total_utility_usage_without_meter_suffix(self):
        response = self.client.get(
            reverse('sitesync:report_data_api'),
            {'site_id': self.site.id, 'end_month': '2026-06'},
        )

        self.assertEqual(response.status_code, 200)
        entries = response.json()['cover_defaults']['front_cover_2']['contents_entries']
        self.assertGreaterEqual(len(entries), 2)

        first_line = entries[0]['display_line']
        self.assertEqual(first_line, 'Total Utility Usage (£)')

        other_lines = [item['display_line'] for item in entries[1:]]
        self.assertTrue(any(line.strip() for line in other_lines))

    def test_report_view_context_exposes_cover_defaults(self):
        response = self.client.get(
            reverse('sitesync:report'),
            {'site_id': self.site.id, 'end_month': '2026-06'},
        )

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('"coverDefaults"', content)
        self.assertIn('"report_month_title": "June 2026 Energy Report"', content)
