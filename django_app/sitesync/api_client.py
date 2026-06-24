"""
Simple Etainabl API client wrapper.
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class EtainablApiClient:
    def __init__(self, api_key=None, base_url=None, timeout=None):
        self.api_key = api_key or settings.ETAINABL_API_KEY
        self.base_url = base_url or settings.ETAINABL_API_URL
        self.timeout = timeout or settings.API_TIMEOUT

    def _headers(self):
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def get(self, path, params=None):
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        logger.debug(f"GET {url} params={params}")
        resp = requests.get(url, params=params, headers=self._headers(), timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()
