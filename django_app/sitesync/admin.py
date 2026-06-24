"""
Django admin configuration for sitesync app.
"""

from django.contrib import admin
from .models import Site, Supply, AppSettings


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'external_id', 'created_at')
    search_fields = ('name', 'external_id')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('external_id', 'created_at', 'updated_at')


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'site', 'utility_type', 'device_id', 'created_at')
    search_fields = ('name', 'external_id', 'site__name')
    list_filter = ('utility_type', 'created_at', 'updated_at')
    readonly_fields = ('external_id', 'created_at', 'updated_at')
    autocomplete_fields = ('site',)


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'etainabl_api_url', 'page_size', 'api_timeout', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    
    def has_add_permission(self, request):
        # Allow only one AppSettings instance
        return not AppSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
