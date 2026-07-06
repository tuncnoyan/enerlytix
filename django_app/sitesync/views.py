"""
Views for the sitesync app.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone as datetime_timezone
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone as dj_timezone
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from .models import (
    Benchmark,
    Site,
    Supply,
    AppSettings,
    ImportRun,
    HalfHourlyConsumption,
    MonthlyConsumption,
    InvoiceCost,
)
from .forms import SettingsForm
from .config_service import SettingsConfigService
from .services import EtainaibleSyncService
from .services import ConsumptionImportService, get_consumption_display_records, month_start, reporting_month_bounds, shift_months
from .serializers import (
    SiteSerializer,
    SupplySerializer,
    BenchmarkSerializer,
    AppSettingsSerializer,
    ConsumptionImportRequestSerializer,
    ConsumptionDisplayQuerySerializer,
    ImportRunSerializer,
)

logger = logging.getLogger(__name__)

REPORT_UTILITY_ORDER = ['electricity', 'gas', 'water']
REPORT_UTILITY_LABELS = {
    'electricity': 'Electricity',
    'gas': 'Gas',
    'water': 'Water',
}


def _previous_complete_month_key():
    now = dj_timezone.localtime(dj_timezone.now())
    return shift_months(month_start(now.year, now.month), -1).strftime('%Y-%m')


def _month_label(month_key):
    return datetime.strptime(month_key + '-01', '%Y-%m-%d').strftime('%b %Y')


def _month_sequence(end_month, count=12):
    report_start, _ = reporting_month_bounds(end_month)
    start = shift_months(report_start, -(count - 1))
    return [shift_months(start, offset).strftime('%Y-%m') for offset in range(count)]


def _previous_year_month_key(month_key):
    report_start, _ = reporting_month_bounds(month_key)
    return shift_months(report_start, -12).strftime('%Y-%m')


def _decimal_to_float(value):
    return float(value) if value is not None else None


def _meter_number_for_supply(supply):
    # Prefer the supply name (meter number) over the device ID.
    return (supply.name or supply.device_id or supply.external_id or '').strip()


def _supply_label(supply, utility_counts):
    # Always use the supply's name field as the section label.
    return supply.name or supply.device_id or supply.external_id or supply.get_utility_type_display()


def _monthly_series_for_supply(supply, current_month_keys, previous_month_keys):
    current_rows = {
        row.canonical_month_key: row
        for row in MonthlyConsumption.objects.filter(supply=supply, canonical_month_key__in=current_month_keys)
    }
    previous_rows = {
        row.canonical_month_key: row
        for row in MonthlyConsumption.objects.filter(supply=supply, canonical_month_key__in=previous_month_keys)
    }
    benchmark_rows = {
        row.canonical_month_key: row
        for row in Benchmark.objects.filter(supply=supply, canonical_month_key__in=current_month_keys)
    }

    current_key = 'current_m3' if supply.utility_type == 'water' else 'current_kwh'
    previous_key = 'previous_year_m3' if supply.utility_type == 'water' else 'previous_year_kwh'
    benchmark_key = 'benchmark_m3' if supply.utility_type == 'water' else 'benchmark_kwh'

    table_rows = []
    current_values = []
    previous_values = []
    benchmark_values = []
    for index, month_key in enumerate(current_month_keys):
        current_row = current_rows.get(month_key)
        previous_row = previous_rows.get(previous_month_keys[index])
        benchmark_row = benchmark_rows.get(month_key)
        current_value = _decimal_to_float(current_row.consumption) if current_row else None
        previous_value = _decimal_to_float(previous_row.consumption) if previous_row else None
        benchmark_value = _decimal_to_float(benchmark_row.value) if benchmark_row else None
        variance = current_value - previous_value if current_value is not None and previous_value is not None else None
        relative_variance = (variance / previous_value * 100) if variance is not None and previous_value not in (None, 0) else None

        current_values.append(current_value)
        previous_values.append(previous_value)
        benchmark_values.append(benchmark_value)
        table_rows.append({
            'date': _month_label(month_key),
            'current': current_value,
            'previous_year': previous_value,
            'gross_variance': variance,
            'relative_variance': relative_variance,
        })

    return {
        'months': [
            {
                'key': month_key,
                'label': _month_label(month_key),
                'previous_year_key': previous_month_keys[index],
            }
            for index, month_key in enumerate(current_month_keys)
        ],
        current_key: current_values,
        previous_key: previous_values,
        benchmark_key: benchmark_values,
        'table': table_rows,
    }


def _hh_series_for_supply(supply, end_month):
    previous_month = _previous_year_month_key(end_month)
    current_rows = []
    previous_rows = []
    for item in HalfHourlyConsumption.objects.filter(
        supply=supply,
        canonical_month_key__in=[end_month, previous_month],
    ).order_by('source_period_start'):
        payload = {
            'ts': dj_timezone.localtime(item.source_period_start).isoformat(),
            'consumption_kwh': _decimal_to_float(item.consumption),
        }
        if item.canonical_month_key == end_month:
            current_rows.append(payload)
        elif item.canonical_month_key == previous_month:
            previous_rows.append(payload)

    if not current_rows and not previous_rows:
        return None

    return {
        'month': end_month,
        'current': current_rows,
        'previous_year': previous_rows,
    }


def _load_factor_for_supply(supply, end_month, hh_series):
    if supply.utility_type != 'electricity' or not hh_series or not hh_series['current']:
        return None

    hh_values = [Decimal(str(item['consumption_kwh'] or 0)) for item in hh_series['current']]
    max_halfhourly = max(hh_values)
    max_demand_kw = max_halfhourly / Decimal('0.5')
    monthly_kwh = sum(hh_values)
    report_start, report_end = reporting_month_bounds(end_month)
    days_in_month = (report_end - report_start).days
    denominator = max_demand_kw * Decimal(days_in_month) * Decimal('24')
    load_factor_pct = (monthly_kwh / denominator) * Decimal('100') if denominator else None

    return {
        'month': end_month,
        'monthly_kwh': _decimal_to_float(monthly_kwh),
        'max_demand_kw': _decimal_to_float(max_demand_kw),
        'load_factor_pct': _decimal_to_float(load_factor_pct),
        'available_capacity_kw': _decimal_to_float(supply.available_capacity),
        'halfhourly': hh_series['current'],
    }


def _day_night_for_supply(supply, end_month, hh_series):
    if supply.utility_type != 'electricity' or not hh_series or not hh_series['current']:
        return None

    records = []
    for item in hh_series['current']:
        local_ts = datetime.fromisoformat(item['ts'])
        records.append({
            'ts': item['ts'],
            'consumption_kwh': item['consumption_kwh'],
            'period': 'day' if 7 <= local_ts.hour < 23 else 'night',
        })

    return {
        'month': end_month,
        'day_start': '07:00',
        'day_end': '23:00',
        'records': records,
    }


def _weekday_weekend_for_supply(supply, end_month, hh_series):
    if supply.utility_type not in {'electricity', 'gas'} or not hh_series or not hh_series['current']:
        return None, None

    grouped = defaultdict(list)
    for item in hh_series['current']:
        local_ts = datetime.fromisoformat(item['ts'])
        grouped[local_ts.date().isoformat()].append({
            'time': local_ts.strftime('%H:%M'),
            'consumption_kwh': item['consumption_kwh'],
        })

    weekday_days = []
    weekend_days = []
    for date_key in sorted(grouped):
        local_date = datetime.fromisoformat(date_key)
        payload = {
            'date': date_key,
            'day_name': local_date.strftime('%A'),
            'records': sorted(grouped[date_key], key=lambda row: row['time']),
        }
        if local_date.weekday() >= 5:
            weekend_days.append(payload)
        else:
            weekday_days.append(payload)

    return (
        {'month': end_month, 'days': weekday_days},
        {'month': end_month, 'days': weekend_days},
    )


def _overview_for_site(site, report_start, report_end):
    invoice_rows = InvoiceCost.objects.filter(
        supply__site=site,
        source_period_end__gte=report_start,
        source_period_end__lte=report_end,  # inclusive: catches invoices ending exactly on the boundary (exclusive end-date pattern)
        supply__utility_type__in=REPORT_UTILITY_ORDER,
    ).values('supply_id', 'supply__utility_type', 'supply__device_id', 'supply__name').annotate(total_cost=Sum('cost'))

    totals = defaultdict(Decimal)
    meter_numbers = defaultdict(list)
    per_meter_rows = []
    for row in invoice_rows:
        utility_type = row['supply__utility_type']
        totals[utility_type] += row['total_cost'] or Decimal('0')
        meter_number = row.get('supply__device_id') or row.get('supply__name') or str(row['supply_id'])
        if meter_number not in meter_numbers[utility_type]:
            meter_numbers[utility_type].append(meter_number)
        per_meter_rows.append({
            'utility_type': utility_type,
            'label': REPORT_UTILITY_LABELS.get(utility_type, utility_type.capitalize()),
            'meter_number': meter_number,
            'total_cost': _decimal_to_float(row['total_cost'] or Decimal('0')),
        })

    total_cost = sum(totals.values(), Decimal('0'))
    by_utility = []
    for utility_type in REPORT_UTILITY_ORDER:
        utility_total = totals.get(utility_type, Decimal('0'))
        percentage = (utility_total / total_cost) * Decimal('100') if total_cost else None
        by_utility.append({
            'utility_type': utility_type,
            'label': REPORT_UTILITY_LABELS[utility_type],
            'total_cost': _decimal_to_float(utility_total),
            'percentage': _decimal_to_float(percentage),
            'meter_numbers': meter_numbers.get(utility_type, []),
        })

    order_map = {ut: i for i, ut in enumerate(REPORT_UTILITY_ORDER)}
    per_meter_rows.sort(key=lambda r: order_map.get(r['utility_type'], 99))

    return {
        'total_cost': _decimal_to_float(total_cost),
        'by_utility': by_utility,
        'per_meter': per_meter_rows,
    }


def _report_payload(site, end_month, supply_external_ids=None):
    current_month_keys = _month_sequence(end_month, 12)
    previous_month_keys = [_previous_year_month_key(month_key) for month_key in current_month_keys]
    report_start, report_end = reporting_month_bounds(end_month)
    report_start = shift_months(report_start, -11)

    supplies = list(site.supplies.filter(
        utility_type__in=REPORT_UTILITY_ORDER,
        # Only include fiscal meters; exclude sub-meters
    ).filter(
        Q(parent_account_id__isnull=True) | Q(parent_account_id='')
    ).filter(
        **({'external_id__in': supply_external_ids} if supply_external_ids else {})
    ).order_by('utility_type', 'name', 'id'))
    utility_counts = defaultdict(int)
    for supply in supplies:
        utility_counts[supply.utility_type] += 1

    payload_supplies = []
    for supply in supplies:
        monthly = _monthly_series_for_supply(supply, current_month_keys, previous_month_keys)
        hh_series = _hh_series_for_supply(supply, end_month)
        load_factor = _load_factor_for_supply(supply, end_month, hh_series)
        day_night = _day_night_for_supply(supply, end_month, hh_series)
        weekday_comparison, weekend_comparison = _weekday_weekend_for_supply(supply, end_month, hh_series)

        payload_supplies.append({
            'id': supply.id,
            'utility_type': supply.utility_type,
            'utility_type_display': supply.get_utility_type_display(),
            'label': _supply_label(supply, utility_counts),
            'meter_number': _meter_number_for_supply(supply),
            'available_capacity_kw': _decimal_to_float(supply.available_capacity),
            'monthly': monthly,
            'load_factor': load_factor,
            'hh_comparison': hh_series,
            'day_night': day_night,
            'weekday_comparison': weekday_comparison,
            'weekend_comparison': weekend_comparison,
        })

    return {
        'site': {
            'id': site.id,
            'external_id': site.external_id,
            'name': site.name,
            'description': site.description,
        },
        'reporting_period': {
            'end_month': end_month,
            'start_month': current_month_keys[0],
            'previous_year_start_month': previous_month_keys[0],
            'report_start': report_start.isoformat(),
            'report_end': report_end.isoformat(),
            'months': [
                {
                    'key': month_key,
                    'label': _month_label(month_key),
                    'previous_year_key': previous_month_keys[index],
                }
                for index, month_key in enumerate(current_month_keys)
            ],
        },
        'overview': _overview_for_site(site, report_start, report_end),
        'supplies': payload_supplies,
    }


def report_view(request):
    site_id = request.GET.get('site_id', '').strip()
    end_month = (request.GET.get('end_month', '') or '').strip() or _previous_complete_month_key()
    supply_ids = request.GET.get('supply_ids', '').strip()
    site = None
    if site_id:
        try:
            site = Site.objects.get(id=int(site_id))
        except (Site.DoesNotExist, TypeError, ValueError):
            site = None

    return render(request, 'sitesync/report.html', {
        'report_site': site,
        'site_id': site.id if site else site_id,
        'end_month': end_month,
        'supply_ids': supply_ids,
    })


@api_view(['GET'])
def report_data_api_view(request):
    raw_site_id = request.query_params.get('site_id')
    end_month = (request.query_params.get('end_month') or '').strip()
    supply_ids_raw = (request.query_params.get('supply_ids') or '').strip()
    supply_external_ids = [s.strip() for s in supply_ids_raw.split(',') if s.strip()] if supply_ids_raw else []

    if not raw_site_id or not end_month:
        return Response({'detail': 'site_id and end_month are required'}, status=400)

    try:
        site_id = int(raw_site_id)
    except (TypeError, ValueError):
        return Response({'detail': 'site_id must be an integer'}, status=400)

    try:
        reporting_month_bounds(end_month)
    except Exception:  # pylint: disable=broad-except
        return Response({'detail': 'end_month must be in YYYY-MM format'}, status=400)

    site = get_object_or_404(Site, id=site_id)
    if not site.supplies.exists():
        return Response({
            'site': {
                'id': site.id,
                'external_id': site.external_id,
                'name': site.name,
                'description': site.description,
            },
            'reporting_period': {
                'end_month': end_month,
                'start_month': _month_sequence(end_month, 12)[0],
                'previous_year_start_month': _month_sequence(_previous_year_month_key(end_month), 12)[0],
                'months': [],
            },
            'overview': {
                'total_cost': 0,
                'by_utility': [],
            },
            'supplies': [],
        })

    return Response(_report_payload(site, end_month, supply_external_ids or None))


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
@permission_classes([AllowAny])
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
    supply_ids_raw = validated.get('supply_ids')
    data_type = validated.get('data_type', 'monthly')

    supply_external_ids = []
    if supply_ids_raw:
        supply_external_ids = [item.strip() for item in supply_ids_raw.split(',') if item.strip()]

    rows = get_consumption_display_records(
        reporting_month=reporting_month,
        data_type=data_type,
        supply_external_id=supply_external_id,
        supply_external_ids=supply_external_ids,
    )

    # Tell the client if the returned data falls outside the requested period
    # (e.g. API returned only historical records, not the selected window).
    in_window = True
    if data_type == 'invoice' and rows:
        from .services import get_invoice_window  # local import avoids circular risk
        window_start, window_end = get_invoice_window(reporting_month)
        in_window = any(
            r['source_period_end'] is not None
            and r['source_period_end'] >= window_start
            and r['source_period_end'] <= window_end
            for r in rows
        )

    return Response({
        'reporting_month': reporting_month,
        'data_type': data_type,
        'total_records': len(rows),
        'in_window': in_window,
        'records': rows,
    })


def consumption_display_view(request):
    reporting_month = request.GET.get('reporting_month', '')
    supply_id = request.GET.get('supply_id', '')
    supply_ids = request.GET.get('supply_ids', '')
    data_type = request.GET.get('data_type', 'monthly')

    context = {
        'reporting_month': reporting_month,
        'supply_id': supply_id,
        'supply_ids': supply_ids,
        'data_type': data_type,
        'sites': Site.objects.order_by('name'),
        'site_count': Site.objects.count(),
        'fiscal_meter_count': Supply.objects.filter(
            Q(parent_account_id__isnull=True) | Q(parent_account_id='')
        ).count(),
        'submeter_count': Supply.objects.exclude(
            Q(parent_account_id__isnull=True) | Q(parent_account_id='')
        ).count(),
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
