"""
Data models for the Etainabl site and supply synchronization.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Site(models.Model):
    """
    Represents a site (property/asset) from the Etainabl platform.
    """
    id = models.BigAutoField(primary_key=True)
    external_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Unique identifier from Etainabl API (asset ID)"
    )
    name = models.CharField(
        max_length=500,
        help_text="Site name from Etainabl API"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Site description"
    )
    floor_area = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        blank=True,
        null=True,
        help_text="Site floor area from Etainabl asset data"
    )
    floor_area_unit = models.CharField(
        max_length=16,
        blank=True,
        null=True,
        help_text="Original Etainabl floor area unit (sqm or sqft)"
    )
    team = models.ForeignKey(
        'Team',
        on_delete=models.SET_NULL,
        related_name='sites',
        null=True,
        blank=True,
        help_text='Owning team used for report access scope and ownership fallback checks',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['external_id']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name


class Supply(models.Model):
    """
    Represents a supply (account/meter) associated with a site.
    """
    UTILITY_CHOICES = [
        ('electricity', 'Electricity'),
        ('gas', 'Gas'),
        ('water', 'Water'),
        ('other', 'Other'),
    ]

    id = models.BigAutoField(primary_key=True)
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name='supplies',
        help_text="Associated site"
    )
    external_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Unique identifier from Etainabl API (account ID)"
    )
    name = models.CharField(
        max_length=500,
        help_text="Supply name from Etainabl API"
    )
    utility_type = models.CharField(
        max_length=20,
        choices=UTILITY_CHOICES,
        default='other',
        help_text="Type of utility supply"
    )
    device_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Device ID (meter/sensor identifier)"
    )
    available_capacity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Available capacity in kVA"
    )
    parent_account_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        help_text="Parent fiscal meter account ID from Etainabl parentAccountId"
    )
    status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        db_index=True,
        help_text="Supply status from Etainabl (for example: active/inactive)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['external_id']),
            models.Index(fields=['site', 'name']),
            models.Index(fields=['site', 'parent_account_id']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_utility_type_display()})"


class Benchmark(models.Model):
    """Configured benchmark value for a supply and month."""

    UNIT_CHOICES = [
        ('kWh', 'kWh'),
        ('m3', 'm3'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supply = models.ForeignKey(Supply, on_delete=models.CASCADE, related_name='benchmarks')
    canonical_month_key = models.CharField(max_length=7, db_index=True)
    value = models.DecimalField(max_digits=16, decimal_places=6)
    unit = models.CharField(max_length=3, choices=UNIT_CHOICES, default='kWh')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-canonical_month_key']
        constraints = [
            models.UniqueConstraint(
                fields=['supply', 'canonical_month_key'],
                name='uniq_benchmark_supply_month',
            ),
        ]
        indexes = [
            models.Index(fields=['supply', 'canonical_month_key']),
            models.Index(fields=['canonical_month_key']),
        ]

    def __str__(self):
        return f"Benchmark {self.supply_id} {self.canonical_month_key}"


class Invitation(models.Model):
    """Represents an invitation to join the platform."""

    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REVOKED = 'revoked'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REVOKED, 'Revoked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    expires_at = models.DateTimeField(blank=True, null=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    revoked_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def is_valid(self):
        return self.status == self.STATUS_PENDING

    def accept(self):
        if not self.is_valid():
            return False
        self.status = self.STATUS_ACCEPTED
        self.accepted_at = timezone.now()
        self.save(update_fields=['status', 'accepted_at', 'updated_at'])
        return True

    def revoke(self):
        if self.status != self.STATUS_PENDING:
            return False
        self.status = self.STATUS_REVOKED
        self.revoked_at = timezone.now()
        self.save(update_fields=['status', 'revoked_at', 'updated_at'])
        return True

    def __str__(self):
        return f"Invitation for {self.email}"


class AppSettings(models.Model):
    """
    Application settings that can be edited and persisted in the database.
    Allows runtime configuration to override .env values.
    """
    etainabl_api_url = models.URLField(
        default='https://api.etainabl.com/2.0',
        help_text="Base URL for Etainabl API"
    )
    page_size = models.IntegerField(
        default=50,
        help_text="Number of records to fetch per API request"
    )
    api_timeout = models.IntegerField(
        default=30,
        help_text="API request timeout in seconds"
    )
    electricity_benchmark_intensity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        help_text="Electricity benchmark intensity in kWh per square metre per year"
    )
    gas_benchmark_intensity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        help_text="Gas benchmark intensity in kWh per square metre per year"
    )
    water_benchmark_intensity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        help_text="Water benchmark intensity in m3 per square metre per year"
    )
    invoice_page_limit = models.IntegerField(
        default=100,
        help_text="Number of invoice records to fetch per API page"
    )
    invoice_start_page = models.IntegerField(
        default=1,
        help_text="Page number invoice downloads start from"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "App Settings"

    def __str__(self):
        return "Application Settings"


class CapacityReference(models.Model):
    """Persisted capacity values keyed by normalized eSight meter code."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=500)
    esight_meter_code = models.CharField(max_length=255, unique=True, db_index=True)
    available_capacity_kva = models.DecimalField(max_digits=12, decimal_places=3, blank=True, null=True)
    source_filename = models.CharField(max_length=255, blank=True, null=True)
    last_imported_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['esight_meter_code']
        indexes = [
            models.Index(fields=['esight_meter_code']),
            models.Index(fields=['last_imported_at']),
        ]

    def __str__(self):
        return f"CapacityReference {self.esight_meter_code}"


