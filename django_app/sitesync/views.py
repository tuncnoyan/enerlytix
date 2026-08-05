"""
Views for the sitesync app.
"""

import logging
import json
import csv
from collections import defaultdict
from datetime import datetime, timezone as datetime_timezone
from decimal import Decimal, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Count, Q, Sum
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone as dj_timezone
from openpyxl import Workbook
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
    ReportWriteGrant,
    Invitation,
    AuditLogEntry,
        ReportValidationEvent,
)
from .forms import (
    AccountActionForm,
    AuditLogFilterForm,
    CapacityUploadForm,
    InvitationForm,
    ReportDelegationActionForm,
    ReportOwnerUnavailabilityApprovalForm,
    ReportOwnershipTransferForm,
    ReportValidationAssignForm,
    ReportValidationPageToggleForm,
    ReportWriteGrantForm,
    ReportWriteRevokeForm,
    SettingsForm,
)
from .config_service import SettingsConfigService
from .auth_service import build_invitation_email
from .services import EtainaibleSyncService
from .services import (
    AUDIT_ACTION_ACCESS_DENIED,
    AUDIT_ACTION_ADMIN_ACCEPT_INVITATION,
    AUDIT_ACTION_ADMIN_ADD_SUB_TEAM,
    AUDIT_ACTION_ADMIN_ASSIGN_ROLE,
    AUDIT_ACTION_ADMIN_ASSIGN_TEAM,
    AUDIT_ACTION_ADMIN_CREATE_INVITATION,
    AUDIT_ACTION_ADMIN_SEND_INVITATION_EMAIL,
    AUDIT_ACTION_ADMIN_RESEND_INVITATION_EMAIL,
    AUDIT_ACTION_ADMIN_REVOKE_INVITATION,
    AUDIT_ACTION_ADMIN_CREATE_TEAM,
    AUDIT_ACTION_ADMIN_DELETE_USER,
    AUDIT_ACTION_ADMIN_DISABLE_USER,
    AUDIT_ACTION_ADMIN_ENABLE_USER,
    AUDIT_ACTION_ADMIN_EXPORT_AUDIT_LOG,
    AUDIT_ACTION_ADMIN_REVOKE_ROLE,
    AUDIT_ACTION_ADMIN_RESET_PASSWORD,
    AUDIT_ACTION_ADMIN_SYNC_TRIGGER,
    AUDIT_ACTION_ADMIN_UNASSIGN_TEAM,
    AUDIT_ACTION_ADMIN_UPDATE_SETTINGS,
    AUDIT_ACTION_ADMIN_UPDATE_TEAM,
    AUDIT_ACTION_ADMIN_UPDATE_USERNAME,
    AUDIT_ACTION_ADMIN_UPLOAD_CAPACITY,
    AUDIT_ACTION_ADMIN_VIEW_AUDIT_LOG,
    AUDIT_ACTION_REPORT_APPROVE_UNAVAILABLE_OWNER,
    AUDIT_ACTION_REPORT_GRANT_WRITE,
    AUDIT_ACTION_REPORT_REPLACE_FINAL,
    AUDIT_ACTION_REPORT_REVOKE_WRITE,
    AUDIT_ACTION_REPORT_SAVE_DRAFT,
    AUDIT_ACTION_REPORT_SAVE_FINAL,
    AUDIT_ACTION_REPORT_TRANSFER_OWNERSHIP,
    approve_owner_unavailability_and_transfer,
    build_report_cover_set,
    carry_forward_comments_from_previous_final,
    check_audit_export_threshold,
    ConsumptionImportService,
    create_audit_log_entry,
    create_report_version,
    get_filtered_audit_logs,
    get_capacity_lookup_by_meter_codes,
    get_report_access_mode,
    get_or_create_monthly_report,
    get_report_write_grant,
    grant_report_write_access,
    get_consumption_display_records,
    get_report_delegation_candidate_users,
    get_report_delegation_role_hint,
    get_report_validation_summary,
    get_report_validation_candidate_users,
    get_report_delegation_visibility_rows,
    get_previous_month_final_version,
    import_capacity_upload,
    month_start,
    normalize_esight_meter_code,
    normalize_reporting_month,
    can_user_manage_report_delegations,
    can_user_assign_report_validator,
    _resolve_grantor_role,
    reporting_month_bounds,
    serialize_audit_entry_for_export,
    shift_months,
    transfer_report_ownership,
    assign_report_validator,
    get_report_validation_comment_snapshot,
    mark_report_page_validation_state,
    reset_report_page_validation_state,
    upsert_report_validation_comments,
    user_can_write_report,
    revoke_report_write_access,
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


def _get_client_ip(request):
    """Resolve the best-effort client IP from forwarding headers."""

    forwarded_for = (request.META.get('HTTP_X_FORWARDED_FOR') or '').strip()
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    remote_addr = (request.META.get('REMOTE_ADDR') or '').strip()
    return remote_addr or None


def _log_denied_admin_panel_access(request):
    """Log denied attempts to access admin-only panel routes."""

    actor = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
    actor_name = actor.get_username() if actor else 'anonymous'
    create_audit_log_entry(
        actor_user=actor,
        actor_username_snapshot=actor_name,
        source_ip=_get_client_ip(request),
        action_type=AUDIT_ACTION_ACCESS_DENIED,
        action_outcome=AuditLogEntry.OUTCOME_DENIED,
        target_entity_type='admin_panel',
        target_entity_id='route',
        target_entity_label=request.path,
        message=f"Denied admin panel access for {actor_name}",
        request_path=request.path,
        metadata_json={
            'reason': 'admin_required',
            'method': request.method,
        },
    )


def _log_audit_event(
    request,
    *,
    action_type,
    action_outcome,
    target_entity_type,
    message,
    target_entity_id=None,
    target_entity_label=None,
    metadata=None,
):
    """Write audit row with consistent actor and request context."""

    actor = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
    actor_name = actor.get_username() if actor else 'anonymous'
    create_audit_log_entry(
        actor_user=actor,
        actor_username_snapshot=actor_name,
        source_ip=_get_client_ip(request),
        action_type=action_type,
        action_outcome=action_outcome,
        target_entity_type=target_entity_type,
        target_entity_id=target_entity_id,
        target_entity_label=target_entity_label,
        message=message,
        request_path=request.path,
        metadata_json=metadata or {},
    )


def _send_invitation_email(request, invitation):
    """Send invitation email through configured Django email backend."""
    message, _ = build_invitation_email(request, invitation)

    try:
        sent_count = message.send(fail_silently=False)
        return sent_count > 0, ''
    except Exception as exc:
        logger.exception('Failed to send invitation email for %s', invitation.email)
        return False, str(exc)


def _send_and_log_invitation_email(request, invitation, *, action_type, success_message, failure_message):
    """Send invitation email and persist a corresponding audit row."""

    email_sent, email_error = _send_invitation_email(request, invitation)
    _log_audit_event(
        request,
        action_type=action_type,
        action_outcome=AuditLogEntry.OUTCOME_SUCCESS if email_sent else AuditLogEntry.OUTCOME_FAILED,
        target_entity_type='invitation',
        target_entity_id=str(invitation.id),
        target_entity_label=invitation.email,
        message=success_message if email_sent else failure_message.format(error=email_error),
        metadata={
            'email_backend': getattr(settings, 'EMAIL_BACKEND', ''),
            'send_attempted': True,
            'sent': email_sent,
            'error': email_error,
        },
    )
    return email_sent, email_error


def _activate_and_resend_invitation(request, invitation):
    """Reset an invitation to pending and resend it."""

    invitation.status = Invitation.STATUS_PENDING
    invitation.revoked_at = None
    invitation.save(update_fields=['status', 'revoked_at', 'updated_at'])
    return invitation


def _revoke_invitation(invitation):
    """Mark a pending invitation as revoked."""

    if invitation.status != Invitation.STATUS_PENDING:
        return False
    return invitation.revoke()


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



def _report_editor_context(raw_site_id, raw_end_month, raw_reporting_month, raw_supply_ids, user=None, request=None):
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

    validation_summary = get_report_validation_summary(monthly_report) if monthly_report is not None else {
        'validation_status': MonthlyReport.VALIDATION_DRAFT,
        'validator_user_id': None,
        'validator_user': None,
        'validator_assigned_by_user_id': None,
        'validator_assigned_at': None,
        'validated_by_user_id': None,
        'validated_by_user': None,
        'validated_at': None,
        'validated_page_count': 0,
        'total_page_count': 0,
        'can_finalize': False,
        'pages_validation': {},
    }
    validation_comment_snapshot = get_report_validation_comment_snapshot(monthly_report) if monthly_report is not None else {
        'validation_comments': {},
        'validation_comment_threads': {},
    }
    validation_candidates = get_report_validation_candidate_users(monthly_report, actor_user=user) if monthly_report is not None else []
    can_assign_validator = bool(monthly_report is not None and user is not None and getattr(user, 'is_authenticated', False) and can_user_assign_report_validator(monthly_report, user))

    access_mode = 'read_only'
    if monthly_report is not None:
        access_mode = get_report_access_mode(monthly_report, user)
    elif user is not None and getattr(user, 'is_authenticated', False):
        # New unsaved report sessions should be editable so the first save can establish ownership.
        access_mode = 'owner'

    active_delegations = []
    delegation_candidates = []
    can_manage_delegations = False
    delegation_role_hint = ''
    if monthly_report is not None and user is not None and getattr(user, 'is_authenticated', False):
        active_delegations = get_report_delegation_visibility_rows(monthly_report)
        can_manage_delegations = can_user_manage_report_delegations(monthly_report, user)
        if can_manage_delegations:
            delegation_candidates = get_report_delegation_candidate_users(monthly_report, user)
            delegation_role_hint = get_report_delegation_role_hint(monthly_report, user)

    validation_summary_client = {
        'validation_status': validation_summary['validation_status'],
        'validator_user_id': validation_summary['validator_user_id'],
        'validator_user_name': validation_summary['validator_user'].get_username() if validation_summary['validator_user'] else None,
        'validator_assigned_by_user_id': validation_summary['validator_assigned_by_user_id'],
        'validator_assigned_at': validation_summary['validator_assigned_at'],
        'validated_by_user_id': validation_summary['validated_by_user_id'],
        'validated_by_user_name': validation_summary['validated_by_user'].get_username() if validation_summary['validated_by_user'] else None,
        'validated_at': validation_summary['validated_at'],
        'validated_page_count': validation_summary['validated_page_count'],
        'total_page_count': validation_summary['total_page_count'],
        'can_finalize': validation_summary['can_finalize'],
        'pages_validation': validation_summary['pages_validation'],
    }

    report_context = {
        'reportId': str(monthly_report.id) if monthly_report else '',
        'reportStatus': monthly_report.current_status if monthly_report else '',
        'siteId': site.id if site else site_id,
        'endMonth': end_month,
        'siteName': site.name if site else '',
        'supplyIds': supply_ids,
        'initialComments': initial_comments,
        'referenceCommentKeys': reference_comment_keys,
        'validationComments': validation_comment_snapshot['validation_comments'],
        'validationCommentThreads': validation_comment_snapshot['validation_comment_threads'],
        'validationCandidates': validation_candidates,
        'canAssignValidator': can_assign_validator,
        'accessMode': access_mode,
        'validationSummary': validation_summary_client,
        'currentUserId': request.user.id if request is not None and getattr(request.user, 'is_authenticated', False) else None,
        'activeDelegations': active_delegations,
        'canManageDelegations': can_manage_delegations,
        'coverDefaults': build_report_cover_set(site.name if site else '', end_month),
    }

    return {
        'report_site': site,
        'site_id': site.id if site else site_id,
        'end_month': end_month,
        'supply_ids': supply_ids,
        'monthly_report': monthly_report,
        'report_access_mode': access_mode,
        'validation_summary': validation_summary,
        'validation_comment_snapshot': validation_comment_snapshot,
        'validation_candidates': validation_candidates,
        'can_assign_validator': can_assign_validator,
        'active_delegations': active_delegations,
        'delegation_candidates': delegation_candidates,
        'can_manage_delegations': can_manage_delegations,
        'delegation_role_hint': delegation_role_hint,
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


@login_required(login_url='/login/')
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

        validation_comments_payload = {}
        validation_comments_raw = (request.POST.get('validation_comments') or '').strip()
        if validation_comments_raw:
            try:
                parsed_validation_comments = json.loads(validation_comments_raw)
                if isinstance(parsed_validation_comments, dict):
                    validation_comments_payload = {
                        str(k): str(v or '') for k, v in parsed_validation_comments.items()
                    }
            except json.JSONDecodeError:
                return JsonResponse({'detail': 'validation_comments must be valid JSON object'}, status=400)

        report = get_or_create_monthly_report(site, end_month, actor_user=request.user)
        previous_version = report.current_version
        previous_status = report.current_status
        access_mode = get_report_access_mode(report, request.user)
        if not user_can_write_report(report, request.user):
            _log_audit_event(
                request,
                action_type=AUDIT_ACTION_ACCESS_DENIED,
                action_outcome=AuditLogEntry.OUTCOME_DENIED,
                target_entity_type='report',
                target_entity_id=str(report.id),
                target_entity_label=f"{site.name} {end_month}",
                message='Denied report write without ownership or active grant.',
                metadata={'site_id': site.id, 'reporting_month': end_month, 'access_mode': access_mode},
            )
            return JsonResponse({'detail': 'You do not have write access to this report.'}, status=403)

        created_first_version = report.current_version is None
        if save_mode == 'final':
            if report.current_status == MonthlyReport.STATUS_FINAL and not confirm_final_edit:
                _log_audit_event(
                    request,
                    action_type=AUDIT_ACTION_REPORT_REPLACE_FINAL,
                    action_outcome=AuditLogEntry.OUTCOME_DENIED,
                    target_entity_type='report',
                    target_entity_id=str(report.id),
                    target_entity_label=f"{site.name} {end_month}",
                    message='Denied final report replacement without confirmation.',
                    metadata={'site_id': site.id, 'reporting_month': end_month},
                )
                return JsonResponse({
                    'detail': 'This report is already final. Confirm before editing.',
                    'warning_required': True,
                }, status=409)

            validation_summary = get_report_validation_summary(report)
            if not validation_summary['can_finalize']:
                action_type = (
                    AUDIT_ACTION_REPORT_REPLACE_FINAL
                    if report.current_status == MonthlyReport.STATUS_FINAL
                    else AUDIT_ACTION_REPORT_SAVE_FINAL
                )
                _log_audit_event(
                    request,
                    action_type=action_type,
                    action_outcome=AuditLogEntry.OUTCOME_DENIED,
                    target_entity_type='report',
                    target_entity_id=str(report.id),
                    target_entity_label=f"{site.name} {end_month}",
                    message='Denied final report save until all pages are validated.',
                    metadata={
                        'site_id': site.id,
                        'reporting_month': end_month,
                        'validation_status': validation_summary['validation_status'],
                        'validated_page_count': validation_summary['validated_page_count'],
                        'total_page_count': validation_summary['total_page_count'],
                    },
                )
                ReportValidationEvent.objects.create(
                    report=report,
                    event_type=ReportValidationEvent.EVENT_FINAL_BLOCKED,
                    event_by_user=request.user,
                    metadata={
                        'site_id': site.id,
                        'reporting_month': end_month,
                        'validation_status': validation_summary['validation_status'],
                        'validated_page_count': validation_summary['validated_page_count'],
                        'total_page_count': validation_summary['total_page_count'],
                    },
                )
                return JsonResponse({
                    'detail': 'All report pages must be validated before saving final.',
                    'can_save_final': False,
                    'validation_status': validation_summary['validation_status'],
                    'validated_page_count': validation_summary['validated_page_count'],
                    'total_page_count': validation_summary['total_page_count'],
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
            actor_user=request.user,
        )

        changed_page_keys = []
        if previous_version is not None:
            previous_comments = {comment.visual_key: comment.text for comment in previous_version.comments.all()}
            new_comments = {comment.visual_key: comment.text for comment in version.comments.all()}
            all_keys = set(previous_comments) | set(new_comments)
            changed_page_keys = [
                key for key in sorted(all_keys)
                if previous_comments.get(key, '') != new_comments.get(key, '')
            ]

        if changed_page_keys:
            reset_reason = 'final_reopened' if previous_status == MonthlyReport.STATUS_FINAL else 'content_changed'
            reset_report_page_validation_state(
                report=report,
                page_keys=changed_page_keys,
                reason=reset_reason,
                actor_user=request.user,
            )

        if validation_comments_payload:
            upsert_report_validation_comments(
                report=report,
                comments_by_page=validation_comments_payload,
                actor_user=request.user,
            )

        copied_reference_comments = 0
        if save_mode == 'draft' and created_first_version:
            copied_reference_comments = carry_forward_comments_from_previous_final(report, version)

        if version_kind in {MonthlyReportVersion.KIND_FINAL, MonthlyReportVersion.KIND_REPLACEMENT_FINAL}:
            # Finalized reports must reopen as read-only until a fresh superior regrant is issued.
            ReportWriteGrant.objects.filter(report=report, is_active=True).update(
                is_active=False,
                revoked_by=request.user,
                revoked_by_role=None,
                revoked_at=dj_timezone.now(),
            )

        if version_kind == MonthlyReportVersion.KIND_DRAFT:
            action_type = AUDIT_ACTION_REPORT_SAVE_DRAFT
        elif version_kind == MonthlyReportVersion.KIND_REPLACEMENT_FINAL:
            action_type = AUDIT_ACTION_REPORT_REPLACE_FINAL
        else:
            action_type = AUDIT_ACTION_REPORT_SAVE_FINAL

        _log_audit_event(
            request,
            action_type=action_type,
            action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
            target_entity_type='report',
            target_entity_id=str(report.id),
            target_entity_label=f"{site.name} {end_month}",
            message=f"Saved report version {version.version_number} as {version.version_kind}.",
            metadata={
                'site_id': site.id,
                'reporting_month': end_month,
                'version_id': str(version.id),
                'copied_reference_comments': copied_reference_comments,
            },
        )

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'report_id': str(report.id),
                'version_id': str(version.id),
                'status': report.current_status,
                'reporting_month': report.reporting_month,
                'copied_reference_comments': copied_reference_comments,
                'access_mode': get_report_access_mode(report, request.user),
            })

        return redirect(f"{reverse('sitesync:report')}?site_id={site.id}&end_month={end_month}")

    context = _report_editor_context(
        request.GET.get('site_id', ''),
        request.GET.get('end_month', ''),
        request.GET.get('reporting_month', ''),
        request.GET.get('supply_ids', ''),
        user=request.user,
        request=request,
    )
    context['is_admin'] = _user_is_admin(getattr(request, 'user', None))
    return render(request, 'sitesync/report.html', context)


@login_required(login_url='/login/')
def saved_reports_view(request):
    """Entry point for the saved reports browser with team-based access scoping."""
    from .services import get_accessible_reports
    from .models import Team, UserTeamAssignment
    from django.db.models import Q
    import json

    user_has_teams = (
        UserTeamAssignment.objects.filter(user=request.user).exists()
        or Team.objects.filter(Q(manager=request.user) | Q(team_lead=request.user)).exists()
    )

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
    
    user_has_teams = (
        UserTeamAssignment.objects.filter(user=request.user).exists()
        or Team.objects.filter(Q(manager=request.user) | Q(team_lead=request.user)).exists()
    )
    
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
    accessible_reports = accessible_reports.select_related('site', 'owner_user', 'created_by_user', 'last_modified_by_user').order_by('-reporting_month', 'site__name')

    reports_payload = []
    for report in accessible_reports:
        validation_summary = get_report_validation_summary(report)
        reports_payload.append({
            'id': str(report.id),
            'site_id': report.site_id,
            'site_name': report.site.name,
            'reporting_month': report.reporting_month,
            'owner_name': report.owner_user.get_username() if report.owner_user else 'Unassigned',
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'created_by_name': report.created_by_user.get_username() if report.created_by_user else 'Unknown',
            'last_edited_by_name': report.last_modified_by_user.get_username() if report.last_modified_by_user else 'Unknown',
            'last_edited_at': (report.last_modified_at or report.updated_at).isoformat() if (report.last_modified_at or report.updated_at) else None,
            'status': report.current_status,
            'updated_at': report.updated_at.isoformat(),
            'access_mode': get_report_access_mode(report, request.user),
            'validation_status': validation_summary['validation_status'],
            'validator_name': validation_summary['validator_user'].get_username() if validation_summary['validator_user'] else None,
            'validated_by_name': validation_summary['validated_by_user'].get_username() if validation_summary['validated_by_user'] else None,
            'validation_date': validation_summary['validated_at'].isoformat() if validation_summary['validated_at'] else None,
            'can_save_final': validation_summary['can_finalize'],
            'open_url': f"{reverse('sitesync:report')}?site_id={report.site_id}&end_month={report.reporting_month}",
        })
    
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


@login_required(login_url='/login/')
def report_grant_write_access_view(request, report_id):
    """Grant report write access to a named user."""
    if request.method != 'POST':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)

    report = get_object_or_404(MonthlyReport, id=report_id)
    payload = request.POST.copy()
    if 'granted_user' not in payload and payload.get('granted_user_id'):
        payload['granted_user'] = payload.get('granted_user_id')
    if 'granted_user' not in payload and payload.get('target_user_id'):
        payload['granted_user'] = payload.get('target_user_id')

    form = ReportDelegationActionForm(payload)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)

    granted_user = form.cleaned_data['granted_user']
    try:
        grant = grant_report_write_access(report=report, granted_user=granted_user, granted_by=request.user)
    except PermissionError as exc:
        _log_audit_event(
            request,
            action_type=AUDIT_ACTION_ACCESS_DENIED,
            action_outcome=AuditLogEntry.OUTCOME_DENIED,
            target_entity_type='report',
            target_entity_id=str(report.id),
            target_entity_label=f"{report.site.name} {report.reporting_month}",
            message='Denied report write grant attempt by unauthorized actor.',
            metadata={'granted_user_id': granted_user.id},
        )
        return JsonResponse({'detail': str(exc)}, status=403)
    except ValueError as exc:
        # A final validated report may already carry an owner-issued grant.
        # Regrant upgrades authority source to superior-issued access.
        if (
            str(exc) == 'Write access already granted to this user'
            and report.current_status == MonthlyReport.STATUS_FINAL
            and report.validation_status == MonthlyReport.VALIDATION_VALIDATED
        ):
            existing_grant = get_report_write_grant(report, granted_user)
            if existing_grant is not None and existing_grant.granted_by_role == ReportWriteGrant.ROLE_OWNER:
                revoke_report_write_access(report=report, granted_user=granted_user, revoked_by=request.user)
                grant = grant_report_write_access(report=report, granted_user=granted_user, granted_by=request.user)
            else:
                return JsonResponse({'detail': str(exc)}, status=400)
        else:
            return JsonResponse({'detail': str(exc)}, status=400)

    _log_audit_event(
        request,
        action_type=AUDIT_ACTION_REPORT_GRANT_WRITE,
        action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
        target_entity_type='report_write_grant',
        target_entity_id=str(grant.id),
        target_entity_label=f"{report.site.name} {report.reporting_month}",
        message=f"Granted report write access to {granted_user.get_username()}.",
        metadata={'report_id': str(report.id), 'granted_user_id': granted_user.id},
    )

    return JsonResponse({'success': True, 'grant_id': str(grant.id), 'granted_user': granted_user.get_username()})


