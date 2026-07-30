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
    """Represents a time-limited invitation to join the platform."""

    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_EXPIRED = 'expired'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_EXPIRED, 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def is_valid(self):
        return self.status == self.STATUS_PENDING and self.expires_at > timezone.now()

    def accept(self):
        if not self.is_valid():
            return False
        self.status = self.STATUS_ACCEPTED
        self.accepted_at = timezone.now()
        self.save(update_fields=['status', 'accepted_at', 'updated_at'])
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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='monthly_reports')
    reporting_month = models.CharField(max_length=7, db_index=True)
    current_status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)
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
