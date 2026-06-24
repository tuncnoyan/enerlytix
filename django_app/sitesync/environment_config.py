"""
Environment configuration loader and validator for the sitesync app.
"""
import os
from django.conf import settings


def load_env_config():
    """Load configuration values from environment and return as dict."""
    return {
        'ETAINABL_API_KEY': os.getenv('ETAINABL_API_KEY') or getattr(settings, 'ETAINABL_API_KEY', None),
        'ETAINABL_API_URL': os.getenv('ETAINABL_API_URL') or getattr(settings, 'ETAINABL_API_URL', None),
        'API_TIMEOUT': int(os.getenv('API_TIMEOUT', getattr(settings, 'API_TIMEOUT', 30))) ,
        'PAGE_SIZE': int(os.getenv('PAGE_SIZE', getattr(settings, 'REST_FRAMEWORK', {}).get('PAGE_SIZE', 50)))
    }


def validate_env_config(raise_on_missing: bool = True) -> dict:
    """Validate required environment configuration.

    If `raise_on_missing` is True, raise ValueError for missing required keys.
    Returns the loaded config dict.
    """
    cfg = load_env_config()
    missing = []
    if not cfg.get('ETAINABL_API_KEY'):
        missing.append('ETAINABL_API_KEY')
    if not cfg.get('ETAINABL_API_URL'):
        missing.append('ETAINABL_API_URL')

    # During Django test runs, it's acceptable for keys to be mocked by overrides
    is_testing = 'test' in os.sys.argv

    if missing and raise_on_missing and not is_testing:
        raise ValueError(f"Missing required environment configuration: {', '.join(missing)}")

    return cfg