@login_required(login_url='/login/')
def report_validation_regrant_write_view(request, report_id):
    """Route alias for reopening write access through the validation workflow."""
    if request.method != 'POST':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)

    report = get_object_or_404(MonthlyReport, id=report_id)
    if report.current_status != MonthlyReport.STATUS_FINAL:
        return JsonResponse({'detail': 'Validation regrant is only available for final reports.'}, status=409)

    grantor_role = _resolve_grantor_role(report=report, actor_user=request.user)
    if grantor_role not in {ReportWriteGrant.ROLE_TEAM_LEAD, ReportWriteGrant.ROLE_MANAGER}:
        _log_audit_event(
            request,
            action_type=AUDIT_ACTION_ACCESS_DENIED,
            action_outcome=AuditLogEntry.OUTCOME_DENIED,
            target_entity_type='report',
            target_entity_id=str(report.id),
            target_entity_label=f"{report.site.name} {report.reporting_month}",
            message='Denied validation regrant by unauthorized actor.',
        )
        return JsonResponse({'detail': 'Only a team lead, manager, or admin in the owner\'s supervisory chain can regrant final report write access.'}, status=403)

    payload = request.POST.copy()
    if 'granted_user' not in payload and payload.get('granted_user_id'):
        payload['granted_user'] = payload.get('granted_user_id')
    if 'granted_user' not in payload and payload.get('target_user_id'):
        payload['granted_user'] = payload.get('target_user_id')

    form = ReportDelegationActionForm(payload)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)

    granted_user = form.cleaned_data['granted_user']
    try:
        grant = grant_report_write_access(report=report, granted_user=granted_user, granted_by=request.user)
    except PermissionError as exc:
        _log_audit_event(
            request,
            action_type=AUDIT_ACTION_ACCESS_DENIED,
            action_outcome=AuditLogEntry.OUTCOME_DENIED,
            target_entity_type='report',
            target_entity_id=str(report.id),
            target_entity_label=f"{report.site.name} {report.reporting_month}",
            message='Denied validation regrant attempt by unauthorized actor.',
            metadata={'granted_user_id': granted_user.id},
        )
        return JsonResponse({'detail': str(exc)}, status=403)
    except ValueError as exc:
        if (
            str(exc) == 'Write access already granted to this user'
            and report.validation_status == MonthlyReport.VALIDATION_VALIDATED
        ):
            existing_grant = get_report_write_grant(report, granted_user)
            if existing_grant is not None and existing_grant.granted_by_role == ReportWriteGrant.ROLE_OWNER:
                revoke_report_write_access(report=report, granted_user=granted_user, revoked_by=request.user)
                grant = grant_report_write_access(report=report, granted_user=granted_user, granted_by=request.user)
            else:
                return JsonResponse({'detail': str(exc)}, status=400)
        else:
            return JsonResponse({'detail': str(exc)}, status=400)

    validation_summary = get_report_validation_summary(report)
    return JsonResponse({
        'success': True,
        'grant_id': str(grant.id),
        'granted_user': granted_user.get_username(),
        'validation_summary': {
            'validation_status': validation_summary['validation_status'],
            'validated_page_count': validation_summary['validated_page_count'],
            'total_page_count': validation_summary['total_page_count'],
            'can_finalize': validation_summary['can_finalize'],
        },
    })


