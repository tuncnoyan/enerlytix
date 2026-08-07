from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from sitesync.security import production_security_issues, validate_production_security_posture_or_raise
from sitesync.views import _get_client_ip


class PenTestHardeningRuntimeTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_user(
            username='runtime_admin',
            email='runtime-admin@example.com',
            password='StrongPass123!',
            is_staff=True,
        )
        self.factory = RequestFactory()

    @patch('sitesync.views.EtainaibleSyncService')
    def test_manual_sync_rejects_scheme_relative_redirect_target(self, service_cls):
        self.client.force_login(self.admin_user)
        service_cls.return_value.sync_all.return_value = {
            'sites_created': 0,
            'sites_updated': 0,
            'sites_deleted': 0,
            'supplies_created': 0,
            'supplies_updated': 0,
            'supplies_deleted': 0,
        }

        response = self.client.post(reverse('sitesync:manual_sync'), {'next': '//evil.example/path'})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('//evil.example', response.url)

    @patch('sitesync.views.EtainaibleSyncService')
    def test_manual_sync_failure_response_is_sanitized(self, service_cls):
        self.client.force_login(self.admin_user)
        service_cls.return_value.sync_all.side_effect = RuntimeError('secret stack details')

        response = self.client.post(reverse('sitesync:manual_sync'))
        self.assertEqual(response.status_code, 500)
        self.assertNotIn('details', response.json().get('error', {}))

    @override_settings(TRUSTED_PROXY_CIDRS=['10.0.0.0/8'])
    def test_client_ip_uses_forwarded_header_only_for_trusted_proxy(self):
        trusted_request = self.factory.get(
            '/',
            REMOTE_ADDR='10.1.1.5',
            HTTP_X_FORWARDED_FOR='198.51.100.12, 10.1.1.5',
        )
        untrusted_request = self.factory.get(
            '/',
            REMOTE_ADDR='192.168.50.10',
            HTTP_X_FORWARDED_FOR='198.51.100.99',
        )

        self.assertEqual(_get_client_ip(trusted_request), '198.51.100.12')
        self.assertEqual(_get_client_ip(untrusted_request), '192.168.50.10')

    @override_settings(
        SECRET_KEY='django-insecure-change-me-in-production',
        DEBUG=True,
        SECURE_SSL_REDIRECT=False,
        SESSION_COOKIE_SECURE=False,
        CSRF_COOKIE_SECURE=False,
        SECURE_HSTS_SECONDS=0,
    )
    def test_production_security_issues_detect_missing_controls(self):
        issues = production_security_issues()
        self.assertGreaterEqual(len(issues), 4)

    @override_settings(
        SECRET_KEY='django-insecure-change-me-in-production',
        DEBUG=True,
        SECURE_SSL_REDIRECT=False,
        SESSION_COOKIE_SECURE=False,
        CSRF_COOKIE_SECURE=False,
        SECURE_HSTS_SECONDS=0,
    )
    def test_production_security_validator_raises_on_missing_controls(self):
        with self.assertRaises(RuntimeError):
            validate_production_security_posture_or_raise()

    @override_settings(
        SECRET_KEY='not-default-but-strong-secret-value-1234567890',
        DEBUG=False,
        SECURE_SSL_REDIRECT=True,
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True,
        SECURE_HSTS_SECONDS=31536000,
    )
    def test_production_security_issues_empty_for_compliant_controls(self):
        self.assertEqual([], production_security_issues())

    @override_settings(
        SECRET_KEY='not-default-but-strong-secret-value-1234567890',
        DEBUG=False,
        SECURE_SSL_REDIRECT=True,
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True,
        SECURE_HSTS_SECONDS=31536000,
    )
    def test_production_security_validator_passes_for_compliant_controls(self):
        validate_production_security_posture_or_raise()
