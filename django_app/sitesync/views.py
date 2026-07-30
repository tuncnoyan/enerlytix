"""
Views for the sitesync app.
"""

import logging
import json
from collections import defaultdict
from datetime import datetime, timezone as datetime_timezone
from decimal import Decimal, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
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
    CapacityUploadRun,
    Site,
    Supply,
    AppSettings,
    ImportRun,
    HalfHourlyConsumption,
    MonthlyConsumption,
    InvoiceCost,
    MonthlyReport,
    MonthlyReportVersion,
    Invitation,
)
from .forms import AccountActionForm, CapacityUploadForm, InvitationForm, SettingsForm
from .config_service import SettingsConfigService
from .services import EtainaibleSyncService
from .services import (
    build_report_cover_set,
    carry_forward_comments_from_previous_final,
    ConsumptionImportService,
    create_report_version,
    get_capacity_lookup_by_meter_codes,
    get_or_create_monthly_report,
    get_consumption_display_records,
    get_previous_month_final_version,
    import_capacity_upload,
    month_start,
    normalize_esight_meter_code,
    normalize_reporting_month,
    reporting_month_bounds,
    shift_months,
)
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


def _site_floor_area_sqm(site):
    if site.floor_area in (None, ''):
        return None
    if site.floor_area <= 0:
        return None
    unit = (site.floor_area_unit or '').strip().lower()
    if unit == 'sqft':
        return (site.floor_area * Decimal('0.09290304')).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
    return site.floor_area


def _monthly_benchmark_value(site, utility_type, settings_instance):
    floor_area_sqm = _site_floor_area_sqm(site)
    if floor_area_sqm is None:
        return None

    if utility_type == 'electricity':
        intensity = settings_instance.electricity_benchmark_intensity
    elif utility_type == 'gas':
        intensity = settings_instance.gas_benchmark_intensity
    elif utility_type == 'water':
        intensity = settings_instance.water_benchmark_intensity
    else:
        return None

    if intensity is None or intensity <= 0:
        return None

    annual_total = intensity * floor_area_sqm
    return (annual_total / Decimal('12')).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)


def _monthly_series_for_supply(supply, current_month_keys, previous_month_keys, settings_instance):
    current_rows = {
        row.canonical_month_key: row
        for row in MonthlyConsumption.objects.filter(supply=supply, canonical_month_key__in=current_month_keys)
    }
    previous_rows = {
        row.canonical_month_key: row
        for row in MonthlyConsumption.objects.filter(supply=supply, canonical_month_key__in=previous_month_keys)
    }
    current_key = 'current_m3' if supply.utility_type == 'water' else 'current_kwh'
    previous_key = 'previous_year_m3' if supply.utility_type == 'water' else 'previous_year_kwh'
    benchmark_key = 'benchmark_m3' if supply.utility_type == 'water' else 'benchmark_kwh'
    monthly_benchmark_value = _monthly_benchmark_value(supply.site, supply.utility_type, settings_instance)

    table_rows = []
    current_values = []
    previous_values = []
    benchmark_values = []
    for index, month_key in enumerate(current_month_keys):
        current_row = current_rows.get(month_key)
        previous_row = previous_rows.get(previous_month_keys[index])
        current_value = _decimal_to_float(current_row.consumption) if current_row else None
        previous_value = _decimal_to_float(previous_row.consumption) if previous_row else None
        benchmark_value = _decimal_to_float(monthly_benchmark_value)
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


def _load_factor_for_supply(supply, end_month, hh_series, available_capacity_kva=None):
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
        'available_capacity_kva': _decimal_to_float(available_capacity_kva),
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



