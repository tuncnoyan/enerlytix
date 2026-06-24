"""
App configuration for sitesync.
"""

from django.apps import AppConfig


class SitesyncConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sitesync'
    
    def ready(self):
        """Initialize app on startup."""
        import logging
        import threading
        import sys
        import os
        logger = logging.getLogger(__name__)
        logger.info("Sitesync app ready")
        
        # Avoid running sync during management commands like 'migrate' or tests
        if any(cmd in sys.argv for cmd in ['makemigrations', 'migrate', 'test']):
            logger.debug("Skipping automatic sync during management command")
            return
        
        # Only run automatic sync when runserver main process is running
        if os.environ.get('RUN_MAIN') != 'true' and 'runserver' not in sys.argv:
            logger.debug("Not running under runserver main process; skipping automatic sync")
            return
        
        def run_sync():
            try:
                from .services import EtainaibleSyncService
                sync_service = EtainaibleSyncService()
                sync_service.sync_all()
            except Exception:
                logger.exception("Automatic initial sync failed")

        t = threading.Thread(target=run_sync, daemon=True)
        t.start()
