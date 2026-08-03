"""
Django admin configuration for sitesync app.
"""

from django.contrib import admin
from .models import (
    Site,
    Supply,
    AppSettings,
    ImportRun,
    HalfHourlyConsumption,
    MonthlyConsumption,
    InvoiceCost,
    MonthlyReport,
    ReportWriteGrant,
    ReportOwnershipUnavailabilityApproval,
    ReportOwnershipTransferEvent,
)


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
    list_display = (
        'id',
        'electricity_benchmark_intensity',
        'gas_benchmark_intensity',
        'water_benchmark_intensity',
        'etainabl_api_url',
        'page_size',
        'api_timeout',
        'invoice_page_limit',
        'invoice_start_page',
        'updated_at',
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def has_add_permission(self, request):
        # Allow only one AppSettings instance
        return not AppSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ImportRun)
class ImportRunAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'reporting_month',
        'status',
        'affected_supply_count',
        'records_imported',
        'records_failed',
        'retry_count',
        'created_at',
    )
    list_filter = ('status', 'reporting_month', 'created_at')
    search_fields = ('id', 'reporting_month')
    readonly_fields = (
        'id',
        'selected_supply_ids',
        'reporting_month',
        'status',
        'started_at',
        'completed_at',
        'affected_supply_count',
        'records_imported',
        'records_failed',
        'retry_count',
        'error_details',
        'outcome_details',
        'created_at',
        'updated_at',
    )


@admin.register(HalfHourlyConsumption)
class HalfHourlyConsumptionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'supply',
        'canonical_month_key',
        'source_period_start',
        'source_period_end',
        'consumption',
        'updated_at',
    )
    search_fields = ('supply__name', 'supply__external_id', 'canonical_month_key')
    list_filter = ('canonical_month_key', 'created_at', 'updated_at')
    autocomplete_fields = ('import_run', 'supply')


@admin.register(MonthlyConsumption)
class MonthlyConsumptionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'supply',
        'canonical_month_key',
        'source_period_start',
        'source_period_end',
        'consumption',
        'updated_at',
    )
    search_fields = ('supply__name', 'supply__external_id', 'canonical_month_key')
    list_filter = ('canonical_month_key', 'created_at', 'updated_at')
    autocomplete_fields = ('import_run', 'supply')


@admin.register(InvoiceCost)
class InvoiceCostAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'supply',
        'canonical_month_key',
        'source_period_start',
        'source_period_end',
        'cost',
        'updated_at',
    )
    search_fields = ('supply__name', 'supply__external_id', 'canonical_month_key')
    list_filter = ('canonical_month_key', 'created_at', 'updated_at')
    autocomplete_fields = ('import_run', 'supply')


@admin.register(MonthlyReport)
class MonthlyReportAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'site',
        'reporting_month',
        'current_status',
        'owner_user',
        'last_modified_by_user',
        'last_modified_at',
        'updated_at',
    )
    list_filter = ('current_status', 'reporting_month', 'owner_user')
    search_fields = ('site__name', 'reporting_month', 'owner_user__username')


@admin.register(ReportWriteGrant)
class ReportWriteGrantAdmin(admin.ModelAdmin):
    list_display = ('id', 'report', 'granted_user', 'granted_by', 'is_active', 'granted_at', 'revoked_at')
    list_filter = ('is_active', 'granted_at')
    search_fields = ('report__site__name', 'granted_user__username', 'granted_by__username')


@admin.register(ReportOwnershipUnavailabilityApproval)
class ReportOwnershipUnavailabilityApprovalAdmin(admin.ModelAdmin):
    list_display = ('id', 'report', 'owner_user', 'approved_by', 'status', 'approved_at')
    list_filter = ('status', 'approved_at')
    search_fields = ('report__site__name', 'owner_user__username', 'approved_by__username')


@admin.register(ReportOwnershipTransferEvent)
class ReportOwnershipTransferEventAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'report',
        'from_owner',
        'to_owner',
        'transfer_mode',
        'transferred_at',
        'executed_by',
    )
    list_filter = ('transfer_mode', 'transferred_at')
    search_fields = ('report__site__name', 'from_owner__username', 'to_owner__username')
