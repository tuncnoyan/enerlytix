"""
Views for the sitesync app.
"""

import logging

from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from .models import (
    Site,
    Supply,
    AppSettings,
    ImportRun,
)
from .forms import SettingsForm
from .config_service import SettingsConfigService
from .services import EtainaibleSyncService
from .services import ConsumptionImportService, get_consumption_display_records
from .serializers import (
    SiteSerializer,
    SupplySerializer,
    AppSettingsSerializer,
    ConsumptionImportRequestSerializer,
    ConsumptionDisplayQuerySerializer,
    ImportRunSerializer,
)

logger = logging.getLogger(__name__)


def site_list_view(request):
    query = request.GET.get('q', '').strip()
    all_sites_qs = Site.objects.annotate(
        fiscal_meter_count=Count(
            'supplies',
            filter=Q(supplies__parent_account_id__isnull=True) | Q(supplies__parent_account_id=''),
            distinct=True,
        ),
        submeter_count=Count(
            'supplies',
            filter=~(Q(supplies__parent_account_id__isnull=True) | Q(supplies__parent_account_id='')),
            distinct=True,
        ),
        electricity_fiscal_count=Count(
            'supplies',
            filter=(Q(supplies__utility_type='electricity') & (Q(supplies__parent_account_id__isnull=True) | Q(supplies__parent_account_id=''))),
            distinct=True,
        ),
        electricity_submeter_count=Count(
            'supplies',
            filter=(Q(supplies__utility_type='electricity') & ~(Q(supplies__parent_account_id__isnull=True) | Q(supplies__parent_account_id=''))),
            distinct=True,
        ),
        gas_fiscal_count=Count(
            'supplies',
            filter=(Q(supplies__utility_type='gas') & (Q(supplies__parent_account_id__isnull=True) | Q(supplies__parent_account_id=''))),
            distinct=True,
        ),
        gas_submeter_count=Count(
            'supplies',
            filter=(Q(supplies__utility_type='gas') & ~(Q(supplies__parent_account_id__isnull=True) | Q(supplies__parent_account_id=''))),
            distinct=True,
        ),
        water_fiscal_count=Count(
            'supplies',
            filter=(Q(supplies__utility_type='water') & (Q(supplies__parent_account_id__isnull=True) | Q(supplies__parent_account_id=''))),
            distinct=True,
        ),
        water_submeter_count=Count(
            'supplies',
            filter=(Q(supplies__utility_type='water') & ~(Q(supplies__parent_account_id__isnull=True) | Q(supplies__parent_account_id=''))),
            distinct=True,
        ),
        other_fiscal_count=Count(
            'supplies',
            filter=(Q(supplies__utility_type='other') & (Q(supplies__parent_account_id__isnull=True) | Q(supplies__parent_account_id=''))),
            distinct=True,
        ),
        other_submeter_count=Count(
            'supplies',
            filter=(Q(supplies__utility_type='other') & ~(Q(supplies__parent_account_id__isnull=True) | Q(supplies__parent_account_id=''))),
            distinct=True,
        ),
    )
    all_supplies_qs = Supply.objects.all()
    site_count = all_sites_qs.count()
    fiscal_meter_count = all_supplies_qs.filter(
        Q(parent_account_id__isnull=True) | Q(parent_account_id='')
    ).count()
    submeter_count = all_supplies_qs.exclude(
        Q(parent_account_id__isnull=True) | Q(parent_account_id='')
    ).count()

    sites = all_sites_qs.prefetch_related('supplies').order_by('name')
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
    raw_site_ids = request.GET.getlist('site_ids')
    if len(raw_site_ids) == 1 and ',' in raw_site_ids[0]:
        raw_site_ids = [value.strip() for value in raw_site_ids[0].split(',')]

    if not raw_site_ids and site_id:
        raw_site_ids = [str(site_id)]

    selected_site_ids = []
    for raw_value in raw_site_ids:
        try:
            selected_site_ids.append(int(raw_value))
        except (TypeError, ValueError):
            continue

    selected_site_ids = list(dict.fromkeys(selected_site_ids))
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
    
    if selected_site_ids:
        try:
            selected_site_count = len(selected_site_ids)

            selected_sites = list(Site.objects.filter(id__in=selected_site_ids).order_by('name'))
            if selected_site_count == 1 and selected_sites:
                selected_site_name = selected_sites[0].name
            else:
                selected_site_name = f"{selected_site_count} sites selected"

            site_supplies = Supply.objects.filter(site_id__in=selected_site_ids)
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
            logger.info("Loaded supplies for site_ids=%s", selected_site_ids)

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
            logger.warning("Invalid site ids provided to supply_list_view: %s", raw_site_ids)
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


@api_view(['POST'])
def consumption_import_view(request):
    serializer = ConsumptionImportRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    service = ConsumptionImportService()
    payload = serializer.validated_data
    run = service.run(
        supply_external_ids=payload['supply_ids'],
        reporting_month=payload['reporting_month'],
        refresh_mode=payload.get('refresh_mode', True),
    )

    return Response({
        'import_run_id': run.id,
        'status': run.status,
        'supplies_count': run.affected_supply_count,
        'started_at': run.started_at,
        'completed_at': run.completed_at,
        'records_imported': run.records_imported,
        'records_failed': run.records_failed,
        'retry_count': run.retry_count,
        'error_details': run.error_details,
        'outcome_details': run.outcome_details,
    })


@api_view(['GET'])
def consumption_display_api_view(request):
    serializer = ConsumptionDisplayQuerySerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    validated = serializer.validated_data

    reporting_month = validated['reporting_month']
    supply_external_id = validated.get('supply_id')
    data_type = validated.get('data_type', 'monthly')

    rows = get_consumption_display_records(
        reporting_month=reporting_month,
        data_type=data_type,
        supply_external_id=supply_external_id,
    )

    return Response({
        'reporting_month': reporting_month,
        'data_type': data_type,
        'total_records': len(rows),
        'records': rows,
    })


def consumption_display_view(request):
    reporting_month = request.GET.get('reporting_month', '')
    supply_id = request.GET.get('supply_id', '')
    data_type = request.GET.get('data_type', 'monthly')

    context = {
        'reporting_month': reporting_month,
        'supply_id': supply_id,
        'data_type': data_type,
        'supplies': Supply.objects.all().order_by('name'),
    }
    return render(request, 'sitesync/consumption_display.html', context)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def import_run_detail_view(request, import_run_id):
    try:
        run = ImportRun.objects.get(id=import_run_id)
    except ImportRun.DoesNotExist:
        return Response({'detail': 'Import run not found'}, status=404)

    serializer = ImportRunSerializer(run)
    return Response(serializer.data)