class CapacityUploadRun(models.Model):
    """Tracks each available-capacity upload result summary."""

    STATUS_SUCCESS = 'success'
    STATUS_PARTIAL_SUCCESS = 'partial_success'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Success'),
        (STATUS_PARTIAL_SUCCESS, 'Partial Success'),
        (STATUS_FAILED, 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_filename = models.CharField(max_length=255, blank=True, null=True)
    total_rows = models.IntegerField(default=0)
    accepted_rows = models.IntegerField(default=0)
    rejected_rows = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUCCESS)
    error_summary = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['uploaded_at']),
        ]

    def __str__(self):
        return f"CapacityUploadRun {self.uploaded_at.isoformat()} ({self.status})"


class CapacityUploadRowResult(models.Model):
    """Persists per-row upload outcomes for workbook export."""

    OUTCOME_SUCCESS = 'success'
    OUTCOME_FAILURE = 'failure'
    OUTCOME_CHOICES = [
        (OUTCOME_SUCCESS, 'Success'),
        (OUTCOME_FAILURE, 'Failure'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(
        CapacityUploadRun,
        on_delete=models.CASCADE,
        related_name='row_results',
    )
    source_row_number = models.PositiveIntegerField()
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES)
    explanation = models.TextField(blank=True, default='')
    original_columns = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['source_row_number', 'created_at']
        indexes = [
            models.Index(fields=['run', 'outcome']),
            models.Index(fields=['run', 'source_row_number']),
        ]

    def __str__(self):
        return f"CapacityUploadRowResult {self.run_id} row={self.source_row_number} ({self.outcome})"


class ImportRun(models.Model):
    """Tracks import lifecycle and aggregate outcomes for a request."""

    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_SUCCESS = 'success'
    STATUS_PARTIAL_FAILURE = 'partial_failure'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_PARTIAL_FAILURE, 'Partial Failure'),
        (STATUS_FAILED, 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    selected_supply_ids = models.JSONField(default=list)
    reporting_month = models.CharField(max_length=7, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    affected_supply_count = models.IntegerField(default=0)
    records_imported = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    retry_count = models.IntegerField(default=0)
    error_details = models.JSONField(default=dict, blank=True)
    outcome_details = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reporting_month']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"ImportRun {self.id} ({self.reporting_month})"


class HalfHourlyConsumption(models.Model):
    """Half-hourly consumption values imported from Xcelerate."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    import_run = models.ForeignKey(
        ImportRun,
        on_delete=models.CASCADE,
        related_name='halfhourly_records',
    )
    supply = models.ForeignKey(Supply, on_delete=models.CASCADE, related_name='halfhourly_consumption')
    canonical_month_key = models.CharField(max_length=7, db_index=True)
    source_period_start = models.DateTimeField()
    source_period_end = models.DateTimeField()
    consumption = models.DecimalField(max_digits=16, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-source_period_start']
        constraints = [
            models.UniqueConstraint(
                fields=['supply', 'source_period_start', 'source_period_end'],
                name='uniq_hh_supply_period',
            ),
        ]
        indexes = [
            models.Index(fields=['canonical_month_key']),
            models.Index(fields=['supply', 'canonical_month_key']),
            models.Index(fields=['import_run']),
        ]

    def __str__(self):
        return f"HH {self.supply_id} {self.canonical_month_key}"


class MonthlyConsumption(models.Model):
    """Monthly consumption records imported from Xcelerate."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    import_run = models.ForeignKey(
        ImportRun,
        on_delete=models.CASCADE,
        related_name='monthly_records',
    )
    supply = models.ForeignKey(Supply, on_delete=models.CASCADE, related_name='monthly_consumption')
    canonical_month_key = models.CharField(max_length=7, db_index=True)
    source_period_start = models.DateTimeField()
    source_period_end = models.DateTimeField()
    consumption = models.DecimalField(max_digits=16, decimal_places=6)
    breakdown = models.JSONField(default=dict, blank=True)
    sources = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-source_period_start']
        constraints = [
            models.UniqueConstraint(
                fields=['supply', 'source_period_start', 'source_period_end'],
                name='uniq_monthly_supply_period',
            ),
        ]
        indexes = [
            models.Index(fields=['canonical_month_key']),
            models.Index(fields=['supply', 'canonical_month_key']),
            models.Index(fields=['import_run']),
        ]

    def __str__(self):
        return f"Monthly {self.supply_id} {self.canonical_month_key}"


class InvoiceCost(models.Model):
    """Invoice cost records imported from Xcelerate invoices endpoint."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    import_run = models.ForeignKey(
        ImportRun,
        on_delete=models.CASCADE,
        related_name='invoice_records',
    )
    supply = models.ForeignKey(Supply, on_delete=models.CASCADE, related_name='invoice_costs')
    canonical_month_key = models.CharField(max_length=7, db_index=True)
    source_period_start = models.DateTimeField()
    source_period_end = models.DateTimeField()
    cost = models.DecimalField(max_digits=16, decimal_places=6)
    invoice_metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-source_period_start']
        constraints = [
            models.UniqueConstraint(
                fields=['supply', 'source_period_start', 'source_period_end'],
                name='uniq_invoice_supply_period',
            ),
        ]
        indexes = [
            models.Index(fields=['canonical_month_key']),
            models.Index(fields=['supply', 'canonical_month_key']),
            models.Index(fields=['import_run']),
        ]

    def __str__(self):
        return f"Invoice {self.supply_id} {self.canonical_month_key}"


class MonthlyReport(models.Model):
    """One report identity per site and reporting month."""

    STATUS_DRAFT = 'draft'
    STATUS_FINAL = 'final'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_FINAL, 'Final'),
    ]

    VALIDATION_DRAFT = 'draft'
    VALIDATION_AWAITING = 'awaiting_validation'
    VALIDATION_VALIDATED = 'validated'
    VALIDATION_STATUS_CHOICES = [
        (VALIDATION_DRAFT, 'Draft'),
        (VALIDATION_AWAITING, 'Awaiting Validation'),
        (VALIDATION_VALIDATED, 'Validated'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='monthly_reports')
    reporting_month = models.CharField(max_length=7, db_index=True)
    current_status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    validation_status = models.CharField(
        max_length=32,
        choices=VALIDATION_STATUS_CHOICES,
        default=VALIDATION_DRAFT,
        db_index=True,
    )
    validator_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='validated_monthly_reports',
        null=True,
        blank=True,
    )
    validator_assigned_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='validation_assignments_made',
        null=True,
        blank=True,
    )
    validator_assigned_at = models.DateTimeField(null=True, blank=True)
    validated_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='monthly_reports_validated',
        null=True,
        blank=True,
    )
    validated_at = models.DateTimeField(null=True, blank=True)
    validation_reopened_at = models.DateTimeField(null=True, blank=True)
    current_version = models.ForeignKey(
        'MonthlyReportVersion',
        on_delete=models.SET_NULL,
        related_name='+',
        null=True,
        blank=True,
    )
    current_final_version = models.ForeignKey(
        'MonthlyReportVersion',
        on_delete=models.SET_NULL,
        related_name='+',
        null=True,
        blank=True,
    )
    owner_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='owned_monthly_reports',
        null=True,
        blank=True,
    )
    created_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_monthly_reports',
        null=True,
        blank=True,
    )
    last_modified_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='last_modified_monthly_reports',
        null=True,
        blank=True,
    )
    last_modified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-reporting_month', '-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['site', 'reporting_month'],
                name='uniq_monthly_report_site_month',
            ),
        ]
        indexes = [
            models.Index(fields=['site', 'reporting_month']),
            models.Index(fields=['current_status']),
            models.Index(fields=['validation_status']),
            models.Index(fields=['validator_user', 'validation_status']),
            models.Index(fields=['owner_user']),
            models.Index(fields=['site', 'owner_user', 'current_status']),
        ]

    def __str__(self):
        return f"MonthlyReport {self.site_id} {self.reporting_month}"


class MonthlyReportVersion(models.Model):
    """Immutable snapshot of report content for a monthly report."""

    KIND_DRAFT = 'draft'
    KIND_FINAL = 'final'
    KIND_REPLACEMENT_FINAL = 'replacement_final'
    KIND_CHOICES = [
        (KIND_DRAFT, 'Draft'),
        (KIND_FINAL, 'Final'),
        (KIND_REPLACEMENT_FINAL, 'Replacement Final'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(MonthlyReport, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    version_kind = models.CharField(max_length=24, choices=KIND_CHOICES, default=KIND_DRAFT)
    derived_from_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        related_name='derived_versions',
        null=True,
        blank=True,
    )
    selected_supply_ids = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['report', 'version_number'],
                name='uniq_report_version_number',
            ),
        ]
        indexes = [
            models.Index(fields=['report', 'version_kind']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"ReportVersion {self.report_id} v{self.version_number} ({self.version_kind})"


class ReportComment(models.Model):
    """Comment text for a specific visual box in a report version."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_version = models.ForeignKey(MonthlyReportVersion, on_delete=models.CASCADE, related_name='comments')
    visual_key = models.CharField(max_length=255)
    text = models.TextField(blank=True, default='')
    is_reference_copy = models.BooleanField(default=False)
    source_reporting_month = models.CharField(max_length=7, blank=True, null=True)
    source_version = models.ForeignKey(
        MonthlyReportVersion,
        on_delete=models.SET_NULL,
        related_name='copied_comments',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['visual_key']
        constraints = [
            models.UniqueConstraint(
                fields=['report_version', 'visual_key'],
                name='uniq_comment_version_visual',
            ),
        ]
        indexes = [
            models.Index(fields=['report_version', 'visual_key']),
            models.Index(fields=['is_reference_copy']),
        ]

    def __str__(self):
        return f"ReportComment {self.report_version_id} {self.visual_key}"


class ReportPageValidationState(models.Model):
    """Per-page validation state for a monthly report."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(MonthlyReport, on_delete=models.CASCADE, related_name='page_validation_states')
    page_key = models.CharField(max_length=255)
    is_validated = models.BooleanField(default=False)
    validated_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='validated_report_pages',
        null=True,
        blank=True,
    )
    validated_at = models.DateTimeField(null=True, blank=True)
    reset_reason = models.CharField(max_length=32, blank=True, null=True)
    reset_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['page_key']
        constraints = [
            models.UniqueConstraint(
                fields=['report', 'page_key'],
                name='uniq_report_page_validation_state',
            ),
        ]
        indexes = [
            models.Index(fields=['report', 'is_validated']),
            models.Index(fields=['report', 'page_key']),
        ]

    def __str__(self):
        return f"ReportPageValidationState {self.report_id} {self.page_key}"


class ReportValidationComment(models.Model):
    """Validation commentary for a report page."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(MonthlyReport, on_delete=models.CASCADE, related_name='validation_comments')
    page_key = models.CharField(max_length=255)
    comment_text = models.TextField(blank=True, default='')
    authored_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='authored_report_validation_comments',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['page_key', 'updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['report', 'page_key', 'authored_by_user'],
                name='uniq_report_validation_comment_author_page',
            ),
        ]
        indexes = [
            models.Index(fields=['report', 'page_key']),
        ]

    def __str__(self):
        return f"ReportValidationComment {self.report_id} {self.page_key}"


class ReportValidationEvent(models.Model):
    """Immutable audit event for report validation workflow actions."""

    EVENT_VALIDATOR_ASSIGNED = 'validator_assigned'
    EVENT_VALIDATOR_REASSIGNED = 'validator_reassigned'
    EVENT_PAGE_VALIDATED = 'page_validated'
    EVENT_PAGE_RESET = 'page_reset'
    EVENT_REPORT_VALIDATED = 'report_validated'
    EVENT_FINAL_BLOCKED = 'final_blocked'
    EVENT_FINAL_REOPENED = 'final_reopened'
    EVENT_CHOICES = [
        (EVENT_VALIDATOR_ASSIGNED, 'Validator Assigned'),
        (EVENT_VALIDATOR_REASSIGNED, 'Validator Reassigned'),
        (EVENT_PAGE_VALIDATED, 'Page Validated'),
        (EVENT_PAGE_RESET, 'Page Reset'),
        (EVENT_REPORT_VALIDATED, 'Report Validated'),
        (EVENT_FINAL_BLOCKED, 'Final Blocked'),
        (EVENT_FINAL_REOPENED, 'Final Reopened'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(MonthlyReport, on_delete=models.CASCADE, related_name='validation_events')
    page_key = models.CharField(max_length=255, blank=True, null=True)
    event_type = models.CharField(max_length=32, choices=EVENT_CHOICES)
    event_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='report_validation_events',
        null=True,
        blank=True,
    )
    event_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-event_at']
        indexes = [
            models.Index(fields=['report', 'event_at']),
            models.Index(fields=['event_type', 'event_at']),
        ]

    def __str__(self):
        return f"ReportValidationEvent {self.report_id} {self.event_type}"


class ReportWriteGrant(models.Model):
    """Owner-managed named-user report write delegation."""

    ROLE_OWNER = 'owner'
    ROLE_TEAM_LEAD = 'team_lead'
    ROLE_MANAGER = 'manager'
    ROLE_CHOICES = [
        (ROLE_OWNER, 'Owner'),
        (ROLE_TEAM_LEAD, 'Team Lead'),
        (ROLE_MANAGER, 'Manager'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(MonthlyReport, on_delete=models.CASCADE, related_name='write_grants')
    granted_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='report_write_grants',
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='report_write_grants_issued',
        null=True,
        blank=True,
    )
    granted_by_role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_OWNER)
    granted_at = models.DateTimeField(auto_now_add=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='report_write_grants_revoked',
        null=True,
        blank=True,
    )
    revoked_by_role = models.CharField(max_length=20, choices=ROLE_CHOICES, null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-granted_at']
        constraints = [
            models.UniqueConstraint(
                fields=['report', 'granted_user'],
                condition=models.Q(is_active=True),
                name='uniq_active_report_write_grant',
            ),
        ]
        indexes = [
            models.Index(fields=['report', 'is_active']),
            models.Index(fields=['granted_user']),
        ]

    def __str__(self):
        state = 'active' if self.is_active else 'revoked'
        return f"ReportWriteGrant {self.report_id} -> {self.granted_user_id} ({state})"


class ReportWriteDelegationEvent(models.Model):
    """Immutable grant/revoke event log for delegated write access."""

    ACTION_GRANT = 'grant'
    ACTION_REVOKE = 'revoke'
    ACTION_CHOICES = [
        (ACTION_GRANT, 'Grant'),
        (ACTION_REVOKE, 'Revoke'),
    ]

    RESOLUTION_LAST_WRITE_WINS = 'last_write_wins_timestamp'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(MonthlyReport, on_delete=models.CASCADE, related_name='delegation_events')
    delegate_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='report_delegation_events',
    )
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    action_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='report_delegation_events_by_actor',
        null=True,
        blank=True,
    )
    action_by_role = models.CharField(max_length=20, choices=ReportWriteGrant.ROLE_CHOICES)
    action_at = models.DateTimeField(auto_now_add=True)
    correlation_key = models.UUIDField(null=True, blank=True)
    resolution_basis = models.CharField(max_length=64, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-action_at']
        indexes = [
            models.Index(fields=['report', 'action_at']),
            models.Index(fields=['delegate_user', 'action_at']),
            models.Index(fields=['correlation_key']),
        ]

    def __str__(self):
        return f"ReportWriteDelegationEvent {self.report_id} {self.action} {self.delegate_user_id}"


class ReportOwnershipUnavailabilityApproval(models.Model):
    """Approval record that gates automatic fallback ownership transfer."""

    STATUS_APPROVED = 'approved'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_APPROVED, 'Approved'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(MonthlyReport, on_delete=models.CASCADE, related_name='unavailability_approvals')
    owner_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ownership_unavailability_records',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ownership_unavailability_approvals',
    )
    approval_reason = models.TextField()
    approved_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_APPROVED)

    class Meta:
        ordering = ['-approved_at']
        indexes = [
            models.Index(fields=['report', 'status']),
            models.Index(fields=['approved_at']),
        ]

    def __str__(self):
        return f"OwnershipApproval {self.report_id} ({self.status})"


