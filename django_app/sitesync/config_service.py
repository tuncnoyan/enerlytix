"""
Configuration loading and persistence helpers.
"""

from django.conf import settings as django_settings
from .models import AppSettings


class SettingsConfigService:
    """Helper for loading and saving runtime configuration."""

    @staticmethod
    def get_default_settings_data():
        return {
            'etainabl_api_url': getattr(django_settings, 'ETAINABL_API_URL', 'https://api.etainabl.com/2.0'),
            'page_size': int(getattr(django_settings, 'PAGE_SIZE', 50)),
            'api_timeout': int(getattr(django_settings, 'API_TIMEOUT', 30)),
        }

    @classmethod
    def get_settings(cls):
        settings_instance = AppSettings.objects.first()
        if settings_instance is not None:
            return settings_instance

        return AppSettings.objects.create(**cls.get_default_settings_data())

    @classmethod
    def update_settings(cls, form):
        settings_instance = form.save(commit=False)
        settings_instance.save()
        return settings_instance
