"""
Serializers for Site, Supply, and Settings models.
"""

from rest_framework import serializers
from .models import (
    Site,
    Supply,
    Benchmark,
    AppSettings,
    ImportRun,
    HalfHourlyConsumption,
    MonthlyConsumption,
    InvoiceCost,
)


class SupplySerializer(serializers.ModelSerializer):
    """Serializer for Supply model."""
    utility_type_display = serializers.CharField(
        source='get_utility_type_display',
        read_only=True
    )

    class Meta:
        model = Supply
        fields = [
            'id',
            'external_id',
            'name',
            'utility_type',
            'utility_type_display',
            'device_id',
            'parent_account_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]


class SiteSerializer(serializers.ModelSerializer):
    """Serializer for Site model with nested supplies."""
    supplies = SupplySerializer(many=True, read_only=True)
    supply_count = serializers.SerializerMethodField()

    class Meta:
        model = Site
        fields = [
            'id',
            'external_id',
            'name',
            'description',
            'supplies',
            'supply_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]

    def get_supply_count(self, obj):
        return obj.supplies.count()


class SiteListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for Site list view (without nested supplies)."""
    supply_count = serializers.SerializerMethodField()

    class Meta:
        model = Site
        fields = [
            'id',
            'external_id',
            'name',
            'supply_count',
        ]

    def get_supply_count(self, obj):
        return obj.supplies.count()


class AppSettingsSerializer(serializers.ModelSerializer):
    """Serializer for AppSettings model."""

    class Meta:
        model = AppSettings
        fields = [
            'id',
            'electricity_benchmark_intensity',
            'gas_benchmark_intensity',
            'water_benchmark_intensity',
            'etainabl_api_url',
            'page_size',
            'api_timeout',
            'invoice_page_limit',
            'invoice_start_page',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]


class BenchmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benchmark
        fields = [
            'id',
            'supply',
            'canonical_month_key',
            'value',
            'unit',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]


class ConsumptionImportRequestSerializer(serializers.Serializer):
    supply_ids = serializers.ListField(
        child=serializers.CharField(),
        min_length=1,
    )
    reporting_month = serializers.RegexField(regex=r'^\d{4}-\d{2}$')
    refresh_mode = serializers.BooleanField(required=False, default=True)


class ConsumptionDisplayQuerySerializer(serializers.Serializer):
    reporting_month = serializers.RegexField(regex=r'^\d{4}-\d{2}$')
    supply_id = serializers.CharField(required=False, allow_blank=False)
    supply_ids = serializers.CharField(required=False, allow_blank=False)
    data_type = serializers.ChoiceField(
        choices=['halfhourly', 'monthly', 'invoice'],
        required=False,
        default='monthly',
    )


class ImportRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportRun
        fields = [
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
        ]


class ConsumptionRecordSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    supply_id = serializers.IntegerField()
    data_type = serializers.CharField()
    source_period_start = serializers.DateTimeField()
    source_period_end = serializers.DateTimeField()
    canonical_month_key = serializers.CharField()
    value = serializers.DecimalField(max_digits=16, decimal_places=6)


class HalfHourlyConsumptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HalfHourlyConsumption
        fields = '__all__'


class MonthlyConsumptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyConsumption
        fields = '__all__'


class InvoiceCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceCost
        fields = '__all__'


class ReportDelegationActionSerializer(serializers.Serializer):
    delegate_user_id = serializers.UUIDField()


class ReportDelegationVisibilitySerializer(serializers.Serializer):
    delegate_user = serializers.CharField()
    granted_by_user = serializers.CharField(allow_blank=True)
    granted_by_role = serializers.CharField()
    granted_at = serializers.DateTimeField()
    is_active = serializers.BooleanField()
