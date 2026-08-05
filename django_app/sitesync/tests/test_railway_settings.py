import importlib
import os
from unittest.mock import patch

import django
from django.test import SimpleTestCase

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


class RailwaySettingsTests(SimpleTestCase):
    def test_railway_env_configures_security_and_static_settings(self):
        with patch.dict(
            os.environ,
            {
                "DJANGO_SETTINGS_MODULE": "config.settings",
                "DEBUG": "False",
                "SECRET_KEY": "railway-test-secret",
                "ALLOWED_HOSTS": "localhost",
                "RAILWAY_PUBLIC_DOMAIN": "enerlytix.up.railway.app",
                "PORT": "8080",
                "DATABASE_URL": "",
            },
            clear=False,
        ):
            import config.settings as settings_module

            settings_module = importlib.reload(settings_module)

            self.assertIn("enerlytix.up.railway.app", settings_module.ALLOWED_HOSTS)
            self.assertEqual(settings_module.PORT, 8080)
            self.assertIn("https://enerlytix.up.railway.app", settings_module.CSRF_TRUSTED_ORIGINS)
            self.assertIn("whitenoise.middleware.WhiteNoiseMiddleware", settings_module.MIDDLEWARE)
            self.assertEqual(settings_module.SECURE_PROXY_SSL_HEADER, ("HTTP_X_FORWARDED_PROTO", "https"))