@login_required(login_url='/login/')
def report_validation_assign_view(request, report_id):
    """Assign or reassign a validator for report validation."""
    if request.method != 'POST':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)

    report = get_object_or_404(MonthlyReport, id=report_id)
    if not can_user_assign_report_validator(report, request.user):
        _log_audit_event(
            request,
            action_type='REPORT_VALIDATION_ASSIGN_DENIED',
            action_outcome=AuditLogEntry.OUTCOME_DENIED,
            target_entity_type='report',
            target_entity_id=str(report.id),
            target_entity_label=f"{report.site.name} {report.reporting_month}",
            message='Denied validator assignment by unauthorized actor.',
            metadata={'report_id': str(report.id)},
        )
        return JsonResponse({'detail': 'You do not have permission to assign a validator for this report.'}, status=403)

    payload = request.POST.copy()
    if 'validator_user' not in payload and payload.get('validator_user_id'):
        payload['validator_user'] = payload.get('validator_user_id')

    form = ReportValidationAssignForm(payload)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)

    validator_user = form.cleaned_data['validator_user']
    try:
        assign_report_validator(report=report, validator_user=validator_user, assigned_by_user=request.user)
    except ValueError as exc:
        _log_audit_event(
            request,
            action_type='REPORT_VALIDATION_ASSIGN_DENIED',
            action_outcome=AuditLogEntry.OUTCOME_DENIED,
            target_entity_type='report',
            target_entity_id=str(report.id),
            target_entity_label=f"{report.site.name} {report.reporting_month}",
            message='Denied validator assignment due to invalid validator selection.',
            metadata={'validator_user_id': validator_user.id, 'error': str(exc)},
        )
        return JsonResponse({'detail': str(exc)}, status=400)

    _log_audit_event(
        request,
        action_type='REPORT_VALIDATION_ASSIGN',
        action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
        target_entity_type='report_validation_assignment',
        target_entity_id=str(report.id),
        target_entity_label=f"{report.site.name} {report.reporting_month}",
        message=f"Assigned report validator to {validator_user.get_username()}.",
        metadata={'report_id': str(report.id), 'validator_user_id': validator_user.id},
    )

    validation_summary = get_report_validation_summary(report)

    return JsonResponse({
        'success': True,
        'report_id': str(report.id),
        'validator_user': validator_user.get_username(),
        'validation_summary': {
            'validation_status': validation_summary['validation_status'],
            'validator_user_id': validation_summary['validator_user_id'],
            'validator_user_name': validation_summary['validator_user'].get_username() if validation_summary['validator_user'] else None,
            'validated_by_user_id': validation_summary['validated_by_user_id'],
            'validated_by_user_name': validation_summary['validated_by_user'].get_username() if validation_summary['validated_by_user'] else None,
            'validated_at': validation_summary['validated_at'].isoformat() if validation_summary['validated_at'] else None,
            'validated_page_count': validation_summary['validated_page_count'],
            'total_page_count': validation_summary['total_page_count'],
            'can_finalize': validation_summary['can_finalize'],
        },
    })