def _report_editor_context(raw_site_id, raw_end_month, raw_reporting_month, raw_supply_ids):
    """Build common context for the report editor view."""
    site_id = (raw_site_id or '').strip()
    supply_ids = (raw_supply_ids or '').strip()
    end_month = normalize_reporting_month(raw_end_month, raw_reporting_month)
    site = None
    if site_id:
        try:
            site = Site.objects.get(id=int(site_id))
        except (Site.DoesNotExist, TypeError, ValueError):
            site = None

    monthly_report = None
    initial_comments = {}
    reference_comment_keys = []
    if site is not None:
        monthly_report = MonthlyReport.objects.filter(site=site, reporting_month=end_month).first()
        if monthly_report and monthly_report.current_version:
            for comment in monthly_report.current_version.comments.all().order_by('visual_key'):
                initial_comments[comment.visual_key] = comment.text
                if comment.is_reference_copy:
                    reference_comment_keys.append(comment.visual_key)
        else:
            # Brand-new report for this site/month: preview the previous
            # month's final comments as reference copies before any save,
            # per the report-workflow contract (carry-forward on open).
            previous_final = get_previous_month_final_version(site, end_month)
            if previous_final:
                for comment in previous_final.comments.all().order_by('visual_key'):
                    initial_comments[comment.visual_key] = comment.text
                    reference_comment_keys.append(comment.visual_key)

    report_context = {
        'siteId': site.id if site else site_id,
        'endMonth': end_month,
        'siteName': site.name if site else '',
        'supplyIds': supply_ids,
        'initialComments': initial_comments,
        'referenceCommentKeys': reference_comment_keys,
        'coverDefaults': build_report_cover_set(site.name if site else '', end_month),
    }

    return {
        'report_site': site,
        'site_id': site.id if site else site_id,
        'end_month': end_month,
        'supply_ids': supply_ids,
        'monthly_report': monthly_report,
        'initial_comments_json': json.dumps(initial_comments),
        'reference_comment_keys_json': json.dumps(reference_comment_keys),
        'report_context': report_context,
    }


def _saved_reports_query(site_id=None):
    """Return saved reports queryset for list rendering."""
    qs = MonthlyReport.objects.select_related('site').order_by('-reporting_month', 'site__name')
    if site_id:
        qs = qs.filter(site_id=site_id)
    return qs

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
    settings_instance = SettingsConfigService.get_settings()

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

    meter_codes = [normalize_esight_meter_code(supply.device_id) for supply in supplies if supply.device_id]
    capacity_lookup = get_capacity_lookup_by_meter_codes(meter_codes)

    payload_supplies = []
    for supply in supplies:
        meter_code = normalize_esight_meter_code(supply.device_id)
        available_capacity_kva = capacity_lookup.get(meter_code) if meter_code else None
        monthly = _monthly_series_for_supply(supply, current_month_keys, previous_month_keys, settings_instance)
        hh_series = _hh_series_for_supply(supply, end_month)
        load_factor = _load_factor_for_supply(supply, end_month, hh_series, available_capacity_kva)
        day_night = _day_night_for_supply(supply, end_month, hh_series)
        weekday_comparison, weekend_comparison = _weekday_weekend_for_supply(supply, end_month, hh_series)

        payload_supplies.append({
            'id': supply.id,
            'external_id': supply.external_id,
            'utility_type': supply.utility_type,
            'utility_type_display': supply.get_utility_type_display(),
            'label': _supply_label(supply, utility_counts),
            'meter_number': _meter_number_for_supply(supply),
            'available_capacity_kva': _decimal_to_float(available_capacity_kva),
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
        'cover_defaults': build_report_cover_set(site.name, end_month, payload_supplies),
        'supplies': payload_supplies,
    }


def report_view(request):
    if request.method == 'POST':
        raw_site_id = (request.POST.get('site_id') or '').strip()
        save_mode = (request.POST.get('save_mode') or 'draft').strip().lower()
        confirm_final_edit = (request.POST.get('confirm_final_edit') or '').strip().lower() in {'1', 'true', 'yes'}
        end_month = normalize_reporting_month(
            request.POST.get('end_month', ''),
            request.POST.get('reporting_month', ''),
        )

        try:
            site = Site.objects.get(id=int(raw_site_id))
        except (Site.DoesNotExist, TypeError, ValueError):
            return JsonResponse({'detail': 'site_id must be a valid integer'}, status=400)

        comments_payload = {}
        comments_raw = (request.POST.get('comments') or '').strip()
        if comments_raw:
            try:
                parsed = json.loads(comments_raw)
                if isinstance(parsed, dict):
                    comments_payload = {str(k): str(v or '') for k, v in parsed.items()}
            except json.JSONDecodeError:
                return JsonResponse({'detail': 'comments must be valid JSON object'}, status=400)

        report = get_or_create_monthly_report(site, end_month)
        created_first_version = report.current_version is None
        if save_mode == 'final':
            if report.current_status == MonthlyReport.STATUS_FINAL and not confirm_final_edit:
                return JsonResponse({
                    'detail': 'This report is already final. Confirm before editing.',
                    'warning_required': True,
                }, status=409)
            version_kind = (
                MonthlyReportVersion.KIND_REPLACEMENT_FINAL
                if report.current_status == MonthlyReport.STATUS_FINAL
                else MonthlyReportVersion.KIND_FINAL
            )
        else:
            version_kind = MonthlyReportVersion.KIND_DRAFT

        version = create_report_version(
            report=report,
            version_kind=version_kind,
            comments=comments_payload,
            derived_from_version=report.current_version,
        )

        copied_reference_comments = 0
        if save_mode == 'draft' and created_first_version:
            copied_reference_comments = carry_forward_comments_from_previous_final(report, version)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'report_id': str(report.id),
                'version_id': str(version.id),
                'status': report.current_status,
                'reporting_month': report.reporting_month,
                'copied_reference_comments': copied_reference_comments,
            })

        return redirect(f"{reverse('sitesync:report')}?site_id={site.id}&end_month={end_month}")

    context = _report_editor_context(
        request.GET.get('site_id', ''),
        request.GET.get('end_month', ''),
        request.GET.get('reporting_month', ''),
        request.GET.get('supply_ids', ''),
    )
    context['is_admin'] = _user_is_admin(getattr(request, 'user', None))
    return render(request, 'sitesync/report.html', context)


