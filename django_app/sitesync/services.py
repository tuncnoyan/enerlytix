"""
Etainabl API sync service for fetching and persisting site and supply data.
"""

import logging
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Set, Tuple
import requests
from openpyxl import load_workbook
from django.conf import settings
from django.db import transaction
from django.utils import timezone as dj_timezone

from .api_client import EtainablApiClient
from .models import (
    Site,
    Supply,
    AppSettings,
    CapacityReference,
    CapacityUploadRun,
    ImportRun,
    HalfHourlyConsumption,
    MonthlyConsumption,
    InvoiceCost,
    MonthlyReport,
    MonthlyReportVersion,
    ReportComment,
)

logger = logging.getLogger(__name__)

CAPACITY_REQUIRED_HEADERS = (
    'Name',
    'eSight Meter Code',
    'Av Cap (kVA)',
)
CAPACITY_UPLOAD_STATUS_SUCCESS = CapacityUploadRun.STATUS_SUCCESS
CAPACITY_UPLOAD_STATUS_PARTIAL_SUCCESS = CapacityUploadRun.STATUS_PARTIAL_SUCCESS
CAPACITY_UPLOAD_STATUS_FAILED = CapacityUploadRun.STATUS_FAILED
CAPACITY_UPLOAD_ERROR_FILE_EMPTY = 'File is empty or missing a header row.'
CAPACITY_UPLOAD_ERROR_PARSE_PREFIX = 'Upload parsing failed:'
SITE_FLOOR_AREA_UNIT_SQM = 'sqm'
SITE_FLOOR_AREA_UNIT_SQFT = 'sqft'


def _build_capacity_upload_result(run: CapacityUploadRun) -> Dict:
    """Normalize upload-run persistence into the view-facing result contract."""
    return {
        'status': run.status,
        'total_rows': run.total_rows,
        'accepted_rows': run.accepted_rows,
        'rejected_rows': run.rejected_rows,
        'errors': run.error_summary,
        'run': run,
    }


def _normalize_floor_area_unit(value: Optional[str]) -> Optional[str]:
    """Normalize Etainabl floor-area unit values into sqm/sqft."""
    raw = str(value or '').strip().casefold()
    if not raw:
        return None
    if raw in {'sqm', 'sq m', 'sq metre', 'sq meter', 'square metre', 'square meter', 'm2', 'm^2', 'metric'}:
        return SITE_FLOOR_AREA_UNIT_SQM
    if raw in {'sqft', 'sq ft', 'square foot', 'square feet', 'ft2', 'ft^2', 'imperial'}:
        return SITE_FLOOR_AREA_UNIT_SQFT
    return None


def _extract_floor_area_from_value(value) -> Tuple[Optional[Decimal], Optional[str]]:
    """Extract floor-area value and unit from a direct or nested asset payload value."""
    if isinstance(value, dict):
        area_value = (
            value.get('value')
            or value.get('amount')
            or value.get('area')
            or value.get('size')
            or value.get('measurement')
        )
        unit_value = (
            value.get('unit')
            or value.get('uom')
            or value.get('unitType')
            or value.get('measurementUnit')
        )
        if area_value is None:
            return None, _normalize_floor_area_unit(unit_value)
        try:
            area = Decimal(str(area_value).strip())
        except (InvalidOperation, ValueError, AttributeError):
            return None, _normalize_floor_area_unit(unit_value)
        normalized_unit = _normalize_floor_area_unit(unit_value)
        if area == Decimal('1'):
            area = Decimal('0')
        return area, normalized_unit

    if value is None or str(value).strip() == '':
        return None, None
    try:
        area = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None, None
    if area == Decimal('1'):
        area = Decimal('0')
    return area, None