@login_required(login_url='/login/')
def report_validation_page_toggle_view(request, report_id, page_key):
    """Mark or unmark a report page as validated."""
    if request.method != 'POST':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)

    report = get_object_or_404(MonthlyReport, id=report_id)
    payload = request.POST.copy()
    if 'is_validated' not in payload:
        payload['is_validated'] = payload.get('validated', 'true')

    form = ReportValidationPageToggleForm(payload)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)

    known_page_keys = []
    known_page_keys_raw = (request.POST.get('known_page_keys') or '').strip()
    if known_page_keys_raw:
        try:
            parsed_keys = json.loads(known_page_keys_raw)
            if isinstance(parsed_keys, list):
                known_page_keys = [str(item or '').strip() for item in parsed_keys if str(item or '').strip()]
        except json.JSONDecodeError:
            return JsonResponse({'detail': 'known_page_keys must be a valid JSON array'}, status=400)

    try:
        row = mark_report_page_validation_state(
            report=report,
            page_key=page_key,
            is_validated=form.cleaned_data['is_validated'],
            actor_user=request.user,
            known_page_keys=known_page_keys,
        )
    except PermissionError as exc:
        _log_audit_event(
            request,
            action_type='REPORT_VALIDATION_PAGE_TOGGLE_DENIED',
            action_outcome=AuditLogEntry.OUTCOME_DENIED,
            target_entity_type='report',
            target_entity_id=str(report.id),
            target_entity_label=f"{report.site.name} {report.reporting_month}",
            message='Denied page validation toggle by unauthorized actor.',
            metadata={'page_key': page_key},
        )
        return JsonResponse({'detail': str(exc)}, status=403)
    except ValueError as exc:
        return JsonResponse({'detail': str(exc)}, status=400)

    summary = get_report_validation_summary(report)
    return JsonResponse({
        'success': True,
        'page_key': row.page_key,
        'is_validated': row.is_validated,
        'validated_by_user': row.validated_by_user.get_username() if row.validated_by_user else None,
        'validated_at': row.validated_at.isoformat() if row.validated_at else None,
        'validation_summary': {
            'validation_status': summary['validation_status'],
            'validator_user_name': summary['validator_user'].get_username() if summary['validator_user'] else None,
            'validated_by_user_name': summary['validated_by_user'].get_username() if summary['validated_by_user'] else None,
            'validated_at': summary['validated_at'].isoformat() if summary['validated_at'] else None,
            'validated_page_count': summary['validated_page_count'],
            'total_page_count': summary['total_page_count'],
            'can_finalize': summary['can_finalize'],
            'pages_validation': summary['pages_validation'],
        },
    })


@login_required(login_url='/login/')
def report_revoke_write_access_view(request, report_id):
    """Revoke report write access from a named user."""
    if request.method != 'POST':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)

    report = get_object_or_404(MonthlyReport, id=report_id)
    payload = request.POST.copy()
    if 'granted_user' not in payload and payload.get('granted_user_id'):
        payload['granted_user'] = payload.get('granted_user_id')

    form = ReportDelegationActionForm(payload)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)

    granted_user = form.cleaned_data['granted_user']
    try:
        grant = revoke_report_write_access(report=report, granted_user=granted_user, revoked_by=request.user)
    except PermissionError as exc:
        _log_audit_event(
            request,
            action_type=AUDIT_ACTION_ACCESS_DENIED,
            action_outcome=AuditLogEntry.OUTCOME_DENIED,
            target_entity_type='report',
            target_entity_id=str(report.id),
            target_entity_label=f"{report.site.name} {report.reporting_month}",
            message='Denied report write revoke attempt by unauthorized actor.',
            metadata={'granted_user_id': granted_user.id},
        )
        return JsonResponse({'detail': str(exc)}, status=403)

    if grant is None:
        return JsonResponse({'detail': 'No active write grant for this user'}, status=404)

    _log_audit_event(
        request,
        action_type=AUDIT_ACTION_REPORT_REVOKE_WRITE,
        action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
        target_entity_type='report_write_grant',
        target_entity_id=str(grant.id),
        target_entity_label=f"{report.site.name} {report.reporting_month}",
        message=f"Revoked report write access from {granted_user.get_username()}.",
        metadata={'report_id': str(report.id), 'granted_user_id': granted_user.id},
    )

    return JsonResponse({'success': True, 'grant_id': str(grant.id), 'revoked_user': granted_user.get_username()})


@login_required(login_url='/login/')
def report_delegations_view(request, report_id):
    """Read endpoint for active delegation rows on a report."""
    if request.method != 'GET':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)

    report = get_object_or_404(MonthlyReport, id=report_id)
    from .services import get_accessible_reports

    if not get_accessible_reports(request.user).filter(id=report.id).exists():
        return JsonResponse({'detail': 'You do not have read access to this report.'}, status=403)

    return JsonResponse({'delegations': get_report_delegation_visibility_rows(report)})


@login_required(login_url='/login/')
def report_delegation_grant_view(request, report_id):
    """Route alias for delegation grant contract path."""
    return report_grant_write_access_view(request, report_id)


@login_required(login_url='/login/')
def report_delegation_revoke_view(request, report_id):
    """Route alias for delegation revoke contract path."""
    return report_revoke_write_access_view(request, report_id)


@login_required(login_url='/login/')
def report_transfer_ownership_view(request, report_id):
    """Owner-only endpoint to manually transfer report ownership."""
    if request.method != 'POST':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)

    report = get_object_or_404(MonthlyReport, id=report_id)
    payload = request.POST.copy()
    if 'new_owner_user' not in payload and payload.get('new_owner_user_id'):
        payload['new_owner_user'] = payload.get('new_owner_user_id')

    form = ReportOwnershipTransferForm(payload)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)

    if report.owner_user_id != request.user.id:
        _log_audit_event(
            request,
            action_type=AUDIT_ACTION_ACCESS_DENIED,
            action_outcome=AuditLogEntry.OUTCOME_DENIED,
            target_entity_type='report',
            target_entity_id=str(report.id),
            target_entity_label=f"{report.site.name} {report.reporting_month}",
            message='Denied ownership transfer by non-owner.',
        )
        return JsonResponse({'detail': 'Only owner can transfer report ownership'}, status=403)

    new_owner = form.cleaned_data['new_owner_user']
    reason = form.cleaned_data['reason']
    try:
        event = transfer_report_ownership(
            report=report,
            new_owner=new_owner,
            transfer_mode='manual_owner_transfer',
            transfer_reason=reason,
            executed_by=request.user,
        )
    except ValueError as exc:
        return JsonResponse({'detail': str(exc)}, status=400)

    _log_audit_event(
        request,
        action_type=AUDIT_ACTION_REPORT_TRANSFER_OWNERSHIP,
        action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
        target_entity_type='report_ownership_transfer',
        target_entity_id=str(event.id),
        target_entity_label=f"{report.site.name} {report.reporting_month}",
        message=f"Transferred report ownership to {new_owner.get_username()}.",
        metadata={'report_id': str(report.id), 'new_owner_user_id': new_owner.id, 'mode': 'manual_owner_transfer'},
    )

    return JsonResponse({'success': True, 'transfer_event_id': str(event.id), 'new_owner': new_owner.get_username()})


