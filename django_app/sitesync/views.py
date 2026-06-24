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
    all_sites_qs = Site.objects.all()
    all_supplies_qs = Supply.objects.all()
    site_count = all_sites_qs.count()
    fiscal_meter_count = all_supplies_qs.filter(
        Q(parent_account_id__isnull=True) | Q(parent_account_id='')
    ).count()
    submeter_count = all_supplies_qs.exclude(
        Q(parent_account_id__isnull=True) | Q(parent_account_id='')
    ).count()

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
        'site_count': site_count,
        'fiscal_meter_count': fiscal_meter_count,
        'submeter_count': submeter_count,
    })


def supply_list_view(request):
    """Display supplies for a selected site."""
    site_id = request.GET.get('site_id')
    utility_type = (request.GET.get('utility_type') or 'all').strip().lower()
    meter_type = (request.GET.get('meter_type') or 'all').strip().lower()
    supplies = []
    fiscal_supplies = []
    orphan_submeters = []
    filtered_fiscal_count = 0
    filtered_submeter_count = 0
    selected_site_count = 0
    selected_site_name = ''

    utility_label_map = {
        'all': 'All',
        'electricity': 'Electricity',
        'gas': 'Gas',
        'water': 'Water',
        'other': 'Other',
    }
    meter_label_map = {
        'all': 'All',
        'fiscal': 'Fiscal',
        'sub': 'Submeter',
    }
    
    if site_id:
        try:
            selected_site_id = int(site_id)
            selected_site_count = 1

            selected_site = Site.objects.filter(id=selected_site_id).first()
            selected_site_name = selected_site.name if selected_site else str(site_id)

            site_supplies = Supply.objects.filter(site_id=selected_site_id)
            filtered_supplies = site_supplies

            if utility_type in {'electricity', 'gas', 'water', 'other'}:
                filtered_supplies = filtered_supplies.filter(utility_type=utility_type)

            if meter_type == 'fiscal':
                filtered_supplies = filtered_supplies.filter(
                    Q(parent_account_id__isnull=True) | Q(parent_account_id='')
                )
            elif meter_type == 'sub':
                filtered_supplies = filtered_supplies.exclude(
                    Q(parent_account_id__isnull=True) | Q(parent_account_id='')
                )

            supplies = filtered_supplies.order_by('name')
            logger.info("Loaded supplies for site_id=%s", site_id)

            filtered_fiscal_count = supplies.filter(
                Q(parent_account_id__isnull=True) | Q(parent_account_id='')
            ).count()
            filtered_submeter_count = supplies.exclude(
                Q(parent_account_id__isnull=True) | Q(parent_account_id='')
            ).count()

            all_site_supplies = list(site_supplies.order_by('name'))
            all_supplies_by_external_id = {
                supply.external_id: supply for supply in all_site_supplies
            }
            children_by_parent = {}
            for supply in supplies:
                parent_id = (supply.parent_account_id or '').strip()
                if parent_id:
                    children_by_parent.setdefault(parent_id, []).append(supply)

            for submeter_list in children_by_parent.values():
                submeter_list.sort(key=lambda item: (item.name or '').lower())

            if meter_type == 'sub':
                fiscal_seen = set()
                for submeter in supplies:
                    parent_id = (submeter.parent_account_id or '').strip()
                    if not parent_id:
                        continue
                    parent_supply = all_supplies_by_external_id.get(parent_id)
                    if not parent_supply:
                        continue
                    if parent_supply.external_id in fiscal_seen:
                        continue
                    fiscal_seen.add(parent_supply.external_id)
                    fiscal_supplies.append({
                        'supply': parent_supply,
                        'submeters': children_by_parent.get(parent_supply.external_id, []),
                    })
            else:
                for supply in supplies:
                    parent_id = (supply.parent_account_id or '').strip()
                    if not parent_id:
                        fiscal_supplies.append({
                            'supply': supply,
                            'submeters': [] if meter_type == 'fiscal' else children_by_parent.get(supply.external_id, []),
                        })

            fiscal_supplies.sort(key=lambda item: (item['supply'].name or '').lower())

            # Keep visibility for malformed imports where parentAccountId points to
            # an account outside the selected site.
            orphan_submeters = [
                supply
                for supply in supplies
                if (supply.parent_account_id or '').strip()
                and (supply.parent_account_id or '').strip() not in all_supplies_by_external_id
            ]
            orphan_submeters.sort(key=lambda item: (item.name or '').lower())
        except (ValueError, TypeError):
            logger.warning("Invalid site_id provided to supply_list_view: %s", site_id)
            supplies = []
    
    return render(request, 'sitesync/supply_list.html', {
        'supplies': supplies,
        'fiscal_supplies': fiscal_supplies,
        'orphan_submeters': orphan_submeters,
        'site_id': site_id,
        'selected_site_count': selected_site_count,
        'selected_site_name': selected_site_name,
        'filtered_fiscal_count': filtered_fiscal_count,
        'filtered_submeter_count': filtered_submeter_count,
        'selected_utility_type': utility_type,
        'selected_meter_type': meter_type,
        'selected_utility_label': utility_label_map.get(utility_type, 'All'),
        'selected_meter_label': meter_label_map.get(meter_type, 'All'),
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
        if (results.get('sites_created', 0) + results.get('sites_updated', 0)) == 0:
            logger.warning("Manual sync completed but no sites were persisted")
            return redirect(f"{reverse('sitesync:site_list')}?sync=empty")
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