def saved_reports_view(request):
    """Entry point for the saved reports browser with team-based access scoping."""
    from .services import get_accessible_reports
    from .models import UserTeamAssignment
    import json
    
    # For anonymous users, show all reports (backward compatibility)
    # For authenticated users without teams, show empty state
    if not request.user.is_authenticated:
        # Anonymous users see all reports
        accessible_reports = MonthlyReport.objects.all()
    else:
        # Check if user has any team assignments
        user_has_teams = UserTeamAssignment.objects.filter(user=request.user).exists()
        
        # show empty state for unassigned authenticated user
        if not user_has_teams and not (request.user.is_staff or request.user.is_superuser):
            context = {
                'show_empty_state': True,
                'user_has_teams': False,
                'is_admin': _user_is_admin(request.user),
            }
            return render(request, 'sitesync/saved_reports.html', context)
        
        # Authenticated user with teams or admin - get accessible reports
        accessible_reports = get_accessible_reports(request.user)
    
    user_has_teams = (request.user.is_authenticated and 
                      UserTeamAssignment.objects.filter(user=request.user).exists())
    
    raw_site_id = (request.GET.get('site_id') or '').strip()
    site_id = None
    if raw_site_id:
        try:
            site_id = int(raw_site_id)
        except (TypeError, ValueError):
            return JsonResponse({'detail': 'site_id must be an integer'}, status=400)
    
    # Filter by site if provided
    if site_id:
        accessible_reports = accessible_reports.filter(site_id=site_id)
    
    # Order reports
    accessible_reports = accessible_reports.select_related('site').order_by('-reporting_month', 'site__name')

    reports_payload = [
        {
            'id': str(report.id),
            'site_id': report.site_id,
            'site_name': report.site.name,
            'reporting_month': report.reporting_month,
            'status': report.current_status,
            'updated_at': report.updated_at.isoformat(),
            'open_url': f"{reverse('sitesync:report')}?site_id={report.site_id}&end_month={report.reporting_month}",
        }
        for report in accessible_reports
    ]
    
    wants_json = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('format') == 'json'
    if wants_json:
        return JsonResponse({'reports': reports_payload})

    # Check for recent team assignment to show welcome message
    show_welcome = False
    welcome_team_name = None
    if user_has_teams:
        recent_assignment = UserTeamAssignment.objects.filter(
            user=request.user
        ).order_by('-assigned_at').first()
        if recent_assignment:
            # Show welcome if assignment is less than 1 hour old
            from datetime import timedelta
            from django.utils import timezone
            one_hour_ago = timezone.now() - timedelta(hours=1)
            if recent_assignment.assigned_at > one_hour_ago:
                show_welcome = True
                welcome_team_name = recent_assignment.team.name

    return render(request, 'sitesync/saved_reports.html', {
        'reports_json': json.dumps(reports_payload),
        'selected_site_id': site_id,
        'user_has_teams': user_has_teams,
        'show_empty_state': False,
        'show_welcome': show_welcome,
        'welcome_team_name': welcome_team_name,
        'is_admin': _user_is_admin(getattr(request, 'user', None)),
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
            'cover_defaults': build_report_cover_set(site.name, end_month, []),
            'supplies': [],
        })

    return Response(_report_payload(site, end_month, supply_external_ids or None))


@login_required(login_url='/login/')
def profile_view(request):
    return render(request, 'sitesync/profile.html', {
        'user': request.user,
        'is_admin': _user_is_admin(getattr(request, 'user', None)),
    })