@login_required(login_url='/login/')
def report_approve_unavailable_owner_view(request, report_id):
    """Team-lead approval endpoint to trigger fallback ownership transfer."""
    if request.method != 'POST':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)

    report = get_object_or_404(MonthlyReport, id=report_id)
    payload = request.POST.copy()
    if 'owner_user' not in payload and payload.get('owner_user_id'):
        payload['owner_user'] = payload.get('owner_user_id')

    form = ReportOwnerUnavailabilityApprovalForm(payload)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)

    owner_user = form.cleaned_data['owner_user']
    reason = form.cleaned_data['reason']

    try:
        approval, transfer_event = approve_owner_unavailability_and_transfer(
            report=report,
            owner_user=owner_user,
            approved_by=request.user,
            reason=reason,
        )
    except PermissionError as exc:
        _log_audit_event(
            request,
            action_type=AUDIT_ACTION_ACCESS_DENIED,
            action_outcome=AuditLogEntry.OUTCOME_DENIED,
            target_entity_type='report',
            target_entity_id=str(report.id),
            target_entity_label=f"{report.site.name} {report.reporting_month}",
            message='Denied unavailable-owner approval attempt.',
            metadata={'owner_user_id': owner_user.id},
        )
        return JsonResponse({'detail': str(exc)}, status=403)
    except (ValueError, LookupError) as exc:
        return JsonResponse({'detail': str(exc)}, status=400)

    _log_audit_event(
        request,
        action_type=AUDIT_ACTION_REPORT_APPROVE_UNAVAILABLE_OWNER,
        action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
        target_entity_type='report_ownership_transfer',
        target_entity_id=str(transfer_event.id),
        target_entity_label=f"{report.site.name} {report.reporting_month}",
        message='Approved owner unavailability and executed fallback transfer.',
        metadata={
            'report_id': str(report.id),
            'approval_id': str(approval.id),
            'new_owner_user_id': transfer_event.to_owner_id,
        },
    )

    return JsonResponse({
        'success': True,
        'approval_id': str(approval.id),
        'transfer_event_id': str(transfer_event.id),
        'new_owner_user_id': transfer_event.to_owner_id,
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
    profile_error = ''
    profile_success = ''

    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        first_name = (request.POST.get('first_name') or '').strip()
        last_name = (request.POST.get('last_name') or '').strip()
        user_model = get_user_model()

        if not username:
            profile_error = 'Username is required.'
        elif user_model.objects.filter(username__iexact=username).exclude(id=request.user.id).exists():
            profile_error = 'That username is already taken.'
        else:
            request.user.username = username
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save(update_fields=['username', 'first_name', 'last_name'])
            profile_success = 'Profile updated successfully.'

    return render(request, 'sitesync/profile.html', {
        'user': request.user,
        'is_admin': _user_is_admin(getattr(request, 'user', None)),
        'profile_error': profile_error,
        'profile_success': profile_success,
    })


@login_required(login_url='/login/')
def user_admin_view(request):
    return redirect('sitesync:admin_users')


def password_reset_view(request):
    return redirect('password_reset')


def accept_invitation_view(request, invitation_id):
    invitation = Invitation.objects.filter(id=invitation_id).first()
    if invitation is None:
        return render(request, 'sitesync/invite_accept.html', {'error': 'This invitation is no longer valid.'})
    if not invitation.is_valid():
        return render(request, 'sitesync/invite_accept.html', {'error': 'This invitation is no longer valid.'})

    if request.method == 'POST':
        first_name = (request.POST.get('first_name') or '').strip()
        last_name = (request.POST.get('last_name') or '').strip()
        username = (request.POST.get('username') or '').strip()
        password = (request.POST.get('password') or '').strip()
        if not first_name or not last_name or not username or not password:
            return render(request, 'sitesync/invite_accept.html', {
                'invitation': invitation,
                'error': 'Please provide first name, last name, username, and password.',
            })
        user_model = get_user_model()
        if user_model.objects.filter(username__iexact=username).exists():
            return render(request, 'sitesync/invite_accept.html', {
                'invitation': invitation,
                'error': 'That username is already taken.',
            })
        user = user_model.objects.create_user(
            username=username,
            email=invitation.email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        invitation.accept()
        _log_audit_event(
            request,
            action_type=AUDIT_ACTION_ADMIN_ACCEPT_INVITATION,
            action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
            target_entity_type='invitation',
            target_entity_id=str(invitation.id),
            target_entity_label=invitation.email,
            message=f"Accepted invitation for {invitation.email}.",
            metadata={'created_user_id': str(user.id), 'created_username': user.get_username()},
        )
        return render(request, 'sitesync/invite_accept.html', {
            'invitation': invitation,
            'success': True,
            'user': user,
        })

    return render(request, 'sitesync/invite_accept.html', {'invitation': invitation})


@login_required(login_url='/login/')
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
        'is_admin': _user_is_admin(getattr(request, 'user', None)),
    })


@login_required(login_url='/login/')
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
    supply_query = (request.GET.get('supply_q') or '').strip()
    include_inactive = (request.GET.get('include_inactive') or '').strip().lower() in {'1', 'true', 'yes', 'on'}
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

            # Inactive toggle controls whether inactive supplies are eligible first,
            # then utility/meter/search filters are applied.
            if not include_inactive:
                filtered_supplies = filtered_supplies.exclude(status__iexact='inactive')

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

            if supply_query:
                filtered_supplies = filtered_supplies.filter(
                    Q(name__icontains=supply_query)
                    | Q(external_id__icontains=supply_query)
                    | Q(device_id__icontains=supply_query)
                )

            supplies = filtered_supplies.order_by('name')
            logger.info("Loaded supplies for site_ids=%s", selected_site_ids)

            filtered_fiscal_count = supplies.filter(
                Q(parent_account_id__isnull=True) | Q(parent_account_id='')
            ).count()
            filtered_submeter_count = supplies.exclude(
                Q(parent_account_id__isnull=True) | Q(parent_account_id='')
            ).count()

            all_site_supplies = list(supplies)
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
        'supply_query': supply_query,
        'include_inactive': include_inactive,
        'selected_utility_label': utility_label_map.get(utility_type, 'All'),
        'selected_meter_label': meter_label_map.get(meter_type, 'All'),
    })


@login_required(login_url='/login/')
def manual_sync_view(request):
    """Trigger a manual sync and return to the site list."""
    if request.method != 'POST':
        return JsonResponse({
            'error': {
                'message': 'Method not allowed',
            }
        }, status=405)

    next_url = (request.POST.get('next') or '').strip()
    if not next_url.startswith('/'):
        next_url = reverse('sitesync:site_list')

    def _redirect_with_sync_status(status_value):
        joiner = '&' if '?' in next_url else '?'
        return redirect(f"{next_url}{joiner}sync={status_value}")

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
            _log_audit_event(
                request,
                action_type=AUDIT_ACTION_ADMIN_SYNC_TRIGGER,
                action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
                target_entity_type='sync',
                target_entity_id='manual',
                target_entity_label='manual_sync',
                message='Manual sync completed with no persistence changes.',
                metadata={'sync_activity': sync_activity, 'results': results},
            )
            return _redirect_with_sync_status('empty')
        _log_audit_event(
            request,
            action_type=AUDIT_ACTION_ADMIN_SYNC_TRIGGER,
            action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
            target_entity_type='sync',
            target_entity_id='manual',
            target_entity_label='manual_sync',
            message='Manual sync completed successfully.',
            metadata={'sync_activity': sync_activity, 'results': results},
        )
        return _redirect_with_sync_status('success')
    except Exception as exc:
        logger.exception("Manual sync failed")
        try:
            _log_audit_event(
                request,
                action_type=AUDIT_ACTION_ADMIN_SYNC_TRIGGER,
                action_outcome=AuditLogEntry.OUTCOME_FAILED,
                target_entity_type='sync',
                target_entity_id='manual',
                target_entity_label='manual_sync',
                message='Manual sync failed.',
                metadata={'error': str(exc)},
            )
        except Exception:
            logger.exception("Failed to write manual sync failure audit event")
        return JsonResponse({
            'error': {
                'message': 'Unable to complete sync',
                'details': str(exc),
            }
        }, status=500)


@login_required(login_url='/login/')
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
                _log_audit_event(
                    request,
                    action_type=AUDIT_ACTION_ADMIN_UPLOAD_CAPACITY,
                    action_outcome=(
                        AuditLogEntry.OUTCOME_SUCCESS
                        if capacity_upload_result.get('status') in {
                            CapacityUploadRun.STATUS_SUCCESS,
                            CapacityUploadRun.STATUS_PARTIAL_SUCCESS,
                        }
                        else AuditLogEntry.OUTCOME_FAILED
                    ),
                    target_entity_type='settings',
                    target_entity_id='capacity_upload',
                    target_entity_label='capacity_upload',
                    message='Processed capacity upload from settings panel.',
                    metadata={
                        'status': capacity_upload_result.get('status'),
                        'total_rows': capacity_upload_result.get('total_rows', 0),
                        'accepted_rows': capacity_upload_result.get('accepted_rows', 0),
                        'rejected_rows': capacity_upload_result.get('rejected_rows', 0),
                    },
                )
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
                _log_audit_event(
                    request,
                    action_type=AUDIT_ACTION_ADMIN_UPLOAD_CAPACITY,
                    action_outcome=AuditLogEntry.OUTCOME_FAILED,
                    target_entity_type='settings',
                    target_entity_id='capacity_upload',
                    target_entity_label='capacity_upload',
                    message='Failed capacity upload validation from settings panel.',
                    metadata={'errors': capacity_upload_result['errors']},
                )
        else:
            form = SettingsForm(request.POST, instance=settings_instance)
            if form.is_valid():
                logger.info("Updating application settings")
                SettingsConfigService.update_settings(form)
                _log_audit_event(
                    request,
                    action_type=AUDIT_ACTION_ADMIN_UPDATE_SETTINGS,
                    action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
                    target_entity_type='settings',
                    target_entity_id='app_settings',
                    target_entity_label='application_settings',
                    message='Updated application settings.',
                )
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

    payload = _build_consumption_display_payload(validated)
    return Response(payload)


@login_required(login_url='/login/')
def admin_import_review_sites_api_view(request):
    """Return site options for admin import-review selection."""

    if not _user_is_admin(request.user):
        _log_denied_admin_panel_access(request)
        return JsonResponse({'detail': 'Admin access required.'}, status=403)

    sites = Site.objects.annotate(supply_count=Count('supplies')).order_by('name')
    payload = [
        {
            'id': site.id,
            'name': site.name,
            'external_id': site.external_id,
            'supply_count': site.supply_count,
        }
        for site in sites
    ]
    return JsonResponse({'sites': payload})


@login_required(login_url='/login/')
def admin_import_review_supplies_api_view(request):
    """Return supply options scoped to selected sites for import review."""

    if not _user_is_admin(request.user):
        _log_denied_admin_panel_access(request)
        return JsonResponse({'detail': 'Admin access required.'}, status=403)

    raw_site_ids = request.GET.get('site_ids', '')
    raw_supply_ids = request.GET.get('supply_ids', '')
    search_query = (request.GET.get('q') or '').strip()
    include_inactive = (request.GET.get('include_inactive') or '').strip().lower() in {'1', 'true', 'yes', 'on'}
    utility_type = (request.GET.get('utility_type') or 'all').strip().lower()
    include_submeters = (request.GET.get('include_submeters') or '').strip().lower() in {'1', 'true', 'yes', 'on'}

    site_ids = []
    if raw_site_ids:
        for value in raw_site_ids.split(','):
            value = value.strip()
            if not value:
                continue
            try:
                site_ids.append(int(value))
            except (TypeError, ValueError):
                continue
    site_ids = list(dict.fromkeys(site_ids))

    supply_external_ids = [value.strip() for value in raw_supply_ids.split(',') if value.strip()] if raw_supply_ids else []

    supplies = Supply.objects.select_related('site')
    if site_ids:
        supplies = supplies.filter(site_id__in=site_ids)
    if supply_external_ids:
        supplies = supplies.filter(external_id__in=supply_external_ids)
    if not include_inactive:
        supplies = supplies.exclude(status__iexact='inactive')
    if utility_type in {'electricity', 'gas', 'water', 'other'}:
        supplies = supplies.filter(utility_type=utility_type)
    if not include_submeters:
        supplies = supplies.filter(Q(parent_account_id__isnull=True) | Q(parent_account_id=''))
    if search_query:
        supplies = supplies.filter(
            Q(name__icontains=search_query)
            | Q(external_id__icontains=search_query)
            | Q(site__name__icontains=search_query)
            | Q(device_id__icontains=search_query)
        )

    payload = []
    for supply in supplies.order_by('site__name', 'name'):
        parent_id = (supply.parent_account_id or '').strip()
        payload.append({
            'external_id': supply.external_id,
            'name': supply.name or supply.external_id,
            'site_id': supply.site_id,
            'site_name': supply.site.name,
            'utility_type': supply.utility_type,
            'utility_label': supply.get_utility_type_display(),
            'meter_type': 'submeter' if parent_id else 'fiscal',
            'status': (supply.status or '').strip().lower() or 'unknown',
            'device_id': supply.device_id or '',
        })

    return JsonResponse({'supplies': payload, 'total': len(payload)})