class ReportOwnershipTransferEvent(models.Model):
    """Auditable ownership transfer event for a monthly report."""

    MODE_AUTO_FALLBACK = 'auto_fallback'
    MODE_MANUAL_TRANSFER = 'manual_owner_transfer'
    MODE_CHOICES = [
        (MODE_AUTO_FALLBACK, 'Auto Fallback'),
        (MODE_MANUAL_TRANSFER, 'Manual Owner Transfer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(MonthlyReport, on_delete=models.CASCADE, related_name='ownership_transfers')
    from_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='ownership_transfers_from',
        null=True,
        blank=True,
    )
    to_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ownership_transfers_to',
    )
    transfer_mode = models.CharField(max_length=32, choices=MODE_CHOICES)
    transfer_reason = models.TextField(blank=True)
    approval_record = models.ForeignKey(
        ReportOwnershipUnavailabilityApproval,
        on_delete=models.SET_NULL,
        related_name='transfer_events',
        null=True,
        blank=True,
    )
    transferred_at = models.DateTimeField(auto_now_add=True)
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='ownership_transfers_executed',
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-transferred_at']
        indexes = [
            models.Index(fields=['report', 'transferred_at']),
            models.Index(fields=['to_owner', 'transferred_at']),
        ]

    def __str__(self):
        return f"OwnershipTransfer {self.report_id} -> {self.to_owner_id}"

