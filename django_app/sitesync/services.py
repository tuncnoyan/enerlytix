"""
Etainabl API sync service for fetching and persisting site and supply data.
"""

import logging
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone as dj_timezone

from .api_client import EtainablApiClient
from .models import (
    Site,
    Supply,
    AppSettings,
    ImportRun,
    HalfHourlyConsumption,
    MonthlyConsumption,
    InvoiceCost,
)

logger = logging.getLogger(__name__)


class EtainaibleSyncService:
    """Service to sync assets and accounts from Etainabl API."""
    
    def __init__(self):
        """Initialize the sync service with API configuration."""
        self.api_key = (settings.ETAINABL_API_KEY or '').strip()
        self.api_url = settings.ETAINABL_API_URL
        self.timeout = settings.API_TIMEOUT
        self.max_retries = 10
        self.base_backoff = 1  # Start with 1 second
        self.max_backoff = 120  # Cap at 120 seconds
        
        if not self.api_key:
            raise ValueError(
                "ETAINABL_API_KEY environment variable not set. "
                "Cannot initialize sync service."
            )
    
    def sync_all(self) -> Dict[str, int]:
        """
        Perform complete sync of assets and accounts.
        
        Returns:
            Dict with counts: {
                'sites_created': int,
                'sites_updated': int,
                'supplies_created': int,
                'supplies_updated': int,
            }
        """
        logger.info("Starting full sync of Etainabl data...")
        
        results = {
            'sites_created': 0,
            'sites_updated': 0,
            'supplies_created': 0,
            'supplies_updated': 0,
        }
        
        try:
            # Sync assets (sites)
            sites_result = self.sync_assets()
            results['sites_created'] = sites_result.get('created', 0)
            results['sites_updated'] = sites_result.get('updated', 0)
            logger.info(
                f"Assets sync complete: {results['sites_created']} created, "
                f"{results['sites_updated']} updated"
            )
            
            # Sync accounts (supplies)
            supplies_result = self.sync_accounts()
            results['supplies_created'] = supplies_result.get('created', 0)
            results['supplies_updated'] = supplies_result.get('updated', 0)
            logger.info(
                f"Accounts sync complete: {results['supplies_created']} created, "
                f"{results['supplies_updated']} updated"
            )
            
            logger.info(f"Full sync completed successfully: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Sync failed with error: {str(e)}", exc_info=True)
            raise
    
    def sync_assets(self) -> Dict[str, int]:
        """
        Sync all assets (sites) from Etainabl.
        
        Returns:
            Dict with created and updated counts
        """
        logger.info("Starting asset sync...")
        created = 0
        updated = 0
        skipped = 0
        
        try:
            endpoint = f"{self.api_url}/assets"
            page_size = 50
            page = 1
            
            while True:
                # Fetch paginated results
                params = {
                    'limit': page_size,
                    'page': page,
                }
                
                data = self._fetch_from_api(endpoint, params)
                
                assets = self._extract_data_items(data)
                if assets is None:
                    logger.warning(f"No data in response from {endpoint}")
                    break

                if not assets:
                    logger.info(f"No more assets to fetch (page={page})")
                    break
                
                # Process each asset
                for asset in assets:
                    site_created = self._upsert_site(asset)
                    if site_created is True:
                        created += 1
                    elif site_created is False:
                        updated += 1
                    else:
                        skipped += 1
                
                # Check pagination
                total = data.get('total') if isinstance(data, dict) else None
                if total is not None:
                    reported_skip = data.get('skip') if isinstance(data, dict) else None
                    reported_limit = data.get('limit') if isinstance(data, dict) else None
                    offset = reported_skip if isinstance(reported_skip, int) else (page - 1) * page_size
                    limit_used = reported_limit if isinstance(reported_limit, int) else len(assets)
                    downloaded = offset + limit_used
                    if downloaded >= total:
                        logger.info(f"Reached end of assets (total={total})")
                        break

                if len(assets) < page_size:
                    logger.info("Reached final assets page by page size (page=%s)", page)
                    break

                page += 1
            
            logger.info(
                "Asset sync complete: %s created, %s updated, %s skipped",
                created,
                updated,
                skipped,
            )
            return {'created': created, 'updated': updated, 'skipped': skipped}
            
        except Exception as e:
            logger.error(f"Asset sync failed: {str(e)}", exc_info=True)
            raise
    
    def sync_accounts(self) -> Dict[str, int]:
        """
        Sync all accounts (supplies) from Etainabl.
        
        Returns:
            Dict with created and updated counts
        """
        logger.info("Starting account sync...")
        created = 0
        updated = 0
        skipped = 0
        
        try:
            endpoint = f"{self.api_url}/accounts"
            page_size = 50
            page = 1
            
            while True:
                # Fetch paginated results
                params = {
                    'limit': page_size,
                    'page': page,
                }
                
                data = self._fetch_from_api(endpoint, params)
                
                accounts = self._extract_data_items(data)
                if accounts is None:
                    logger.warning(f"No data in response from {endpoint}")
                    break

                if not accounts:
                    logger.info(f"No more accounts to fetch (page={page})")
                    break
                
                # Process each account
                for account in accounts:
                    supply_created = self._upsert_supply(account)
                    if supply_created is True:
                        created += 1
                    elif supply_created is False:
                        updated += 1
                    else:
                        skipped += 1
                
                # Check pagination
                total = data.get('total') if isinstance(data, dict) else None
                if total is not None:
                    reported_skip = data.get('skip') if isinstance(data, dict) else None
                    reported_limit = data.get('limit') if isinstance(data, dict) else None
                    offset = reported_skip if isinstance(reported_skip, int) else (page - 1) * page_size
                    limit_used = reported_limit if isinstance(reported_limit, int) else len(accounts)
                    downloaded = offset + limit_used
                    if downloaded >= total:
                        logger.info(f"Reached end of accounts (total={total})")
                        break

                if len(accounts) < page_size:
                    logger.info("Reached final accounts page by page size (page=%s)", page)
                    break

                page += 1
            
            logger.info(
                "Account sync complete: %s created, %s updated, %s skipped",
                created,
                updated,
                skipped,
            )
            return {'created': created, 'updated': updated, 'skipped': skipped}
            
        except Exception as e:
            logger.error(f"Account sync failed: {str(e)}", exc_info=True)
            raise
    
    def _fetch_from_api(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Fetch data from Etainabl API with retry logic.
        
        Args:
            endpoint: API endpoint URL
            params: Query parameters
        
        Returns:
            JSON response data
        
        Raises:
            Exception if all retries are exhausted
        """
        headers = {
            'x-api-key': self.api_key,
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(
                    f"API request to {endpoint} (attempt {attempt}/{self.max_retries})"
                )
                
                response = requests.get(
                    endpoint,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )
                
                # Check for permanent errors
                if response.status_code in [400, 401, 403, 404]:
                    logger.error(
                        f"Permanent API error {response.status_code}: {response.text}"
                    )
                    raise Exception(
                        f"API returned {response.status_code}: {response.text}"
                    )
                
                # Retry on transient errors
                if response.status_code >= 500 or response.status_code == 408:
                    if attempt < self.max_retries:
                        backoff = min(
                            self.base_backoff * (2 ** (attempt - 1)),
                            self.max_backoff
                        )
                        logger.warning(
                            f"Transient API error {response.status_code}, "
                            f"retrying in {backoff}s..."
                        )
                        time.sleep(backoff)
                        continue
                    else:
                        raise Exception(
                            f"API returned {response.status_code} after "
                            f"{self.max_retries} retries"
                        )
                
                # Success
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                if attempt < self.max_retries:
                    backoff = min(
                        self.base_backoff * (2 ** (attempt - 1)),
                        self.max_backoff
                    )
                    logger.warning(f"Timeout, retrying in {backoff}s...")
                    time.sleep(backoff)
                    continue
                else:
                    logger.error(f"Timeout after {self.max_retries} retries")
                    raise
            
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    backoff = min(
                        self.base_backoff * (2 ** (attempt - 1)),
                        self.max_backoff
                    )
                    logger.warning(f"Request error: {str(e)}, retrying in {backoff}s...")
                    time.sleep(backoff)
                    continue
                else:
                    logger.error(f"Request failed after {self.max_retries} retries: {str(e)}")
                    raise
        
        raise Exception(f"Failed to fetch from {endpoint} after {self.max_retries} attempts")

    def _extract_data_items(self, payload: object) -> Optional[List[Dict]]:
        """Extract list-like data from known Etainabl response shapes."""
        if payload is None:
            return None
        if isinstance(payload, list):
            return payload
        if not isinstance(payload, dict):
            return None

        for key in ('data', 'results', 'items'):
            value = payload.get(key)
            if isinstance(value, list):
                return value

        return None
    
    def _upsert_site(self, asset_data: Dict) -> Optional[bool]:
        """
        Create or update a Site from asset data.
        
        Args:
            asset_data: Asset data from Etainabl API
        
        Returns:
            True if created, False if updated
        """
        try:
            external_id = (
                asset_data.get('id')
                or asset_data.get('_id')
                or asset_data.get('assetId')
            )
            if not external_id:
                logger.warning(f"Asset missing id field: {asset_data}")
                return None

            name_value = (
                asset_data.get('name')
                or asset_data.get('siteName')
                or asset_data.get('siteCode')
                or asset_data.get('label')
            )
            if isinstance(name_value, dict):
                name_value = (
                    name_value.get('name')
                    or name_value.get('value')
                    or name_value.get('label')
                )

            description_value = asset_data.get('description')
            if not description_value:
                address_data = asset_data.get('address')
                if isinstance(address_data, dict):
                    address_parts = [
                        address_data.get('streetAddress'),
                        address_data.get('locality'),
                        address_data.get('region'),
                        address_data.get('postCode'),
                    ]
                    description_value = ", ".join(
                        str(part).strip() for part in address_parts if part
                    )
                elif address_data:
                    description_value = str(address_data)

            if isinstance(description_value, dict):
                description_value = str(description_value)
            
            site, created = Site.objects.update_or_create(
                external_id=external_id,
                defaults={
                    'name': str(name_value or 'Unknown'),
                    'description': str(description_value or ''),
                }
            )
            
            if created:
                logger.debug(f"Created site: {site.name} (id={external_id})")
            else:
                logger.debug(f"Updated site: {site.name} (id={external_id})")
            
            return created
            
        except Exception as e:
            logger.error(f"Failed to upsert site from {asset_data}: {str(e)}")
            return None
    
    def _upsert_supply(self, account_data: Dict) -> Optional[bool]:
        """
        Create or update a Supply from account data.
        
        Args:
            account_data: Account data from Etainabl API
        
        Returns:
            True if created, False if updated
        """
        try:
            external_id = account_data.get('id') or account_data.get('_id')
            site_external_id = (
                account_data.get('asset_id')
                or account_data.get('assetId')
                or account_data.get('asset')
            )
            parent_account_id = (
                account_data.get('parentAccountId')
                or account_data.get('parent_account_id')
                or account_data.get('parentAccount')
            )
            if isinstance(site_external_id, dict):
                site_external_id = (
                    site_external_id.get('id')
                    or site_external_id.get('_id')
                    or site_external_id.get('assetId')
                )
            if isinstance(parent_account_id, dict):
                parent_account_id = (
                    parent_account_id.get('id')
                    or parent_account_id.get('_id')
                    or parent_account_id.get('accountId')
                )
            
            if not external_id or not site_external_id:
                logger.warning(f"Account missing id or asset_id: {account_data}")
                return None
            
            # Find associated site
            try:
                site = Site.objects.get(external_id=site_external_id)
            except Site.DoesNotExist:
                logger.warning(
                    f"Site not found for account {external_id} "
                    f"(site_id={site_external_id})"
                )
                return None
            
            # Map utility type
            utility_type_map = {
                'electricity': 'electricity',
                'electric': 'electricity',
                'gas': 'gas',
                'water': 'water',
                'thermal': 'other',
            }
            utility_raw = str(account_data.get('type', account_data.get('utility_type', 'other'))).lower()
            utility_type = utility_type_map.get(utility_raw, 'other')

            device_id = account_data.get('device_id') or account_data.get('deviceId') or ''
            if not device_id:
                third_parties = account_data.get('thirdParties') or []
                if isinstance(third_parties, list) and third_parties:
                    first_tp = third_parties[0]
                    if isinstance(first_tp, dict):
                        device_id = first_tp.get('deviceId') or ''
            
            supply, created = Supply.objects.update_or_create(
                external_id=external_id,
                defaults={
                    'site': site,
                    'name': str(account_data.get('name') or account_data.get('label') or 'Unknown'),
                    'utility_type': utility_type,
                    'device_id': device_id,
                    'parent_account_id': str(parent_account_id) if parent_account_id else None,
                }
            )
            
            if created:
                logger.debug(f"Created supply: {supply.name} (id={external_id})")
            else:
                logger.debug(f"Updated supply: {supply.name} (id={external_id})")
            
            return created
            
        except Exception as e:
            logger.error(f"Failed to upsert supply from {account_data}: {str(e)}")
            return None


def parse_utc_datetime(value: str) -> datetime:
    """Parse ISO datetime/date values from source and return UTC-aware datetime."""
    if not value:
        raise ValueError('Missing datetime value')

    normalized = value.replace('Z', '+00:00')
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def canonical_month_key(value: datetime) -> str:
    """Derive canonical month key from UTC datetime."""
    return value.astimezone(timezone.utc).strftime('%Y-%m')


def month_start(year: int, month: int) -> datetime:
    return datetime(year, month, 1, tzinfo=timezone.utc)


def shift_months(start: datetime, months: int) -> datetime:
    total = start.year * 12 + (start.month - 1) + months
    year = total // 12
    month = (total % 12) + 1
    return datetime(year, month, 1, tzinfo=timezone.utc)


def reporting_month_bounds(reporting_month: str) -> Tuple[datetime, datetime]:
    year, month = reporting_month.split('-')
    start = month_start(int(year), int(month))
    end = shift_months(start, 1)
    return start, end


def get_halfhourly_windows(reporting_month: str) -> List[Tuple[datetime, datetime]]:
    start, end = reporting_month_bounds(reporting_month)
    prior_start = shift_months(start, -12)
    prior_end = shift_months(end, -12)
    return [(start, end), (prior_start, prior_end)]


def get_monthly_window(reporting_month: str) -> Tuple[datetime, datetime]:
    start, end = reporting_month_bounds(reporting_month)
    return shift_months(end, -settings.CONSUMPTION_MONTHLY_MONTHS), end


def get_invoice_window(reporting_month: str) -> Tuple[datetime, datetime]:
    start, end = reporting_month_bounds(reporting_month)
    return shift_months(end, -settings.CONSUMPTION_INVOICE_MONTHS), end


def set_import_run_status(import_run: ImportRun, status: str, error_details: Optional[Dict] = None) -> None:
    """Persist import run status transitions and completion timestamps."""
    import_run.status = status
    if status in {ImportRun.STATUS_SUCCESS, ImportRun.STATUS_PARTIAL_FAILURE, ImportRun.STATUS_FAILED}:
        import_run.completed_at = dj_timezone.now()
    if error_details is not None:
        import_run.error_details = error_details
    import_run.save(
        update_fields=['status', 'completed_at', 'error_details', 'updated_at']
        if error_details is not None
        else ['status', 'completed_at', 'updated_at']
    )


def upsert_halfhourly_record(import_run: ImportRun, supply: Supply, row: Dict) -> Tuple[HalfHourlyConsumption, bool]:
    start = parse_utc_datetime(row.get('startDate') or row.get('periodStart') or row.get('start_date'))
    end = parse_utc_datetime(row.get('endDate') or row.get('periodEnd') or row.get('end_date'))
    value = Decimal(str(row.get('consumption', 0) or 0))
    return HalfHourlyConsumption.objects.update_or_create(
        supply=supply,
        source_period_start=start,
        source_period_end=end,
        defaults={
            'import_run': import_run,
            'canonical_month_key': canonical_month_key(end),
            'consumption': value,
        },
    )


def upsert_monthly_record(import_run: ImportRun, supply: Supply, row: Dict) -> Tuple[MonthlyConsumption, bool]:
    start = parse_utc_datetime(row.get('startDate') or row.get('periodStart') or row.get('start_date'))
    end = parse_utc_datetime(row.get('endDate') or row.get('periodEnd') or row.get('end_date'))
    value = Decimal(str(row.get('consumption', 0) or 0))
    breakdown = row.get('combinedBreakdown') or row.get('breakdown') or {}
    sources = row.get('sources') or []
    return MonthlyConsumption.objects.update_or_create(
        supply=supply,
        source_period_start=start,
        source_period_end=end,
        defaults={
            'import_run': import_run,
            'canonical_month_key': canonical_month_key(end),
            'consumption': value,
            'breakdown': breakdown if isinstance(breakdown, dict) else {},
            'sources': sources if isinstance(sources, list) else [],
        },
    )


def upsert_invoice_record(import_run: ImportRun, supply: Supply, row: Dict) -> Tuple[InvoiceCost, bool]:
    start = parse_utc_datetime(
        row.get('periodStart')
        or row.get('startDate')
        or row.get('fromDate')
        or row.get('period_start')
    )
    end = parse_utc_datetime(
        row.get('periodEnd')
        or row.get('endDate')
        or row.get('toDate')
        or row.get('period_end')
    )
    cost = Decimal(str(row.get('cost', 0) or row.get('amount', 0) or 0))
    metadata = {
        'invoiceDate': row.get('invoiceDate') or row.get('date'),
        'invoiceNumber': row.get('invoiceNumber') or row.get('number'),
        'status': row.get('status'),
    }
    return InvoiceCost.objects.update_or_create(
        supply=supply,
        source_period_start=start,
        source_period_end=end,
        defaults={
            'import_run': import_run,
            'canonical_month_key': canonical_month_key(end),
            'cost': cost,
            'invoice_metadata': {k: v for k, v in metadata.items() if v is not None},
        },
    )


class ConsumptionImportService:
    """Orchestrates usage/invoice imports for selected supplies and reporting month."""

    def __init__(self, api_client: Optional[EtainablApiClient] = None):
        self.client = api_client or EtainablApiClient()
        self.retry_count = max(0, int(settings.CONSUMPTION_IMPORT_RETRY_COUNT))
        self.retry_backoff = max(1, int(settings.CONSUMPTION_IMPORT_RETRY_BACKOFF_SECONDS))

    def run(self, supply_external_ids: List[str], reporting_month: str, refresh_mode: bool = True) -> ImportRun:
        import_run = ImportRun.objects.create(
            selected_supply_ids=supply_external_ids,
            reporting_month=reporting_month,
            status=ImportRun.STATUS_IN_PROGRESS,
            affected_supply_count=len(supply_external_ids),
        )

        records_imported = 0
        records_failed = 0
        retry_used = 0
        errors: Dict[str, str] = {}
        outcomes: List[Dict] = []

        supplies = list(Supply.objects.filter(external_id__in=supply_external_ids).order_by('id'))
        supply_by_external_id = {s.external_id: s for s in supplies}

        for supply_external_id in supply_external_ids:
            supply = supply_by_external_id.get(supply_external_id)
            if not supply:
                records_failed += 1
                errors[supply_external_id] = 'Supply not found'
                outcomes.append({
                    'supply_id': supply_external_id,
                    'status': 'failed',
                    'failure_reason': 'Supply not found',
                })
                continue

            try:
                outcome, imported_count, retries_for_supply, failed_ops = self._import_supply(import_run, supply, reporting_month)
                records_imported += imported_count
                retry_used += retries_for_supply
                records_failed += failed_ops
                outcomes.extend(outcome)
            except Exception as exc:  # pylint: disable=broad-except
                records_failed += 1
                errors[supply_external_id] = str(exc)
                outcomes.append({
                    'supply_id': supply.external_id,
                    'status': 'failed',
                    'failure_reason': str(exc),
                })

        import_run.records_imported = records_imported
        import_run.records_failed = records_failed
        import_run.retry_count = retry_used
        import_run.error_details = errors
        import_run.outcome_details = outcomes

        if records_failed == 0:
            import_run.status = ImportRun.STATUS_SUCCESS
        elif records_imported > 0:
            import_run.status = ImportRun.STATUS_PARTIAL_FAILURE
        else:
            import_run.status = ImportRun.STATUS_FAILED

        import_run.completed_at = dj_timezone.now()
        import_run.save()
        return import_run

    def _import_supply(self, import_run: ImportRun, supply: Supply, reporting_month: str) -> Tuple[List[Dict], int, int, int]:
        outcomes = []
        imported_count = 0
        retries_used = 0
        failed_ops = 0

        hh_windows = get_halfhourly_windows(reporting_month)
        for start, end in hh_windows:
            try:
                rows, retries = self._fetch_with_retry(
                    lambda: self.client.get_consumption(
                        account_id=supply.external_id,
                        start_date=start.isoformat().replace('+00:00', 'Z'),
                        end_date=end.isoformat().replace('+00:00', 'Z'),
                        granularity='halfhourly',
                    ),
                )
                retries_used += retries
                payload_rows = rows.get('data') if isinstance(rows, dict) else []
                payload_rows = payload_rows if isinstance(payload_rows, list) else []
                with transaction.atomic():
                    for row in payload_rows:
                        upsert_halfhourly_record(import_run, supply, row)
                        imported_count += 1
                outcomes.append({
                    'supply_id': supply.external_id,
                    'data_type': 'halfhourly',
                    'request_window': {'start': start.isoformat(), 'end': end.isoformat()},
                    'attempt_count': retries + 1,
                    'retry_used': retries > 0,
                    'response_code': 200,
                    'status': 'success',
                })
            except Exception as exc:  # pylint: disable=broad-except
                failed_ops += 1
                outcomes.append({
                    'supply_id': supply.external_id,
                    'data_type': 'halfhourly',
                    'request_window': {'start': start.isoformat(), 'end': end.isoformat()},
                    'attempt_count': self.retry_count + 1,
                    'retry_used': self.retry_count > 0,
                    'response_code': None,
                    'status': 'failed',
                    'failure_reason': str(exc),
                })

        monthly_start, monthly_end = get_monthly_window(reporting_month)
        try:
            monthly_payload, retries = self._fetch_with_retry(
                lambda: self.client.get_consumption(
                    account_id=supply.external_id,
                    start_date=monthly_start.isoformat().replace('+00:00', 'Z'),
                    end_date=monthly_end.isoformat().replace('+00:00', 'Z'),
                    granularity='monthly',
                ),
            )
            retries_used += retries
            monthly_rows = monthly_payload.get('data') if isinstance(monthly_payload, dict) else []
            monthly_rows = monthly_rows if isinstance(monthly_rows, list) else []
            with transaction.atomic():
                for row in monthly_rows:
                    upsert_monthly_record(import_run, supply, row)
                    imported_count += 1
            outcomes.append({
                'supply_id': supply.external_id,
                'data_type': 'monthly',
                'request_window': {'start': monthly_start.isoformat(), 'end': monthly_end.isoformat()},
                'attempt_count': retries + 1,
                'retry_used': retries > 0,
                'response_code': 200,
                'status': 'success',
            })
        except Exception as exc:  # pylint: disable=broad-except
            failed_ops += 1
            outcomes.append({
                'supply_id': supply.external_id,
                'data_type': 'monthly',
                'request_window': {'start': monthly_start.isoformat(), 'end': monthly_end.isoformat()},
                'attempt_count': self.retry_count + 1,
                'retry_used': self.retry_count > 0,
                'response_code': None,
                'status': 'failed',
                'failure_reason': str(exc),
            })

        invoice_start, invoice_end = get_invoice_window(reporting_month)
        try:
            invoice_rows, retries = self._fetch_with_retry(
                lambda: self.client.get_invoices(
                    account_id=supply.external_id,
                    start_date=invoice_start.isoformat().replace('+00:00', 'Z'),
                    end_date=invoice_end.isoformat().replace('+00:00', 'Z'),
                ),
            )
            retries_used += retries
            with transaction.atomic():
                for row in invoice_rows:
                    upsert_invoice_record(import_run, supply, row)
                    imported_count += 1
            outcomes.append({
                'supply_id': supply.external_id,
                'data_type': 'invoice',
                'request_window': {'start': invoice_start.isoformat(), 'end': invoice_end.isoformat()},
                'attempt_count': retries + 1,
                'retry_used': retries > 0,
                'response_code': 200,
                'status': 'success',
            })
        except Exception as exc:  # pylint: disable=broad-except
            failed_ops += 1
            outcomes.append({
                'supply_id': supply.external_id,
                'data_type': 'invoice',
                'request_window': {'start': invoice_start.isoformat(), 'end': invoice_end.isoformat()},
                'attempt_count': self.retry_count + 1,
                'retry_used': self.retry_count > 0,
                'response_code': None,
                'status': 'failed',
                'failure_reason': str(exc),
            })

        return outcomes, imported_count, retries_used, failed_ops

    def _fetch_with_retry(self, fetcher):
        attempts = 0
        while True:
            try:
                return fetcher(), attempts
            except Exception:  # pylint: disable=broad-except
                if attempts >= self.retry_count:
                    raise
                attempts += 1
                time.sleep(self.retry_backoff)


def get_consumption_display_records(reporting_month: str, data_type: str = 'monthly', supply_external_id: Optional[str] = None) -> List[Dict]:
    model_map = {
        'halfhourly': (HalfHourlyConsumption, 'consumption'),
        'monthly': (MonthlyConsumption, 'consumption'),
        'invoice': (InvoiceCost, 'cost'),
    }
    model, value_field = model_map.get(data_type, model_map['monthly'])

    qs = model.objects.filter(canonical_month_key=reporting_month).select_related('supply')
    if supply_external_id:
        qs = qs.filter(supply__external_id=supply_external_id)

    records = []
    for item in qs.order_by('-source_period_start'):
        records.append({
            'id': item.id,
            'supply_id': item.supply.id,
            'supply_external_id': item.supply.external_id,
            'supply_name': item.supply.name,
            'data_type': data_type,
            'source_period_start': item.source_period_start,
            'source_period_end': item.source_period_end,
            'canonical_month_key': item.canonical_month_key,
            'value': getattr(item, value_field),
            'updated_at': item.updated_at,
        })
    return records
