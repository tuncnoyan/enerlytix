"""
Data models for the Etainabl site and supply synchronization.
"""

from django.db import models
import uuid


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
        help_text="Available capacity in kW"
    )
    parent_account_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        help_text="Parent fiscal meter account ID from Etainabl parentAccountId"
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "App Settings"

    def __str__(self):
        return "Application Settings"


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