class Team(models.Model):
    """
    Represents a hierarchical team/group within the organisation.
    Teams can have parent teams (sub-teams) and contain users.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Display name for the team"
    )
    level = models.PositiveIntegerField(
        default=1,
        db_index=True,
        help_text="Hierarchy level (root teams are level 1, sub-teams increment by 1)"
    )
    parent_team = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        related_name='sub_teams',
        null=True,
        blank=True,
        help_text="Parent team for hierarchical structure (null for root teams)"
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='managed_teams',
        null=True,
        blank=True,
        help_text="User assigned as team manager"
    )
    team_lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='led_teams',
        null=True,
        blank=True,
        help_text="User assigned as team lead"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['manager']),
            models.Index(fields=['parent_team']),
        ]

    def __str__(self):
        if self.parent_team:
            return f'{self.parent_team.name} → {self.name}'
        return self.name

    def get_parent_teams(self):
        """Recursively get all parent teams up the hierarchy."""
        parents = []
        current = self.parent_team
        while current:
            parents.append(current)
            current = current.parent_team
        return parents

    def get_sub_teams(self):
        """Recursively get all sub-teams within this team."""
        subs = list(self.sub_teams.all())
        for sub in self.sub_teams.all():
            subs.extend(sub.get_sub_teams())
        return subs

    def get_all_teams_in_scope(self):
        """Get this team and all sub-teams (used for access scoping)."""
        return [self] + self.get_sub_teams()


class UserTeamAssignment(models.Model):
    """
    Tracks the assignment of a user to a team.
    A user can be assigned to multiple teams.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_assignments',
        help_text="User assigned to the team"
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='user_assignments',
        help_text="Team the user is assigned to"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='team_assignments_made',
        null=True,
        blank=True,
        help_text="Administrator who performed the assignment"
    )

    def get_report_scope(self):
        """
        Returns all reports accessible via this team assignment based on user role.
        
        Access scope:
        - Regular user: Only assigned team's reports
        - Team lead: Assigned team + sub-teams' reports
        - Manager: Assigned team + all sub-teams' reports
        - Admin: All reports
        
        Returns:
            QuerySet of MonthlyReport objects accessible via this assignment
        """
        from django.db.models import Q
        
        # Get user's roles
        roles = RoleAssignment.objects.filter(
            user=self.user
        ).values_list('role_name', flat=True)
        role_list = list(roles)
        
        # Build list of accessible team IDs
        accessible_team_ids = {self.team.id}
        
        # If manager or team lead, include sub-teams
        if 'manager' in role_list or 'team_lead' in role_list:
            sub_teams = self.team.get_sub_teams()
            accessible_team_ids.update([t.id for t in sub_teams])
        
        # TODO: When Site.team is implemented, filter by accessible_team_ids
        # For now, return all reports
        from sitesync.models import MonthlyReport
        return MonthlyReport.objects.all()

    class Meta:
        ordering = ['team__name', 'user__username']
        unique_together = [['user', 'team']]
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['team']),
            models.Index(fields=['user', 'team']),
        ]

    def __str__(self):
        return f"{self.user.username} → {self.team.name}"