def _build_consumption_display_payload(validated_query):
    """Build import-review records payload shared by API and export views."""

    reporting_month = validated_query['reporting_month']
    supply_external_id = validated_query.get('supply_id')
    supply_ids_raw = validated_query.get('supply_ids')
    data_type = validated_query.get('data_type', 'monthly')

    supply_external_ids = []
    if supply_ids_raw:
        supply_external_ids = [item.strip() for item in supply_ids_raw.split(',') if item.strip()]

    rows = get_consumption_display_records(
        reporting_month=reporting_month,
        data_type=data_type,
        supply_external_id=supply_external_id,
        supply_external_ids=supply_external_ids,
    )

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

    return {
        'reporting_month': reporting_month,
        'data_type': data_type,
        'total_records': len(rows),
        'in_window': in_window,
        'records': rows,
    }


@login_required(login_url='/login/')
def consumption_display_view(request):
    # Preserve legacy bookmarks by redirecting to the new admin panel route.
    redirect_url = reverse('sitesync:admin_import_review_results')
    query_string = request.GET.urlencode()
    if query_string:
        redirect_url = f"{redirect_url}?{query_string}"
    return redirect(redirect_url)


@login_required(login_url='/login/')
def admin_import_review_view(request):
    """Render admin import selection page (sites + supplies)."""

    if not _user_is_admin(request.user):
        _log_denied_admin_panel_access(request)
        messages.error(request, 'Admin access required.')
        return redirect('sitesync:site_list')

    reporting_month = request.GET.get('reporting_month', '')
    site_ids = request.GET.get('site_ids', '')
    supply_ids = request.GET.get('supply_ids', '')
    supply_id = request.GET.get('supply_id', '')
    data_type = request.GET.get('data_type', 'monthly')
    utility_type = request.GET.get('utility_type', 'all')
    include_submeters = request.GET.get('include_submeters', '')
    include_inactive = request.GET.get('include_inactive', '')

    context = {
        'reporting_month': reporting_month,
        'site_ids': site_ids,
        'supply_id': supply_id,
        'supply_ids': supply_ids,
        'data_type': data_type,
        'utility_type': utility_type,
        'include_submeters': include_submeters,
        'include_inactive': include_inactive,
    }
    return render(request, 'sitesync/import_selection.html', context)


@login_required(login_url='/login/')
def admin_import_review_results_view(request):
    """Render admin import review results table in a dedicated page."""

    if not _user_is_admin(request.user):
        _log_denied_admin_panel_access(request)
        messages.error(request, 'Admin access required.')
        return redirect('sitesync:site_list')

    reporting_month = request.GET.get('reporting_month', '')
    site_ids = request.GET.get('site_ids', '')
    supply_id = request.GET.get('supply_id', '')
    supply_ids = request.GET.get('supply_ids', '')
    data_type = request.GET.get('data_type', 'monthly')

    query_string = request.GET.urlencode()
    csv_export_url = reverse('sitesync:admin_import_review_export_csv')
    xlsx_export_url = reverse('sitesync:admin_import_review_export_xlsx')
    if query_string:
        csv_export_url = f"{csv_export_url}?{query_string}"
        xlsx_export_url = f"{xlsx_export_url}?{query_string}"

    context = {
        'reporting_month': reporting_month,
        'site_ids': site_ids,
        'supply_id': supply_id,
        'supply_ids': supply_ids,
        'data_type': data_type,
        'csv_export_url': csv_export_url,
        'xlsx_export_url': xlsx_export_url,
        'query_string': query_string,
    }
    return render(request, 'sitesync/consumption_display.html', context)


@login_required(login_url='/login/')
def admin_import_review_export_csv_view(request):
    """Export the current filtered import-review view to CSV."""

    if not _user_is_admin(request.user):
        _log_denied_admin_panel_access(request)
        messages.error(request, 'Admin access required.')
        return redirect('sitesync:site_list')

    serializer = ConsumptionDisplayQuerySerializer(data=request.GET)
    if not serializer.is_valid():
        return JsonResponse({'errors': serializer.errors}, status=400)

    payload = _build_consumption_display_payload(serializer.validated_data)
    rows = payload.get('records', [])

    response = HttpResponse(content_type='text/csv')
    filename = f"import_review_{payload['data_type']}_{payload['reporting_month']}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.DictWriter(
        response,
        fieldnames=[
            'supply_name',
            'supply_external_id',
            'source_period_start',
            'source_period_end',
            'canonical_month_key',
            'value',
            'data_type',
        ],
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({
            'supply_name': row.get('supply_name') or '',
            'supply_external_id': row.get('supply_external_id') or '',
            'source_period_start': row.get('source_period_start') or '',
            'source_period_end': row.get('source_period_end') or '',
            'canonical_month_key': row.get('canonical_month_key') or '',
            'value': row.get('value') or '',
            'data_type': row.get('data_type') or payload['data_type'],
        })
    return response


