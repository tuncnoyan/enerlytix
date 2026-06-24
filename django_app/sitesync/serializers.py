"""
Serializers for Site, Supply, and Settings models.
"""

from rest_framework import serializers
from .models import Site, Supply, AppSettings


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
            'etainabl_api_url',
            'page_size',
            'api_timeout',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]