@login_required(login_url='/login/')
def user_admin_view(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return redirect('sitesync:profile')

    invitation_form = InvitationForm()
    action_form = AccountActionForm()
    users = get_user_model().objects.order_by('username')
    invitations = Invitation.objects.order_by('-created_at')

    if request.method == 'POST':
        if 'create_invitation' in request.POST:
            invitation_form = InvitationForm(request.POST)
            if invitation_form.is_valid():
                Invitation.objects.create(
                    email=invitation_form.cleaned_data['email'],
                    invited_by=request.user,
                    expires_at=dj_timezone.now() + dj_timezone.timedelta(days=7),
                )
                invitation_form = InvitationForm()
        elif 'account_action' in request.POST:
            action_form = AccountActionForm(request.POST)
            if action_form.is_valid():
                target_id = request.POST.get('user_id')
                target_user = get_user_model().objects.filter(id=target_id).first()
                if target_user is not None:
                    action = action_form.cleaned_data['action']
                    if action == 'enable':
                        target_user.is_active = True
                        target_user.save(update_fields=['is_active'])
                    elif action == 'disable':
                        target_user.is_active = False
                        target_user.save(update_fields=['is_active'])
                    elif action == 'reset_password':
                        target_user.set_password('TempPassword123!')
                        target_user.save(update_fields=['password'])
                    elif action == 'delete':
                        target_user.delete()
                    if action_form.cleaned_data.get('new_username'):
                        target_user.username = action_form.cleaned_data['new_username']
                        target_user.save(update_fields=['username'])

    return render(request, 'sitesync/user_admin.html', {
        'users': users,
        'invitations': invitations,
        'invitation_form': invitation_form,
        'action_form': action_form,
        'is_admin': _user_is_admin(getattr(request, 'user', None)),
    })


def password_reset_view(request):
    _is_admin = _user_is_admin(getattr(request, 'user', None))
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip()
        if email:
            user_model = get_user_model()
            user_model.objects.filter(email=email).exists()
        return render(request, 'sitesync/password_reset.html', {
            'page_title': 'Reset password',
            'submitted': True,
            'is_admin': _is_admin,
        })

    return render(request, 'sitesync/password_reset.html', {
        'page_title': 'Reset password',
        'submitted': False,
        'is_admin': _is_admin,
    })


def accept_invitation_view(request, invitation_id):
    invitation = Invitation.objects.filter(id=invitation_id).first()
    if invitation is None:
        return render(request, 'sitesync/invite_accept.html', {'error': 'Invitation not found.'})
    if not invitation.is_valid():
        return render(request, 'sitesync/invite_accept.html', {'error': 'This invitation is no longer valid.'})

    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = (request.POST.get('password') or '').strip()
        if not username or not password:
            return render(request, 'sitesync/invite_accept.html', {
                'invitation': invitation,
                'error': 'Please provide a username and password.',
            })
        user_model = get_user_model()
        if user_model.objects.filter(username__iexact=username).exists():
            return render(request, 'sitesync/invite_accept.html', {
                'invitation': invitation,
                'error': 'That username is already taken.',
            })
        user = user_model.objects.create_user(username=username, email=invitation.email, password=password)
        invitation.accept()
        return render(request, 'sitesync/invite_accept.html', {
            'invitation': invitation,
            'success': True,
            'user': user,
        })

    return render(request, 'sitesync/invite_accept.html', {'invitation': invitation})


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
        'is_admin': _user_is_admin(getattr(request, 'user', None)),
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
        sync_activity = (
            results.get('sites_created', 0)
            + results.get('sites_updated', 0)
            + results.get('sites_deleted', 0)
            + results.get('supplies_created', 0)
            + results.get('supplies_updated', 0)
            + results.get('supplies_deleted', 0)
        )
        if sync_activity == 0:
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
    capacity_upload_result = None
    latest_capacity_run = CapacityUploadRun.objects.order_by('-uploaded_at').first()

    if request.method == 'POST':
        if 'capacity_upload_submit' in request.POST:
            form = SettingsForm(instance=settings_instance)
            capacity_form = CapacityUploadForm(request.POST, request.FILES)
            if capacity_form.is_valid():
                capacity_upload_result = import_capacity_upload(capacity_form.cleaned_data['capacity_upload_file'])
                latest_capacity_run = capacity_upload_result.get('run')
            else:
                upload_errors = []
                for field_errors in capacity_form.errors.values():
                    upload_errors.extend(field_errors)
                capacity_upload_result = {
                    'status': CapacityUploadRun.STATUS_FAILED,
                    'total_rows': 0,
                    'accepted_rows': 0,
                    'rejected_rows': 0,
                    'errors': [str(error) for error in upload_errors],
                    'run': None,
                }
        else:
            form = SettingsForm(request.POST, instance=settings_instance)
            if form.is_valid():
                logger.info("Updating application settings")
                SettingsConfigService.update_settings(form)
            capacity_form = CapacityUploadForm()
    else:
        form = SettingsForm(instance=settings_instance)
        capacity_form = CapacityUploadForm()

    if capacity_upload_result is not None:
        capacity_upload_status = capacity_upload_result.get('status')
        capacity_upload_total_rows = capacity_upload_result.get('total_rows', 0)
        capacity_upload_accepted_rows = capacity_upload_result.get('accepted_rows', 0)
        capacity_upload_rejected_rows = capacity_upload_result.get('rejected_rows', 0)
        capacity_upload_errors = capacity_upload_result.get('errors', [])
    elif latest_capacity_run is not None:
        capacity_upload_status = latest_capacity_run.status
        capacity_upload_total_rows = latest_capacity_run.total_rows
        capacity_upload_accepted_rows = latest_capacity_run.accepted_rows
        capacity_upload_rejected_rows = latest_capacity_run.rejected_rows
        capacity_upload_errors = latest_capacity_run.error_summary or []
    else:
        capacity_upload_status = ''
        capacity_upload_total_rows = 0
        capacity_upload_accepted_rows = 0
        capacity_upload_rejected_rows = 0
        capacity_upload_errors = []

    return render(request, 'sitesync/settings_panel.html', {
        'form': form,
        'capacity_form': capacity_form,
        'settings': settings_instance,
        'save_success': request.method == 'POST' and form.is_valid(),
        'capacity_upload_status': capacity_upload_status,
        'capacity_upload_total_rows': capacity_upload_total_rows,
        'capacity_upload_accepted_rows': capacity_upload_accepted_rows,
        'capacity_upload_rejected_rows': capacity_upload_rejected_rows,
        'capacity_upload_errors': capacity_upload_errors,
        'latest_capacity_run': latest_capacity_run,
        'is_admin': _user_is_admin(getattr(request, 'user', None)),
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
        'is_admin': _user_is_admin(getattr(request, 'user', None)),
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


# Team Management Views (Phase 4)

@login_required
def team_detail_view(request, team_id):
    """
    GET: Return team details and member list.
    POST: Update team properties (admin/manager only).
    """
    from .models import Team, UserTeamAssignment
    from .forms import TeamForm
    
    try:
        team = Team.objects.get(id=team_id)
    except Team.DoesNotExist:
        return JsonResponse({'error': 'Team not found'}, status=404)
    
    # Check access: user must be admin, manager, or assigned to team
    is_team_admin = (
        request.user.is_staff or request.user.is_superuser or
        request.user.role_assignments.filter(role_name='admin').exists()
    )
    is_team_manager = (
        team.manager_id == request.user.id or
        request.user.role_assignments.filter(role_name='manager').exists()
    )
    is_team_member = UserTeamAssignment.objects.filter(
        user=request.user, team=team
    ).exists()
    
    if not (is_team_admin or is_team_manager or is_team_member):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    team_form = TeamForm(instance=team) if hasattr(TeamForm, 'Meta') else TeamForm(initial={
        'name': team.name,
        'level': team.level,
        'parent_team': team.parent_team,
        'manager': team.manager,
        'team_lead': team.team_lead,
    })

    can_edit = is_team_admin or is_team_manager

    if request.method == 'POST':
        if not can_edit:
            return JsonResponse({'error': 'Permission denied'}, status=403)

        action = request.POST.get('action', 'update_team')

        if action == 'add_sub_team':
            sub_team_id = request.POST.get('sub_team_id')

            if not sub_team_id:
                messages.error(request, 'Please select a team to add as a sub-team.')
                return redirect('sitesync:team_detail', team_id=team.id)

            try:
                sub_team = Team.objects.get(id=sub_team_id)
            except Team.DoesNotExist:
                messages.error(request, 'Selected team was not found.')
                return redirect('sitesync:team_detail', team_id=team.id)

            if sub_team.id == team.id:
                messages.error(request, 'A team cannot be added as a sub-team of itself.')
                return redirect('sitesync:team_detail', team_id=team.id)

            if sub_team.parent_team_id == team.id:
                messages.info(request, f"{sub_team.name} is already a sub-team of {team.name}.")
                return redirect('sitesync:team_detail', team_id=team.id)

            expected_level = team.level + 1
            if sub_team.level != expected_level:
                messages.error(
                    request,
                    f'Only level {expected_level} teams can be added under {team.name} (level {team.level}).'
                )
                return redirect('sitesync:team_detail', team_id=team.id)

            # Prevent circular hierarchy by blocking ancestor -> descendant reassignment.
            if team.id in {ancestor.id for ancestor in sub_team.get_parent_teams()}:
                messages.info(request, f"{sub_team.name} is already in this hierarchy.")
                return redirect('sitesync:team_detail', team_id=team.id)

            if sub_team.id in {ancestor.id for ancestor in team.get_parent_teams()}:
                messages.error(request, 'Cannot create circular hierarchy. The selected team is an ancestor of this team.')
                return redirect('sitesync:team_detail', team_id=team.id)

            sub_team.parent_team = team
            sub_team.save(update_fields=['parent_team', 'updated_at'])
            logger.info(
                f"User {request.user.username} added existing team {sub_team.name} as sub-team of {team.name}"
            )
            messages.success(request, f"{sub_team.name} added as a sub-team of {team.name}.")
            return redirect('sitesync:team_detail', team_id=team.id)

        team_form = TeamForm(request.POST)
        if team_form.is_valid():
            selected_parent = team_form.cleaned_data.get('parent_team')

            # Prevent assigning a team under one of its descendants.
            if selected_parent and team.id in {ancestor.id for ancestor in selected_parent.get_parent_teams()}:
                team_form.add_error('parent_team', 'Cannot set a descendant as parent team.')
            elif team.sub_teams.exclude(level=team_form.cleaned_data['level'] + 1).exists():
                team_form.add_error(
                    'level',
                    'This level is incompatible with current sub-team levels. Update sub-teams first.'
                )

        if team_form.is_valid():
            team.name = team_form.cleaned_data['name']
            team.level = team_form.cleaned_data['level']
            team.parent_team = team_form.cleaned_data.get('parent_team')
            team.manager = team_form.cleaned_data.get('manager')
            team.team_lead = team_form.cleaned_data.get('team_lead')
            team.save()
            logger.info(f"User {request.user.username} updated team: {team.name}")
            return redirect('sitesync:team_detail', team_id=team.id)

        wants_json = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('format') == 'json'
        if wants_json:
            return JsonResponse({'errors': team_form.errors}, status=400)
    
    # GET: Display team details
    members = team.user_assignments.all().select_related('user')
    sub_teams = team.sub_teams.all()
    parent_team = team.parent_team
    assigned_user_ids = members.values_list('user_id', flat=True)
    assignable_users = get_user_model().objects.filter(is_active=True).exclude(id__in=assigned_user_ids).order_by('username')
    ancestor_ids = [parent.id for parent in team.get_parent_teams()]
    expected_child_level = team.level + 1
    sub_team_candidates = Team.objects.exclude(id=team.id).exclude(id__in=ancestor_ids).exclude(parent_team=team).filter(level=expected_child_level).order_by('name')
    
    context = {
        'team': team,
        'members': members,
        'sub_teams': sub_teams,
        'parent_team': parent_team,
        'can_edit': can_edit,
        'assignable_users': assignable_users,
        'sub_team_candidates': sub_team_candidates,
        'team_form': team_form,
    }
    return render(request, 'sitesync/team_detail.html', context)


@login_required
def user_team_assignment_view(request):
    """
    GET: List team assignments for a user.
    POST: Assign user to a team (admin/manager only).
    DELETE: Remove user from a team (admin/manager only).
    """
    from .models import UserTeamAssignment, Team
    from .forms import UserTeamAssignmentForm
    
    # Check if user is admin or manager
    is_admin_or_manager = (
        request.user.is_staff or 
        request.user.is_superuser or
        request.user.role_assignments.filter(role_name='admin').exists() or
        request.user.role_assignments.filter(role_name='manager').exists()
    )
    
    if request.method == 'POST':
        if not is_admin_or_manager:
            return JsonResponse({'error': 'Permission denied'}, status=403)

        return_to_team_id = request.POST.get('return_to_team_id')
        wants_json = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('format') == 'json'
        
        form = UserTeamAssignmentForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            team = form.cleaned_data['team']
            
            # Check if assignment already exists
            if UserTeamAssignment.objects.filter(user=user, team=team).exists():
                if return_to_team_id and not wants_json:
                    messages.error(request, 'User is already assigned to this team.')
                    return redirect('sitesync:team_detail', team_id=return_to_team_id)
                return JsonResponse({'error': 'User already assigned to this team'}, status=400)
            
            assignment = UserTeamAssignment(
                user=user,
                team=team,
                assigned_by=request.user,
            )
            assignment.save()
            logger.info(f"User {request.user.username} assigned {user.username} to team {team.name}")
            if return_to_team_id and not wants_json:
                messages.success(request, f"{user.get_username()} added to {team.name}.")
                return redirect('sitesync:team_detail', team_id=return_to_team_id)
            return JsonResponse({'success': True, 'assignment_id': str(assignment.id)})
        else:
            if return_to_team_id and not wants_json:
                messages.error(request, 'Unable to add member. Please select a valid user.')
                return redirect('sitesync:team_detail', team_id=return_to_team_id)
            return JsonResponse({'errors': form.errors}, status=400)
    
    if request.method == 'DELETE':
        if not is_admin_or_manager:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        assignment_id = request.GET.get('assignment_id')
        try:
            assignment = UserTeamAssignment.objects.get(id=assignment_id)
            user_name = assignment.user.username
            team_name = assignment.team.name
            assignment.delete()
            logger.info(f"User {request.user.username} removed {user_name} from team {team_name}")
            return JsonResponse({'success': True})
        except UserTeamAssignment.DoesNotExist:
            return JsonResponse({'error': 'Assignment not found'}, status=404)
    
    # GET: List assignments
    assignments = UserTeamAssignment.objects.all().select_related('user', 'team', 'assigned_by')
    paginator = Paginator(assignments, 50)
    page = request.GET.get('page', 1)
    
    try:
        assignments_page = paginator.page(page)
    except Exception:
        assignments_page = paginator.page(1)
    
    context = {
        'assignments': assignments_page,
        'is_admin_or_manager': is_admin_or_manager,
    }
    return render(request, 'sitesync/user_team_assignment.html', context)


@login_required
def role_assignment_view(request):
    """
    GET: List role assignments for users.
    POST: Assign a role to a user (admin only).
    DELETE: Revoke a role from a user (admin only).
    """
    from .models import RoleAssignment
    from .forms import RoleAssignmentForm
    
    # Check if user is admin
    is_admin = (
        request.user.is_staff or 
        request.user.is_superuser or
        request.user.role_assignments.filter(role_name='admin').exists()
    )
    
    if request.method == 'POST':
        if not is_admin:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        form = RoleAssignmentForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            role_name = form.cleaned_data['role_name']
            
            # Check if role assignment already exists
            if RoleAssignment.objects.filter(user=user, role_name=role_name).exists():
                return JsonResponse({'error': 'User already has this role'}, status=400)
            
            assignment = RoleAssignment(
                user=user,
                role_name=role_name,
                assigned_by=request.user,
            )
            assignment.save()
            logger.info(f"User {request.user.username} assigned role {role_name} to {user.username}")
            return JsonResponse({'success': True, 'assignment_id': str(assignment.id)})
        else:
            return JsonResponse({'errors': form.errors}, status=400)
    
    if request.method == 'DELETE':
        if not is_admin:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        assignment_id = request.GET.get('assignment_id')
        try:
            assignment = RoleAssignment.objects.get(id=assignment_id)
            user_name = assignment.user.username
            role_name = assignment.get_role_name_display()
            assignment.delete()
            logger.info(f"User {request.user.username} revoked role {role_name} from {user_name}")
            return JsonResponse({'success': True})
        except RoleAssignment.DoesNotExist:
            return JsonResponse({'error': 'Assignment not found'}, status=404)
    
    # GET: List assignments
    assignments = RoleAssignment.objects.all().select_related('user', 'assigned_by')
    paginator = Paginator(assignments, 50)
    page = request.GET.get('page', 1)
    
    try:
        assignments_page = paginator.page(page)
    except Exception:
        assignments_page = paginator.page(1)
    
    context = {
        'assignments': assignments_page,
        'is_admin': is_admin,
    }
    return render(request, 'sitesync/role_assignment.html', context)


# Admin Panel Views (Phase 5)

def _user_is_admin(user):
    """Return True if user has Django staff/superuser status or an 'admin' RoleAssignment."""
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    from .models import RoleAssignment
    return RoleAssignment.objects.filter(user=user, role_name='admin').exists()


def admin_panel_required(view_func):
    """Decorator to require admin access for panel views."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not _user_is_admin(request.user):
            messages.error(request, 'Admin access required.')
            return redirect('sitesync:site_list')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_panel_required
def admin_panel_view(request):
    """Admin panel home/dashboard view."""
    from .models import Team, UserTeamAssignment, RoleAssignment
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Get statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    total_teams = Team.objects.count()
    total_assignments = UserTeamAssignment.objects.count()
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'total_teams': total_teams,
        'total_assignments': total_assignments,
    }
    return render(request, 'sitesync/panel_dashboard.html', context)


@admin_panel_required
def admin_users_view(request):
    """Admin panel users section."""
    from django.contrib.auth import get_user_model
    from django.core.paginator import Paginator
    
    User = get_user_model()
    
    users = User.objects.all().order_by('-date_joined')
    paginator = Paginator(users, 20)
    page = request.GET.get('page', 1)
    
    try:
        users_page = paginator.page(page)
    except Exception:
        users_page = paginator.page(1)
    
    context = {
        'users': users_page,
    }
    return render(request, 'sitesync/panel_users.html', context)


@admin_panel_required
def admin_teams_view(request):
    """Admin panel teams section."""
    from .models import Team
    from .forms import TeamForm
    from django.core.paginator import Paginator

    parent_team_id = request.GET.get('parent_team')
    initial_data = {'parent_team': parent_team_id}
    if parent_team_id:
        try:
            parent_team = Team.objects.get(id=parent_team_id)
            initial_data['level'] = parent_team.level + 1
        except Team.DoesNotExist:
            initial_data['level'] = 1
    team_form = TeamForm(initial=initial_data)

    if request.method == 'POST':
        team_form = TeamForm(request.POST)
        if team_form.is_valid():
            team = Team(
                name=team_form.cleaned_data['name'],
                level=team_form.cleaned_data['level'],
                parent_team=team_form.cleaned_data.get('parent_team'),
                manager=team_form.cleaned_data.get('manager'),
                team_lead=team_form.cleaned_data.get('team_lead'),
            )
            team.save()
            logger.info(f"User {request.user.username} created team from admin panel: {team.name}")
            messages.success(request, f"Team '{team.name}' created successfully.")
            return redirect('sitesync:team_detail', team_id=team.id)

        messages.error(request, 'Unable to create team. Please fix the highlighted fields.')
    
    teams = Team.objects.all().order_by('name')
    paginator = Paginator(teams, 20)
    page = request.GET.get('page', 1)
    
    try:
        teams_page = paginator.page(page)
    except Exception:
        teams_page = paginator.page(1)
    
    context = {
        'teams': teams_page,
        'team_form': team_form,
    }
    return render(request, 'sitesync/panel_teams.html', context)


@admin_panel_required
def admin_hierarchy_view(request):
    """Admin panel organizational hierarchy view."""
    from .models import Team
    
    # Get root teams (no parent)
    root_teams = Team.objects.filter(parent_team__isnull=True).order_by('name')
    
    context = {
        'root_teams': root_teams,
    }
    return render(request, 'sitesync/panel_hierarchy.html', context)


@admin_panel_required
def admin_roles_view(request):
    """Admin panel role assignments section."""
    from .models import RoleAssignment
    from django.core.paginator import Paginator
    
    assignments = RoleAssignment.objects.all().select_related('user', 'assigned_by').order_by('user__username')
    paginator = Paginator(assignments, 50)
    page = request.GET.get('page', 1)
    
    try:
        assignments_page = paginator.page(page)
    except Exception:
        assignments_page = paginator.page(1)
    
    context = {
        'assignments': assignments_page,
    }
    return render(request, 'sitesync/panel_roles.html', context)


# ============================================================================
# Phase 6: Report Access Scoping Views
# ============================================================================

@login_required(login_url='/login/')
def request_team_assignment_view(request):
    """
    Allow users without team assignment to request access.
    
    GET: Renders a form for users to provide reason/message
    POST: Creates a request and notifies administrators
    """
    from .models import UserTeamAssignment
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Check if user already has team assignments
    if UserTeamAssignment.objects.filter(user=request.user).exists():
        messages.info(request, 'You are already assigned to a team.')
        return redirect('sitesync:saved_reports')
    
    if request.method == 'POST':
        message = (request.POST.get('message') or '').strip()
        
        # Log the request
        logger.info(
            'User requested team assignment: user=%s, message=%s',
            request.user.username,
            message[:100] if message else 'none'
        )
        
        # TODO: In future versions, create TeamAssignmentRequest model
        # and send notification to admins
        
        messages.success(
            request,
            'Your request has been submitted. An administrator will review and assign you to a team soon.'
        )
        return redirect('sitesync:saved_reports')
    
    return render(request, 'sitesync/request_team_assignment.html', {
        'user': request.user,
    })
