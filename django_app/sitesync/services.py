"""
Etainabl API sync service for fetching and persisting site and supply data.
"""

import logging
import time
from typing import Dict, List, Optional
import requests
from django.conf import settings
from .models import Site, Supply, AppSettings

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
            if isinstance(site_external_id, dict):
                site_external_id = (
                    site_external_id.get('id')
                    or site_external_id.get('_id')
                    or site_external_id.get('assetId')
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
