"""
Views for the sitesync app.
"""

from django.db.models import Q
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from .models import Site, Supply, AppSettings
from .forms import SettingsForm
from .config_service import SettingsConfigService
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


def settings_panel_view(request):
    """Display and update runtime configuration settings."""
    settings_instance = SettingsConfigService.get_settings()

    if request.method == 'POST':
        form = SettingsForm(request.POST, instance=settings_instance)
        if form.is_valid():
            SettingsConfigService.update_settings(form)
    else:
        form = SettingsForm(instance=settings_instance)

    return render(request, 'sitesync/settings_panel.html', {
        'form': form,
        'settings': settings_instance,
        'save_success': request.method == 'POST' and form.is_valid(),
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
