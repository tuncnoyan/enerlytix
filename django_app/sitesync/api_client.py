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

    def _headers_key_only(self):
        return {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }

    def get(self, path, params=None):
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        logger.debug(f"GET {url} params={params}")
        resp = requests.get(url, params=params, headers=self._headers(), timeout=self.timeout)
        if resp.status_code >= 400:
            body = (resp.text or '').lower()
            if resp.status_code >= 500 and ('unauthorized' in body or 'internal server error' in body):
                logger.debug("Retrying GET %s with x-api-key only headers", url)
                resp = requests.get(url, params=params, headers=self._headers_key_only(), timeout=self.timeout)
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

    def get_invoices(self, account_id, limit=100, start_page=1):
        """Fetch all invoices for an account using page-based pagination.

        The `/invoices` endpoint's `skip` parameter does not reliably advance
        through results (it silently truncated invoice history to the first
        page). `page`/`limit` params paginate correctly instead, so all
        invoice history is downloaded starting from `start_page` using
        `limit` records per page, with no server-side date filtering.
        """
        limit = max(1, int(limit or 100))
        page = max(1, int(start_page or 1))
        all_rows = []

        while True:
            params = {
                'accountId': account_id,
                'limit': limit,
                'page': page,
            }

            payload = self.get('/invoices', params=params)
            rows = payload.get('data') or payload.get('results') or payload.get('items') or []
            if not isinstance(rows, list):
                rows = []

            if not rows:
                break

            all_rows.extend(rows)

            total = payload.get('total') if isinstance(payload, dict) else None
            if isinstance(total, int):
                reported_limit = payload.get('limit') if isinstance(payload, dict) else None
                limit_used = reported_limit if isinstance(reported_limit, int) else len(rows)
                offset = (page - 1) * limit
                if offset + limit_used >= total:
                    break

            # Safety: if total is unknown or inconsistent, stop when a page
            # returns fewer rows than requested (final page reached).
            if len(rows) < limit:
                break

            page += 1

        return all_rows
