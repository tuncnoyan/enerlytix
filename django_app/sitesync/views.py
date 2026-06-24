"""
Views for the sitesync app.
"""

import logging

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from rest_framework import viewsets
from rest_framework.response import Response
from .models import Site, Supply, AppSettings
from .forms import SettingsForm
from .config_service import SettingsConfigService
from .services import EtainaibleSyncService
from .serializers import SiteSerializer, SupplySerializer, AppSettingsSerializer

logger = logging.getLogger(__name__)


def site_list_view(request):
    query = request.GET.get('q', '').strip()
    sites = Site.objects.prefetch_related('supplies').order_by('name')
    if query:
        logger.info("Filtering sites by query: %s", query)
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
            logger.info("Loaded supplies for site_id=%s", site_id)
        except (ValueError, TypeError):
            logger.warning("Invalid site_id provided to supply_list_view: %s", site_id)
            supplies = []
    
    return render(request, 'sitesync/supply_list.html', {
        'supplies': supplies,
        'site_id': site_id,
    })


def manual_sync_view(request):
    """Trigger a manual sync and return to the site list."""
    if request.method != 'POST':
        return JsonResponse({
            'error': {
                'message': 'Method not allowed',
            }
        }, status=405)

    try:
        sync_service = EtainaibleSyncService()
        results = sync_service.sync_all()
        logger.info("Manual sync completed: %s", results)
        return redirect(f"{reverse('sitesync:site_list')}?sync=success")
    except Exception as exc:
        logger.exception("Manual sync failed")
        return JsonResponse({
            'error': {
                'message': 'Unable to complete sync',
                'details': str(exc),
            }
        }, status=500)


def settings_panel_view(request):
    """Display and update runtime configuration settings."""
    settings_instance = SettingsConfigService.get_settings()

    if request.method == 'POST':
        form = SettingsForm(request.POST, instance=settings_instance)
        if form.is_valid():
            logger.info("Updating application settings")
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
