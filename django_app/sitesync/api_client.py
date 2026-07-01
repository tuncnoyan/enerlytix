"""
Simple Etainabl API client wrapper.
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class EtainablApiClient:
    def __init__(self, api_key=None, base_url=None, timeout=None):
        self.api_key = (api_key or settings.ETAINABL_API_KEY or '').strip()
        self.base_url = base_url or settings.ETAINABL_API_URL
        self.timeout = timeout or settings.API_TIMEOUT

    def _headers(self):
        return {
            'x-api-key': self.api_key,
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def get(self, path, params=None):
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        logger.debug(f"GET {url} params={params}")
        resp = requests.get(url, params=params, headers=self._headers(), timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_consumption(self, account_id, start_date, end_date, granularity, source=None):
        params = {
            'accountId': account_id,
            'startDate': start_date,
            'endDate': end_date,
            'granularity': granularity,
        }
        if source:
            params['source'] = source
        return self.get('/consumption', params=params)

    def get_invoices(self, account_id, start_date=None, end_date=None, limit=100):
        skip = 0
        all_rows = []
        while True:
            params = {
                'accountId': account_id,
                'limit': limit,
                'skip': skip,
            }
            if start_date:
                params['startDate'] = start_date
            if end_date:
                params['endDate'] = end_date

            payload = self.get('/invoices', params=params)
            rows = payload.get('data') or payload.get('results') or payload.get('items') or []
            if not isinstance(rows, list):
                rows = []

            all_rows.extend(rows)
            total = payload.get('total') if isinstance(payload, dict) else None
            if not rows:
                break
            if isinstance(total, int) and len(all_rows) >= total:
                break
            if len(rows) < limit:
                break
            skip += limit

        return all_rows