def _extract_site_floor_area(asset_data: Dict) -> Tuple[Optional[Decimal], Optional[str]]:
    """Extract site floor area and original unit from known or likely Etainabl asset keys."""
    candidates = [
        ('floorArea', 'floorAreaUnit'),
        ('floor_area', 'floor_area_unit'),
        ('grossInternalArea', 'grossInternalAreaUnit'),
        ('netInternalArea', 'netInternalAreaUnit'),
        ('internalArea', 'internalAreaUnit'),
        ('buildingArea', 'buildingAreaUnit'),
        ('area', 'areaUnit'),
    ]

    for area_key, unit_key in candidates:
        if area_key not in asset_data:
            continue
        area, unit = _extract_floor_area_from_value(asset_data.get(area_key))
        if unit is None:
            unit = _normalize_floor_area_unit(asset_data.get(unit_key))
        if area is not None or unit is not None:
            return area, unit

    for key, value in asset_data.items():
        if not isinstance(value, dict):
            continue
        if 'area' not in str(key).casefold() and 'floor' not in str(key).casefold():
            continue
        area, unit = _extract_floor_area_from_value(value)
        if area is not None or unit is not None:
            return area, unit

    return None, None


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
            'sites_deleted': 0,
            'supplies_created': 0,
            'supplies_updated': 0,
            'supplies_deleted': 0,
        }
        
        try:
            # Sync assets (sites)
            sites_result = self.sync_assets()
            results['sites_created'] = sites_result.get('created', 0)
            results['sites_updated'] = sites_result.get('updated', 0)
            results['sites_deleted'] = sites_result.get('deleted', 0)
            logger.info(
                f"Assets sync complete: {results['sites_created']} created, "
                f"{results['sites_updated']} updated, "
                f"{results['sites_deleted']} deleted"
            )
            
            # Sync accounts (supplies)
            supplies_result = self.sync_accounts()
            results['supplies_created'] = supplies_result.get('created', 0)
            results['supplies_updated'] = supplies_result.get('updated', 0)
            results['supplies_deleted'] = supplies_result.get('deleted', 0)
            logger.info(
                f"Accounts sync complete: {results['supplies_created']} created, "
                f"{results['supplies_updated']} updated, "
                f"{results['supplies_deleted']} deleted"
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
        deleted = 0
        remote_site_ids: Set[str] = set()
        received_valid_payload = False
        
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

                received_valid_payload = True

                if not assets:
                    logger.info(f"No more assets to fetch (page={page})")
                    break
                
                # Process each asset
                for asset in assets:
                    external_id = self._extract_site_external_id(asset)
                    if external_id:
                        remote_site_ids.add(external_id)
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

            if received_valid_payload:
                stale_sites = Site.objects.exclude(external_id__in=remote_site_ids)
                deleted = stale_sites.count()
                if deleted:
                    stale_sites.delete()
                    logger.info("Removed %s stale sites not present in Etainabl", deleted)
            else:
                logger.warning("Skipping stale site reconciliation due to invalid assets payload shape")
            
            logger.info(
                "Asset sync complete: %s created, %s updated, %s skipped, %s deleted",
                created,
                updated,
                skipped,
                deleted,
            )
            return {
                'created': created,
                'updated': updated,
                'skipped': skipped,
                'deleted': deleted,
            }
            
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
        deleted = 0
        remote_supply_ids: Set[str] = set()
        received_valid_payload = False
        
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

                received_valid_payload = True

                if not accounts:
                    logger.info(f"No more accounts to fetch (page={page})")
                    break
                
                # Process each account
                for account in accounts:
                    external_id = self._extract_supply_external_id(account)
                    if external_id:
                        remote_supply_ids.add(external_id)
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

            if received_valid_payload:
                stale_supplies = Supply.objects.exclude(external_id__in=remote_supply_ids)
                deleted = stale_supplies.count()
                if deleted:
                    stale_supplies.delete()
                    logger.info("Removed %s stale supplies not present in Etainabl", deleted)
            else:
                logger.warning("Skipping stale supply reconciliation due to invalid accounts payload shape")
            
            logger.info(
                "Account sync complete: %s created, %s updated, %s skipped, %s deleted",
                created,
                updated,
                skipped,
                deleted,
            )
            return {
                'created': created,
                'updated': updated,
                'skipped': skipped,
                'deleted': deleted,
            }
            
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
            external_id = self._extract_site_external_id(asset_data)
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
            floor_area_value, floor_area_unit = _extract_site_floor_area(asset_data)
            
            site, created = Site.objects.update_or_create(
                external_id=external_id,
                defaults={
                    'name': str(name_value or 'Unknown'),
                    'description': str(description_value or ''),
                    'floor_area': floor_area_value,
                    'floor_area_unit': floor_area_unit,
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
            external_id = self._extract_supply_external_id(account_data)
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
            status = self._normalize_supply_status(account_data)

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
                    'status': status,
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

    def _extract_site_external_id(self, asset_data: Dict) -> Optional[str]:
        """Extract a stable site external ID from asset payload."""
        external_id = (
            asset_data.get('id')
            or asset_data.get('_id')
            or asset_data.get('assetId')
        )
        if not external_id:
            return None
        return str(external_id).strip()

    def _extract_supply_external_id(self, account_data: Dict) -> Optional[str]:
        """Extract a stable supply external ID from account payload."""
        external_id = account_data.get('id') or account_data.get('_id')
        if not external_id:
            return None
        return str(external_id).strip()

    def _normalize_supply_status(self, account_data: Dict) -> Optional[str]:
        """Extract and normalize account status from Etainabl payload."""
        raw_status = (
            account_data.get('status')
            or account_data.get('state')
            or account_data.get('accountStatus')
        )
        if isinstance(raw_status, dict):
            raw_status = (
                raw_status.get('status')
                or raw_status.get('state')
                or raw_status.get('value')
                or raw_status.get('label')
            )
        if raw_status is None:
            return None

        status = str(raw_status).strip().lower()
        return status or None


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
    """Derive canonical month key from UTC datetime.

    Etainabl uses exclusive end dates: a period ending on 2026-06-01T00:00:00Z
    covers up to (but not including) June 1st, so it belongs to May 2026.
    When the timestamp is exactly midnight on the 1st of a month we subtract one
    second to land in the correct (previous) month.
    """
    dt = value.astimezone(timezone.utc)
    if dt.day == 1 and dt.hour == 0 and dt.minute == 0 and dt.second == 0:
        dt = dt - timedelta(seconds=1)
    return dt.strftime('%Y-%m')


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


def format_api_datetime(value: datetime) -> str:
    """Format UTC datetime for Xcelerate API requests (ISO with millisecond precision)."""
    return value.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')


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


def normalize_reporting_month(end_month: Optional[str], reporting_month: Optional[str]) -> str:
    """Normalize dual parameter naming to one canonical report month key."""
    candidate = (end_month or '').strip() or (reporting_month or '').strip()
    if not candidate:
        now = dj_timezone.localtime(dj_timezone.now())
        candidate = shift_months(month_start(now.year, now.month), -1).strftime('%Y-%m')
    # Reuse existing bounds parser as format validation.
    reporting_month_bounds(candidate)
    return candidate


def normalize_capacity_header(value: Optional[str]) -> str:
    """Normalize upload headers with trim + casefold rules."""
    return str(value or '').strip().casefold()


def normalize_esight_meter_code(value: Optional[str]) -> str:
    """Normalize eSight meter code for deterministic matching and storage."""
    return str(value or '').strip().upper()


def get_capacity_lookup_by_meter_codes(meter_codes: List[str]) -> Dict[str, Decimal]:
    """Return normalized meter-code -> available_capacity_kva lookup map."""
    normalized = [normalize_esight_meter_code(code) for code in meter_codes if normalize_esight_meter_code(code)]
    if not normalized:
        return {}
    return {
        row.esight_meter_code: row.available_capacity_kva
        for row in CapacityReference.objects.filter(esight_meter_code__in=normalized)
    }


def import_capacity_upload(uploaded_file) -> Dict:
    """Import available capacity reference rows from an uploaded .xlsx file."""
    filename = getattr(uploaded_file, 'name', '')
    required_headers_normalized = {
        normalize_capacity_header(header): header
        for header in CAPACITY_REQUIRED_HEADERS
    }
    row_errors = []
    accepted_rows = 0
    total_rows = 0

    try:
        uploaded_file.seek(0)
        workbook = load_workbook(uploaded_file, data_only=True)
        worksheet = workbook.active
        row_iter = worksheet.iter_rows(values_only=True)
        header_row = next(row_iter, None)

        if header_row is None:
            run = CapacityUploadRun.objects.create(
                uploaded_filename=filename,
                total_rows=0,
                accepted_rows=0,
                rejected_rows=0,
                status=CAPACITY_UPLOAD_STATUS_FAILED,
                error_summary=[CAPACITY_UPLOAD_ERROR_FILE_EMPTY],
            )
            return _build_capacity_upload_result(run)

        header_values = [normalize_capacity_header(cell) for cell in header_row]
        missing = [
            canonical
            for normalized, canonical in required_headers_normalized.items()
            if normalized not in header_values
        ]
        if missing:
            run = CapacityUploadRun.objects.create(
                uploaded_filename=filename,
                total_rows=0,
                accepted_rows=0,
                rejected_rows=0,
                status=CAPACITY_UPLOAD_STATUS_FAILED,
                error_summary=[f"Missing required columns: {', '.join(missing)}"],
            )
            return _build_capacity_upload_result(run)

        indexes = {
            canonical: header_values.index(normalized)
            for normalized, canonical in required_headers_normalized.items()
        }

        seen_codes = set()
        valid_rows = []
        for row_index, row in enumerate(row_iter, start=2):
            if row is None:
                continue
            if all(cell is None or str(cell).strip() == '' for cell in row):
                continue

            total_rows += 1
            name_raw = row[indexes['Name']] if len(row) > indexes['Name'] else None
            code_raw = row[indexes['eSight Meter Code']] if len(row) > indexes['eSight Meter Code'] else None
            capacity_raw = row[indexes['Av Cap (kVA)']] if len(row) > indexes['Av Cap (kVA)'] else None

            name = str(name_raw or '').strip()
            code = normalize_esight_meter_code(code_raw)
            current_errors = []

            if not name:
                current_errors.append('Name is blank')
            if not code:
                current_errors.append('eSight Meter Code is blank')

            capacity_value = None
            capacity_text = '' if capacity_raw is None else str(capacity_raw).strip()
            if not capacity_text:
                current_errors.append('Av Cap (kVA) is blank')
            else:
                try:
                    capacity_value = Decimal(capacity_text)
                    if capacity_value < 0:
                        current_errors.append('Av Cap (kVA) cannot be negative')
                except (InvalidOperation, ValueError):
                    current_errors.append('Av Cap (kVA) must be numeric when provided')

            if code and code in seen_codes:
                current_errors.append('Duplicate eSight Meter Code in upload')

            if current_errors:
                row_errors.append(f"Row {row_index}: {', '.join(current_errors)}")
                continue

            seen_codes.add(code)
            valid_rows.append({
                'name': name,
                'esight_meter_code': code,
                'available_capacity_kva': capacity_value,
            })

        with transaction.atomic():
            now = dj_timezone.now()
            for valid_row in valid_rows:
                CapacityReference.objects.update_or_create(
                    esight_meter_code=valid_row['esight_meter_code'],
                    defaults={
                        'name': valid_row['name'],
                        'available_capacity_kva': valid_row['available_capacity_kva'],
                        'source_filename': filename,
                        'last_imported_at': now,
                    },
                )
                accepted_rows += 1

            rejected_rows = len(row_errors)
            if accepted_rows > 0 and rejected_rows == 0:
                status = CAPACITY_UPLOAD_STATUS_SUCCESS
            elif accepted_rows > 0 and rejected_rows > 0:
                status = CAPACITY_UPLOAD_STATUS_PARTIAL_SUCCESS
            else:
                status = CAPACITY_UPLOAD_STATUS_FAILED

            run = CapacityUploadRun.objects.create(
                uploaded_filename=filename,
                total_rows=total_rows,
                accepted_rows=accepted_rows,
                rejected_rows=rejected_rows,
                status=status,
                error_summary=row_errors,
            )

        return _build_capacity_upload_result(run)
    except Exception as exc:  # pylint: disable=broad-except
        run = CapacityUploadRun.objects.create(
            uploaded_filename=filename,
            total_rows=0,
            accepted_rows=0,
            rejected_rows=0,
            status=CAPACITY_UPLOAD_STATUS_FAILED,
            error_summary=[f'{CAPACITY_UPLOAD_ERROR_PARSE_PREFIX} {str(exc)}'],
        )
        return _build_capacity_upload_result(run)


def get_or_create_monthly_report(site: Site, reporting_month: str) -> MonthlyReport:
    """Return the unique monthly report identity for site + reporting month."""
    report, _ = MonthlyReport.objects.get_or_create(
        site=site,
        reporting_month=reporting_month,
        defaults={'current_status': MonthlyReport.STATUS_DRAFT},
    )
    return report


def _next_report_version_number(report: MonthlyReport) -> int:
    latest = report.versions.order_by('-version_number').first()
    return 1 if latest is None else latest.version_number + 1


def create_report_version(
    report: MonthlyReport,
    version_kind: str,
    comments: Optional[Dict[str, str]] = None,
    derived_from_version: Optional[MonthlyReportVersion] = None,
) -> MonthlyReportVersion:
    """Create an immutable report version and update report pointers."""
    version = MonthlyReportVersion.objects.create(
        report=report,
        version_number=_next_report_version_number(report),
        version_kind=version_kind,
        derived_from_version=derived_from_version,
    )

    for visual_key, text in (comments or {}).items():
        ReportComment.objects.create(
            report_version=version,
            visual_key=str(visual_key),
            text=str(text or ''),
        )

    report.current_version = version
    if version_kind in {MonthlyReportVersion.KIND_FINAL, MonthlyReportVersion.KIND_REPLACEMENT_FINAL}:
        report.current_status = MonthlyReport.STATUS_FINAL
        report.current_final_version = version
    else:
        report.current_status = MonthlyReport.STATUS_DRAFT
    report.save(update_fields=['current_version', 'current_final_version', 'current_status', 'updated_at'])
    return version


def get_previous_month_final_version(site: Site, reporting_month: str) -> Optional[MonthlyReportVersion]:
    """Return the prior month final version for the same site, if available."""
    start, _ = reporting_month_bounds(reporting_month)
    previous_month = shift_months(start, -1).strftime('%Y-%m')
    previous_report = MonthlyReport.objects.filter(site=site, reporting_month=previous_month).first()
    if not previous_report:
        return None
    return previous_report.current_final_version


def carry_forward_comments_from_previous_final(
    report: MonthlyReport,
    report_version: MonthlyReportVersion,
) -> int:
    """Copy previous-month final comments into this version as reference comments.

    A comment is (re)tagged as a reference copy unless the version already has
    a saved comment for that visual key with different text - which means the
    user edited the prefilled reference comment before saving, so their edit
    is preserved as-is.
    """
    previous_final = get_previous_month_final_version(report.site, report.reporting_month)
    if previous_final is None:
        return 0

    existing_comments = {comment.visual_key: comment for comment in report_version.comments.all()}

    copied = 0
    for previous_comment in previous_final.comments.all().order_by('visual_key'):
        existing = existing_comments.get(previous_comment.visual_key)
        if existing is not None and existing.text != previous_comment.text:
            continue

        ReportComment.objects.update_or_create(
            report_version=report_version,
            visual_key=previous_comment.visual_key,
            defaults={
                'text': previous_comment.text,
                'is_reference_copy': True,
                'source_reporting_month': previous_final.report.reporting_month,
                'source_version': previous_final,
            },
        )
        copied += 1

    return copied


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
    breakdown = row.get('combinedBreakdown') or {}
    hh_value = None
    if isinstance(breakdown, dict):
        hh_value = breakdown.get('hh')
    if hh_value is None:
        hh_value = row.get('consumption', 0)
    value = Decimal(str(hh_value or 0))
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
    values = row.get('values') if isinstance(row.get('values'), dict) else {}

    def pick(*keys: str):
        for key in keys:
            if values.get(key) is not None:
                return values.get(key)
            if row.get(key) is not None:
                return row.get(key)
        return None

    start_raw = pick(
        'startDate',
        'periodStart',
        'fromDate',
        'start_date',
        'period_start',
        'invoiceDate',
        'date',
    )
    end_raw = pick(
        'endDate',
        'periodEnd',
        'toDate',
        'end_date',
        'period_end',
    ) or start_raw
    start = parse_utc_datetime(start_raw)
    end = parse_utc_datetime(end_raw)
    cost = Decimal(str(pick('netTotalCost', 'netCost', 'cost', 'amount') or 0))
    metadata = {
        'invoiceDate': pick('invoiceDate', 'date'),
        'invoiceNumber': pick('invoiceNumber', 'number'),
        'status': pick('status'),
        'financialStatus': pick('financialStatus'),
        'completed': pick('completed'),
        'type': pick('type'),
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
                outcome, imported_count, retries_for_supply, failed_ops = self._import_supply(
                    import_run,
                    supply,
                    reporting_month,
                    refresh_mode=refresh_mode,
                )
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

    def _import_supply(
        self,
        import_run: ImportRun,
        supply: Supply,
        reporting_month: str,
        refresh_mode: bool,
    ) -> Tuple[List[Dict], int, int, int]:
        outcomes = []
        imported_count = 0
        retries_used = 0
        failed_ops = 0

        hh_windows = get_halfhourly_windows(reporting_month)
        for start, end in hh_windows:
            if not refresh_mode and HalfHourlyConsumption.objects.filter(
                supply=supply,
                source_period_start__gte=start,
                source_period_start__lt=end,
            ).exists():
                outcomes.append({
                    'supply_id': supply.external_id,
                    'data_type': 'halfhourly',
                    'request_window': {'start': start.isoformat(), 'end': end.isoformat()},
                    'attempt_count': 0,
                    'retry_used': False,
                    'response_code': None,
                    'status': 'skipped',
                    'reason': 'cached_data_reused',
                })
                continue
            try:
                rows, retries, account_id_used = self._fetch_consumption_for_supply(
                    supply=supply,
                    start_date=format_api_datetime(start),
                    end_date=format_api_datetime(end),
                    granularity='halfhourly',
                    source='combined',
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
                    'account_id': account_id_used,
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
        if not refresh_mode and MonthlyConsumption.objects.filter(
            supply=supply,
            source_period_start__gte=monthly_start,
            source_period_start__lt=monthly_end,
        ).exists():
            outcomes.append({
                'supply_id': supply.external_id,
                'data_type': 'monthly',
                'request_window': {'start': monthly_start.isoformat(), 'end': monthly_end.isoformat()},
                'attempt_count': 0,
                'retry_used': False,
                'response_code': None,
                'status': 'skipped',
                'reason': 'cached_data_reused',
            })
        else:
            try:
                monthly_payload, retries, account_id_used = self._fetch_consumption_for_supply(
                    supply=supply,
                    start_date=format_api_datetime(monthly_start),
                    end_date=format_api_datetime(monthly_end),
                    granularity='monthly',
                    source='combined',
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
                    'account_id': account_id_used,
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
        has_invoice_window_data = InvoiceCost.objects.filter(
            supply=supply,
            source_period_end__gte=invoice_start,
            source_period_end__lte=invoice_end,  # inclusive: catches invoices ending exactly on the boundary
        ).exists()
        if not refresh_mode and has_invoice_window_data:
            outcomes.append({
                'supply_id': supply.external_id,
                'data_type': 'invoice',
                'request_window': {'start': invoice_start.isoformat(), 'end': invoice_end.isoformat()},
                'attempt_count': 0,
                'retry_used': False,
                'response_code': None,
                'status': 'skipped',
                'reason': 'cached_data_reused',
            })
        else:
            try:
                invoice_rows, retries, account_id_used = self._fetch_invoices_for_supply(
                    supply=supply,
                    start_date=format_api_datetime(invoice_start),
                    end_date=format_api_datetime(invoice_end),
                )
                retries_used += retries
                skipped_invoice_rows = 0
                with transaction.atomic():
                    for row in invoice_rows:
                        try:
                            upsert_invoice_record(import_run, supply, row)
                            imported_count += 1
                        except ValueError:
                            skipped_invoice_rows += 1
                            logger.warning(
                                "Skipping invoice row with missing datetime fields for supply %s",
                                supply.external_id,
                            )
                outcomes.append({
                    'supply_id': supply.external_id,
                    'data_type': 'invoice',
                    'request_window': {'start': invoice_start.isoformat(), 'end': invoice_end.isoformat()},
                    'attempt_count': retries + 1,
                    'retry_used': retries > 0,
                    'response_code': 200,
                    'account_id': account_id_used,
                    'skipped_rows': skipped_invoice_rows,
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

    def _account_id_candidates(self, supply: Supply) -> List[str]:
        candidates = [
            getattr(settings, 'ETAINABL_ACCOUNT_ID', None),
            supply.external_id,
            supply.parent_account_id,
            supply.name,
        ]
        cleaned = []
        for candidate in candidates:
            if not candidate:
                continue
            value = str(candidate).strip()
            if not value:
                continue
            if value not in cleaned:
                cleaned.append(value)
        return cleaned

    def _fetch_consumption_for_supply(self, supply: Supply, start_date: str, end_date: str, granularity: str, source: str):
        errors = []
        for account_id in self._account_id_candidates(supply):
            try:
                payload, retries = self._fetch_with_retry(
                    lambda: self.client.get_consumption(
                        account_id=account_id,
                        start_date=start_date,
                        end_date=end_date,
                        granularity=granularity,
                        source=source,
                    ),
                )
                return payload, retries, account_id
            except Exception as exc:  # pylint: disable=broad-except
                errors.append(f"{account_id}: {exc}")
        raise Exception('All accountId candidates failed for consumption: ' + ' | '.join(errors))

    def _fetch_invoices_for_supply(self, supply: Supply, start_date: str, end_date: str):
        errors = []
        for account_id in self._account_id_candidates(supply):
            try:
                payload, retries = self._fetch_with_retry(
                    lambda: self.client.get_invoices(
                        account_id=account_id,
                        start_date=start_date,
                        end_date=end_date,
                    ),
                )
                logger.info(
                    "Invoice fetch for supply %s: accountId=%s returned %d rows",
                    supply.external_id, account_id, len(payload) if isinstance(payload, list) else -1,
                )
                return payload, retries, account_id
            except Exception as exc:  # pylint: disable=broad-except
                errors.append(f"{account_id}: {exc}")
        raise Exception('All accountId candidates failed for invoices: ' + ' | '.join(errors))


def get_consumption_display_records(
    reporting_month: str,
    data_type: str = 'monthly',
    supply_external_id: Optional[str] = None,
    supply_external_ids: Optional[List[str]] = None,
) -> List[Dict]:
    model_map = {
        'halfhourly': (HalfHourlyConsumption, 'consumption'),
        'monthly': (MonthlyConsumption, 'consumption'),
        'invoice': (InvoiceCost, 'cost'),
    }
    model, value_field = model_map.get(data_type, model_map['monthly'])

    qs = model.objects.select_related('supply')

    if supply_external_ids:
        qs = qs.filter(supply__external_id__in=supply_external_ids)
    if supply_external_id:
        qs = qs.filter(supply__external_id=supply_external_id)

    # For monthly display, show the trailing 12-month window ending at reporting month.
    if data_type == 'monthly':
        report_start, report_end = reporting_month_bounds(reporting_month)
        window_start = shift_months(report_start, -11)
        qs = qs.filter(source_period_start__gte=window_start, source_period_start__lt=report_end)
    elif data_type == 'invoice':
        window_start, report_end = get_invoice_window(reporting_month)
        window_qs = qs.filter(source_period_end__gte=window_start, source_period_end__lte=report_end)
        if window_qs.exists():
            qs = window_qs
        else:
            # No data in the requested window — fall back to all available invoice history
            # so the user can at least see what has been imported.
            pass  # qs already covers all records for the supply
    else:
        qs = qs.filter(canonical_month_key=reporting_month)

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