class RoleAssignment(models.Model):
    """
    Represents multi-valued role assignments to users.
    A user can hold multiple roles (admin, manager, team_lead, user) simultaneously.
    """
    ROLE_ADMIN = 'admin'
    ROLE_MANAGER = 'manager'
    ROLE_TEAM_LEAD = 'team_lead'
    ROLE_USER = 'user'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Administrator'),
        (ROLE_MANAGER, 'Manager'),
        (ROLE_TEAM_LEAD, 'Team Lead'),
        (ROLE_USER, 'User'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='role_assignments',
        help_text="User being assigned a role"
    )
    role_name = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        help_text="The role being assigned"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='role_assignments_made',
        null=True,
        blank=True,
        help_text="Administrator who assigned the role"
    )

    class Meta:
        ordering = ['user__username', 'role_name']
        unique_together = [['user', 'role_name']]
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['role_name']),
            models.Index(fields=['user', 'role_name']),
        ]

    def __str__(self):
        return f"{self.user.username} → {self.get_role_name_display()}"


class AuditLogEntry(models.Model):
    """Immutable audit trail entry for security and compliance review."""

    OUTCOME_SUCCESS = 'SUCCESS'
    OUTCOME_DENIED = 'DENIED'
    OUTCOME_FAILED = 'FAILED'
    OUTCOME_CHOICES = [
        (OUTCOME_SUCCESS, 'Success'),
        (OUTCOME_DENIED, 'Denied'),
        (OUTCOME_FAILED, 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    occurred_at_utc = models.DateTimeField(default=timezone.now, db_index=True)
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='audit_log_entries',
        null=True,
        blank=True,
    )
    actor_username_snapshot = models.CharField(max_length=150)
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    action_type = models.CharField(max_length=64, db_index=True)
    action_outcome = models.CharField(max_length=16, choices=OUTCOME_CHOICES, db_index=True)
    target_entity_type = models.CharField(max_length=64, db_index=True)
    target_entity_id = models.CharField(max_length=128, null=True, blank=True)
    target_entity_label = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField()
    request_path = models.CharField(max_length=255, null=True, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    retention_class = models.CharField(max_length=50, default='standard')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-occurred_at_utc', '-created_at']
        indexes = [
            models.Index(fields=['actor_user', 'occurred_at_utc']),
            models.Index(fields=['action_type', 'occurred_at_utc']),
            models.Index(fields=['target_entity_type']),
        ]

    def __str__(self):
        return f"{self.occurred_at_utc.isoformat()} {self.action_type} {self.action_outcome}"


# Utility functions for role and team access control (Phase 4)

def has_user_role(user, role_name):
    """Check if a user has a specific role."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Check if is staff or superuser
    if user.is_staff or user.is_superuser:
        return role_name in ['admin', 'manager']
    
    # Check role assignments
    return RoleAssignment.objects.filter(
        user=user,
        role_name=role_name
    ).exists()


def get_user_roles(user):
    """Get all roles assigned to a user."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    roles = list(RoleAssignment.objects.filter(user=user).values_list('role_name', flat=True))
    
    # Add implicit roles
    if user.is_staff or user.is_superuser:
        if 'admin' not in roles:
            roles.append('admin')
        if 'manager' not in roles:
            roles.append('manager')
    
    return roles


def is_user_admin_or_manager(user):
    """Check if a user is an admin or manager."""
    return (
        user.is_staff or 
        user.is_superuser or
        has_user_role(user, 'admin') or
        has_user_role(user, 'manager')
    )


def get_user_teams(user):
    """Get all teams a user is assigned to."""
    return Team.objects.filter(
        user_assignments__user=user
    ).distinct()


def get_user_managed_teams(user):
    """Get all teams managed by a user."""
    return Team.objects.filter(manager=user)


def get_user_led_teams(user):
    """Get all teams led by a user."""
    return Team.objects.filter(team_lead=user)


def get_user_accessible_teams(user):
    """Get all teams accessible to a user (owned, managed, or assigned to)."""
    managed_teams = get_user_managed_teams(user)
    led_teams = get_user_led_teams(user)
    assigned_teams = get_user_teams(user)
    
    return Team.objects.filter(
        models.Q(manager=user) | 
        models.Q(team_lead=user) | 
        models.Q(user_assignments__user=user)
    ).distinct()