@login_required(login_url='/login/')
def admin_import_review_export_xlsx_view(request):
    """Export the current filtered import-review view to XLSX."""

    if not _user_is_admin(request.user):
        _log_denied_admin_panel_access(request)
        messages.error(request, 'Admin access required.')
        return redirect('sitesync:site_list')

    serializer = ConsumptionDisplayQuerySerializer(data=request.GET)
    if not serializer.is_valid():
        return JsonResponse({'errors': serializer.errors}, status=400)

    payload = _build_consumption_display_payload(serializer.validated_data)
    rows = payload.get('records', [])

    def _excel_safe(value):
        if isinstance(value, datetime):
            if dj_timezone.is_aware(value):
                return dj_timezone.make_naive(value, datetime_timezone.utc)
            return value
        return value

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Import Review'
    headers = [
        'supply_name',
        'supply_external_id',
        'source_period_start',
        'source_period_end',
        'canonical_month_key',
        'value',
        'data_type',
    ]
    worksheet.append(headers)
    for row in rows:
        worksheet.append([
            row.get('supply_name') or '',
            row.get('supply_external_id') or '',
            _excel_safe(row.get('source_period_start')) or '',
            _excel_safe(row.get('source_period_end')) or '',
            row.get('canonical_month_key') or '',
            row.get('value') or '',
            row.get('data_type') or payload['data_type'],
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"import_review_{payload['data_type']}_{payload['reporting_month']}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    workbook.save(response)
    return response


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
        _log_audit_event(
            request,
            action_type=AUDIT_ACTION_ACCESS_DENIED,
            action_outcome=AuditLogEntry.OUTCOME_DENIED,
            target_entity_type='team',
            target_entity_id=str(team_id),
            target_entity_label='team_detail',
            message='Denied team detail access.',
            metadata={'reason': 'team_scope_required'},
        )
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
            _log_audit_event(
                request,
                action_type=AUDIT_ACTION_ACCESS_DENIED,
                action_outcome=AuditLogEntry.OUTCOME_DENIED,
                target_entity_type='team',
                target_entity_id=str(team.id),
                target_entity_label=team.name,
                message='Denied team update attempt.',
                metadata={'reason': 'team_admin_or_manager_required'},
            )
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
            _log_audit_event(
                request,
                action_type=AUDIT_ACTION_ADMIN_ADD_SUB_TEAM,
                action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
                target_entity_type='team',
                target_entity_id=str(sub_team.id),
                target_entity_label=sub_team.name,
                message=f"Added {sub_team.name} as sub-team of {team.name}.",
                metadata={'parent_team_id': str(team.id), 'parent_team_name': team.name},
            )
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
            _log_audit_event(
                request,
                action_type=AUDIT_ACTION_ADMIN_UPDATE_TEAM,
                action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
                target_entity_type='team',
                target_entity_id=str(team.id),
                target_entity_label=team.name,
                message=f"Updated team {team.name}.",
                metadata={
                    'level': team.level,
                    'parent_team_id': str(team.parent_team_id) if team.parent_team_id else None,
                    'manager_id': str(team.manager_id) if team.manager_id else None,
                    'team_lead_id': str(team.team_lead_id) if team.team_lead_id else None,
                },
            )
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
            _log_audit_event(
                request,
                action_type=AUDIT_ACTION_ACCESS_DENIED,
                action_outcome=AuditLogEntry.OUTCOME_DENIED,
                target_entity_type='user_team_assignment',
                message='Denied team assignment creation.',
                metadata={'reason': 'admin_or_manager_required'},
            )
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
            _log_audit_event(
                request,
                action_type=AUDIT_ACTION_ADMIN_ASSIGN_TEAM,
                action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
                target_entity_type='user_team_assignment',
                target_entity_id=str(assignment.id),
                target_entity_label=f"{user.get_username()}->{team.name}",
                message=f"Assigned user {user.get_username()} to team {team.name}.",
                metadata={'user_id': str(user.id), 'team_id': str(team.id)},
            )
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
            _log_audit_event(
                request,
                action_type=AUDIT_ACTION_ACCESS_DENIED,
                action_outcome=AuditLogEntry.OUTCOME_DENIED,
                target_entity_type='user_team_assignment',
                message='Denied team assignment deletion.',
                metadata={'reason': 'admin_or_manager_required'},
            )
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        assignment_id = request.GET.get('assignment_id')
        try:
            assignment = UserTeamAssignment.objects.get(id=assignment_id)
            user_name = assignment.user.username
            team_name = assignment.team.name
            assignment_pk = str(assignment.id)
            user_id = str(assignment.user_id)
            team_id = str(assignment.team_id)
            assignment.delete()
            _log_audit_event(
                request,
                action_type=AUDIT_ACTION_ADMIN_UNASSIGN_TEAM,
                action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
                target_entity_type='user_team_assignment',
                target_entity_id=assignment_pk,
                target_entity_label=f"{user_name}->{team_name}",
                message=f"Removed user {user_name} from team {team_name}.",
                metadata={'user_id': user_id, 'team_id': team_id},
            )
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
            _log_audit_event(
                request,
                action_type=AUDIT_ACTION_ACCESS_DENIED,
                action_outcome=AuditLogEntry.OUTCOME_DENIED,
                target_entity_type='role_assignment',
                message='Denied role assignment creation.',
                metadata={'reason': 'admin_required'},
            )
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
            _log_audit_event(
                request,
                action_type=AUDIT_ACTION_ADMIN_ASSIGN_ROLE,
                action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
                target_entity_type='role_assignment',
                target_entity_id=str(assignment.id),
                target_entity_label=f"{user.get_username()}:{role_name}",
                message=f"Assigned role {role_name} to user {user.get_username()}.",
                metadata={'user_id': str(user.id), 'role_name': role_name},
            )
            logger.info(f"User {request.user.username} assigned role {role_name} to {user.username}")
            return JsonResponse({'success': True, 'assignment_id': str(assignment.id)})
        else:
            return JsonResponse({'errors': form.errors}, status=400)
    
    if request.method == 'DELETE':
        if not is_admin:
            _log_audit_event(
                request,
                action_type=AUDIT_ACTION_ACCESS_DENIED,
                action_outcome=AuditLogEntry.OUTCOME_DENIED,
                target_entity_type='role_assignment',
                message='Denied role assignment deletion.',
                metadata={'reason': 'admin_required'},
            )
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        assignment_id = request.GET.get('assignment_id')
        try:
            assignment = RoleAssignment.objects.get(id=assignment_id)
            user_name = assignment.user.username
            role_name = assignment.get_role_name_display()
            assignment_pk = str(assignment.id)
            role_code = assignment.role_name
            user_id = str(assignment.user_id)
            assignment.delete()
            _log_audit_event(
                request,
                action_type=AUDIT_ACTION_ADMIN_REVOKE_ROLE,
                action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
                target_entity_type='role_assignment',
                target_entity_id=assignment_pk,
                target_entity_label=f"{user_name}:{role_name}",
                message=f"Revoked role {role_name} from user {user_name}.",
                metadata={'user_id': user_id, 'role_name': role_code},
            )
            logger.info(f"User {request.user.username} revoked role {role_name} from {user_name}")
            return JsonResponse({'success': True})
        except RoleAssignment.DoesNotExist:
            return JsonResponse({'error': 'Assignment not found'}, status=404)
    
    # GET: List assignments
    assignments = RoleAssignment.objects.all().select_related('user', 'assigned_by')
    assignable_users = get_user_model().objects.filter(is_active=True).order_by('username')
    paginator = Paginator(assignments, 50)
    page = request.GET.get('page', 1)
    
    try:
        assignments_page = paginator.page(page)
    except Exception:
        assignments_page = paginator.page(1)
    
    context = {
        'assignments': assignments_page,
        'is_admin': is_admin,
        'assignable_users': assignable_users,
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
            _log_denied_admin_panel_access(request)
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
        'site_count': Site.objects.count(),
        'fiscal_meter_count': Supply.objects.filter(
            Q(parent_account_id__isnull=True) | Q(parent_account_id='')
        ).count(),
        'submeter_count': Supply.objects.exclude(
            Q(parent_account_id__isnull=True) | Q(parent_account_id='')
        ).count(),
    }
    return render(request, 'sitesync/panel_dashboard.html', context)


@admin_panel_required
def admin_users_view(request):
    """Admin panel users section with invitation and account actions."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    invitation_form = InvitationForm()
    action_form = AccountActionForm()

    users_qs = User.objects.order_by('username')
    invitations = Invitation.objects.order_by('-created_at')
    pending_invitations = invitations.filter(status=Invitation.STATUS_PENDING)

    def _with_invitation_urls(records):
        for item in records:
            item.accept_url = request.build_absolute_uri(
                reverse('sitesync:accept_invitation', kwargs={'invitation_id': item.id})
            )
        return records

    pending_invitations = _with_invitation_urls(list(pending_invitations))

    if request.method == 'POST':
        if 'revoke_invitation' in request.POST:
            invitation_id = (request.POST.get('invitation_id') or '').strip()
            invitation = Invitation.objects.filter(id=invitation_id).first()
            if invitation is None:
                messages.error(request, 'Invitation not found.')
            elif not _revoke_invitation(invitation):
                messages.error(request, 'Only pending invitations can be revoked.')
            else:
                _log_audit_event(
                    request,
                    action_type=AUDIT_ACTION_ADMIN_REVOKE_INVITATION,
                    action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
                    target_entity_type='invitation',
                    target_entity_id=str(invitation.id),
                    target_entity_label=invitation.email,
                    message=f"Revoked invitation for {invitation.email}.",
                )
                messages.success(request, f'Revoked invitation for {invitation.email}.')

        if 'resend_invitation' in request.POST:
            invitation_id = (request.POST.get('invitation_id') or '').strip()
            invitation = Invitation.objects.filter(id=invitation_id).first()
            if invitation is None:
                messages.error(request, 'Invitation not found.')
            elif invitation.status != Invitation.STATUS_PENDING:
                messages.error(request, 'Only pending invitations can be resent.')
            else:
                _activate_and_resend_invitation(request, invitation)
                _log_audit_event(
                    request,
                    action_type=AUDIT_ACTION_ADMIN_RESEND_INVITATION_EMAIL,
                    action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
                    target_entity_type='invitation',
                    target_entity_id=str(invitation.id),
                    target_entity_label=invitation.email,
                    message=f"Resent invitation for {invitation.email}.",
                )
                _send_and_log_invitation_email(
                    request,
                    invitation,
                    action_type=AUDIT_ACTION_ADMIN_SEND_INVITATION_EMAIL,
                    success_message=f"Sent invitation email to {invitation.email}.",
                    failure_message=f"Failed to send invitation email to {invitation.email}: {{error}}",
                )
                messages.warning(request, f'Invitation already exists for {invitation.email}. The pending invitation was resent.')

        if 'create_invitation' in request.POST:
            invitation_form = InvitationForm(request.POST)
            if invitation_form.is_valid():
                email = invitation_form.cleaned_data['email']
                existing_invitation = invitation_form.get_existing_invitation()
                if existing_invitation is not None:
                    if existing_invitation.status == Invitation.STATUS_ACCEPTED:
                        messages.error(request, f'An invitation already exists for {email} and was already accepted.')
                    else:
                        _activate_and_resend_invitation(request, existing_invitation)
                        _log_audit_event(
                            request,
                            action_type=AUDIT_ACTION_ADMIN_RESEND_INVITATION_EMAIL,
                            action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
                            target_entity_type='invitation',
                            target_entity_id=str(existing_invitation.id),
                            target_entity_label=existing_invitation.email,
                            message=f"Resent invitation for {existing_invitation.email}.",
                        )
                        _send_and_log_invitation_email(
                            request,
                            existing_invitation,
                            action_type=AUDIT_ACTION_ADMIN_SEND_INVITATION_EMAIL,
                            success_message=f"Sent invitation email to {existing_invitation.email}.",
                            failure_message=f"Failed to send invitation email to {existing_invitation.email}: {{error}}",
                        )
                        messages.warning(request, f'Invitation already exists for {email}. The pending invitation was resent.')
                else:
                    try:
                        invitation = Invitation.objects.create(
                            email=email,
                            invited_by=request.user,
                        )
                    except IntegrityError:
                        messages.error(request, f'Unable to create invitation for {email}. Please try again.')
                    else:
                        _log_audit_event(
                            request,
                            action_type=AUDIT_ACTION_ADMIN_CREATE_INVITATION,
                            action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
                            target_entity_type='invitation',
                            target_entity_id=str(invitation.id),
                            target_entity_label=invitation.email,
                            message=f"Created invitation for {invitation.email}.",
                        )
                        _send_and_log_invitation_email(
                            request,
                            invitation,
                            action_type=AUDIT_ACTION_ADMIN_SEND_INVITATION_EMAIL,
                            success_message=f"Sent invitation email to {invitation.email}.",
                            failure_message=f"Failed to send invitation email to {invitation.email}: {{error}}",
                        )
                        messages.success(request, f'Created invitation for {email}.')
                invitation_form = InvitationForm()

        elif 'account_action' in request.POST:
            action_form = AccountActionForm(request.POST)
            if action_form.is_valid():
                target_id = request.POST.get('user_id')
                target_user = User.objects.filter(id=target_id).first()
                if target_user is not None:
                    action = action_form.cleaned_data['action']
                    action_type = None
                    message = None
                    target_user_label = target_user.get_username()
                    if action == 'enable':
                        target_user.is_active = True
                        target_user.save(update_fields=['is_active'])
                        action_type = AUDIT_ACTION_ADMIN_ENABLE_USER
                        message = f"Enabled user {target_user_label}."
                    elif action == 'disable':
                        target_user.is_active = False
                        target_user.save(update_fields=['is_active'])
                        action_type = AUDIT_ACTION_ADMIN_DISABLE_USER
                        message = f"Disabled user {target_user_label}."
                    elif action == 'reset_password':
                        target_user.set_password('TempPassword123!')
                        target_user.save(update_fields=['password'])
                        action_type = AUDIT_ACTION_ADMIN_RESET_PASSWORD
                        message = f"Reset password for user {target_user_label}."
                    elif action == 'delete':
                        action_type = AUDIT_ACTION_ADMIN_DELETE_USER
                        message = f"Deleted user {target_user_label}."
                        target_user.delete()

                    if action_form.cleaned_data.get('new_username'):
                        old_username = target_user_label
                        target_user.username = action_form.cleaned_data['new_username']
                        target_user.save(update_fields=['username'])
                        action_type = AUDIT_ACTION_ADMIN_UPDATE_USERNAME
                        target_user_label = target_user.username
                        message = f"Renamed user {old_username} to {target_user.username}."

                    if action_type and message:
                        _log_audit_event(
                            request,
                            action_type=action_type,
                            action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
                            target_entity_type='user',
                            target_entity_id=str(target_id),
                            target_entity_label=target_user_label,
                            message=message,
                        )

        pending_invitations = Invitation.objects.filter(status=Invitation.STATUS_PENDING).order_by('-created_at')
        pending_invitations = _with_invitation_urls(list(pending_invitations))

    paginator = Paginator(users_qs, 20)
    page = request.GET.get('page', 1)

    try:
        users_page = paginator.page(page)
    except Exception:
        users_page = paginator.page(1)

    context = {
        'users': users_page,
        'invitations': invitations,
        'pending_invitations': pending_invitations,
        'invitation_form': invitation_form,
        'action_form': action_form,
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
            _log_audit_event(
                request,
                action_type=AUDIT_ACTION_ADMIN_CREATE_TEAM,
                action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
                target_entity_type='team',
                target_entity_id=str(team.id),
                target_entity_label=team.name,
                message=f"Created team {team.name}.",
                metadata={
                    'level': team.level,
                    'parent_team_id': str(team.parent_team_id) if team.parent_team_id else None,
                },
            )
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
    User = get_user_model()
    
    assignments = RoleAssignment.objects.all().select_related('user', 'assigned_by').order_by('user__username')
    paginator = Paginator(assignments, 50)
    page = request.GET.get('page', 1)
    
    try:
        assignments_page = paginator.page(page)
    except Exception:
        assignments_page = paginator.page(1)
    
    context = {
        'assignments': assignments_page,
        'assignable_users': User.objects.filter(is_active=True).order_by('username'),
    }
    return render(request, 'sitesync/panel_roles.html', context)


@admin_panel_required
def admin_audit_logs_view(request):
    """Render admin audit log viewer with validated filters and pagination."""

    filter_form = AuditLogFilterForm(request.GET)
    entries_page = []
    total_count = 0

    if filter_form.is_valid():
        queryset = get_filtered_audit_logs(filters=filter_form.cleaned_data)
        total_count = queryset.count()
        paginator = Paginator(queryset, 50)
        page_number = request.GET.get('page', 1)
        try:
            entries_page = paginator.page(page_number)
        except Exception:
            entries_page = paginator.page(1)

        _log_audit_event(
            request,
            action_type=AUDIT_ACTION_ADMIN_VIEW_AUDIT_LOG,
            action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
            target_entity_type='audit_log',
            target_entity_id='viewer',
            target_entity_label='viewer',
            message=f"{request.user.get_username()} viewed audit logs.",
            metadata={
                'filters': {
                    'user': str(filter_form.cleaned_data['user'].id) if filter_form.cleaned_data.get('user') else '',
                    'keyword': filter_form.cleaned_data.get('keyword', ''),
                    'start': filter_form.cleaned_data['start'].isoformat() if filter_form.cleaned_data.get('start') else '',
                    'end': filter_form.cleaned_data['end'].isoformat() if filter_form.cleaned_data.get('end') else '',
                    'action_type': filter_form.cleaned_data.get('action_type', ''),
                },
                'total_count': total_count,
            },
        )
    else:
        _log_audit_event(
            request,
            action_type=AUDIT_ACTION_ADMIN_VIEW_AUDIT_LOG,
            action_outcome=AuditLogEntry.OUTCOME_FAILED,
            target_entity_type='audit_log',
            target_entity_id='viewer',
            target_entity_label='viewer',
            message='Audit log viewer request failed validation.',
            metadata={'errors': filter_form.errors.get_json_data()},
        )

    action_types = (
        AuditLogEntry.objects.order_by('action_type')
        .values_list('action_type', flat=True)
        .distinct()
    )
    filter_query = request.GET.copy()
    if 'page' in filter_query:
        del filter_query['page']

    return render(request, 'sitesync/admin_audit_logs.html', {
        'entries': entries_page,
        'filter_form': filter_form,
        'action_types': list(action_types),
        'total_count': total_count,
        'active_filters_querystring': filter_query.urlencode(),
    })


@admin_panel_required
def admin_audit_logs_export_csv_view(request):
    """Export filtered audit rows to CSV using shared filter semantics."""

    filter_form = AuditLogFilterForm(request.GET)
    if not filter_form.is_valid():
        _log_audit_event(
            request,
            action_type=AUDIT_ACTION_ADMIN_EXPORT_AUDIT_LOG,
            action_outcome=AuditLogEntry.OUTCOME_FAILED,
            target_entity_type='audit_log',
            target_entity_id='csv',
            target_entity_label='csv_export',
            message='Audit CSV export failed validation.',
            metadata={'errors': filter_form.errors.get_json_data(), 'format': 'csv'},
        )
        return JsonResponse({'errors': filter_form.errors}, status=400)

    queryset = get_filtered_audit_logs(filters=filter_form.cleaned_data)
    allowed, row_count = check_audit_export_threshold(queryset=queryset, limit=50000)
    if not allowed:
        _log_audit_event(
            request,
            action_type=AUDIT_ACTION_ADMIN_EXPORT_AUDIT_LOG,
            action_outcome=AuditLogEntry.OUTCOME_FAILED,
            target_entity_type='audit_log',
            target_entity_id='csv',
            target_entity_label='csv_export',
            message='Audit CSV export rejected because filter result exceeded threshold.',
            metadata={'format': 'csv', 'row_count': row_count, 'threshold': 50000},
        )
        return JsonResponse({'detail': 'Export exceeds 50000 rows. Please narrow filters.'}, status=400)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
    writer = csv.DictWriter(
        response,
        fieldnames=[
            'utc_timestamp', 'actor_username', 'source_ip', 'action_type', 'action_outcome',
            'target_entity_type', 'target_entity_id', 'target_entity_label', 'message', 'request_path',
        ],
    )
    writer.writeheader()
    for entry in queryset:
        writer.writerow(serialize_audit_entry_for_export(entry))

    _log_audit_event(
        request,
        action_type=AUDIT_ACTION_ADMIN_EXPORT_AUDIT_LOG,
        action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
        target_entity_type='audit_log',
        target_entity_id='csv',
        target_entity_label='csv_export',
        message=f"{request.user.get_username()} exported audit logs to CSV.",
        metadata={'format': 'csv', 'row_count': row_count},
    )
    return response


@admin_panel_required
def admin_audit_logs_export_xlsx_view(request):
    """Export filtered audit rows to XLSX using shared filter semantics."""

    filter_form = AuditLogFilterForm(request.GET)
    if not filter_form.is_valid():
        _log_audit_event(
            request,
            action_type=AUDIT_ACTION_ADMIN_EXPORT_AUDIT_LOG,
            action_outcome=AuditLogEntry.OUTCOME_FAILED,
            target_entity_type='audit_log',
            target_entity_id='xlsx',
            target_entity_label='xlsx_export',
            message='Audit XLSX export failed validation.',
            metadata={'errors': filter_form.errors.get_json_data(), 'format': 'xlsx'},
        )
        return JsonResponse({'errors': filter_form.errors}, status=400)

    queryset = get_filtered_audit_logs(filters=filter_form.cleaned_data)
    allowed, row_count = check_audit_export_threshold(queryset=queryset, limit=50000)
    if not allowed:
        _log_audit_event(
            request,
            action_type=AUDIT_ACTION_ADMIN_EXPORT_AUDIT_LOG,
            action_outcome=AuditLogEntry.OUTCOME_FAILED,
            target_entity_type='audit_log',
            target_entity_id='xlsx',
            target_entity_label='xlsx_export',
            message='Audit XLSX export rejected because filter result exceeded threshold.',
            metadata={'format': 'xlsx', 'row_count': row_count, 'threshold': 50000},
        )
        return JsonResponse({'detail': 'Export exceeds 50000 rows. Please narrow filters.'}, status=400)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Audit Logs'
    headers = [
        'utc_timestamp', 'actor_username', 'source_ip', 'action_type', 'action_outcome',
        'target_entity_type', 'target_entity_id', 'target_entity_label', 'message', 'request_path',
    ]
    worksheet.append(headers)
    for entry in queryset:
        row = serialize_audit_entry_for_export(entry)
        worksheet.append([row[h] for h in headers])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="audit_logs.xlsx"'
    workbook.save(response)

    _log_audit_event(
        request,
        action_type=AUDIT_ACTION_ADMIN_EXPORT_AUDIT_LOG,
        action_outcome=AuditLogEntry.OUTCOME_SUCCESS,
        target_entity_type='audit_log',
        target_entity_id='xlsx',
        target_entity_label='xlsx_export',
        message=f"{request.user.get_username()} exported audit logs to XLSX.",
        metadata={'format': 'xlsx', 'row_count': row_count},
    )
    return response


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
    from .models import Team, UserTeamAssignment
    from django.db.models import Q
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Check if user already has team assignments
    has_team_context = (
        UserTeamAssignment.objects.filter(user=request.user).exists()
        or Team.objects.filter(Q(manager=request.user) | Q(team_lead=request.user)).exists()
    )
    if has_team_context:
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
