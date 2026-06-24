"""
Data models for the Etainabl site and supply synchronization.
"""

from django.db import models


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['external_id']),
            models.Index(fields=['site', 'name']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_utility_type_display()})"


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
