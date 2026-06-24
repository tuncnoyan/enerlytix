"""
Views for the sitesync app.
"""

from django.db.models import Q
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from .models import Site, Supply, AppSettings
from .serializers import SiteSerializer, SupplySerializer, AppSettingsSerializer


def site_list_view(request):
    query = request.GET.get('q', '').strip()
    sites = Site.objects.prefetch_related('supplies').order_by('name')
    if query:
        sites = sites.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(external_id__icontains=query)
            | Q(supplies__name__icontains=query)
        ).distinct()

    return render(request, 'sitesync/site_list.html', {
        'sites': sites,
        'query': query,
    })


def supply_list_view(request):
    """Display supplies for a selected site."""
    site_id = request.GET.get('site_id')
    supplies = []
    
    if site_id:
        try:
            supplies = Supply.objects.filter(site_id=int(site_id)).order_by('name')
        except (ValueError, TypeError):
            supplies = []
    
    return render(request, 'sitesync/supply_list.html', {
        'supplies': supplies,
        'site_id': site_id,
    })


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
