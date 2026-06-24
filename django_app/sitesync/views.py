"""
Views for the sitesync app.
"""

from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from .models import Site, Supply, AppSettings
from .serializers import SiteSerializer, SupplySerializer, AppSettingsSerializer


class SiteViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Site model."""
    queryset = Site.objects.all()
    serializer_class = SiteSerializer


class SupplyViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Supply model."""
    queryset = Supply.objects.all()
    serializer_class = SupplySerializer


class AppSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for AppSettings model."""
    queryset = AppSettings.objects.all()
    serializer_class = AppSettingsSerializer
