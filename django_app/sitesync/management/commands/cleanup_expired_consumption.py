from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from sitesync.models import HalfHourlyConsumption, MonthlyConsumption, InvoiceCost


class Command(BaseCommand):
    help = "Delete imported consumption/invoice records older than retention window"

    def handle(self, *args, **options):
        retention_months = int(getattr(settings, 'CONSUMPTION_RETENTION_MONTHS', 36))
        cutoff = timezone.now() - timedelta(days=retention_months * 30)

        hh_deleted, _ = HalfHourlyConsumption.objects.filter(created_at__lt=cutoff).delete()
        monthly_deleted, _ = MonthlyConsumption.objects.filter(created_at__lt=cutoff).delete()
        invoice_deleted, _ = InvoiceCost.objects.filter(created_at__lt=cutoff).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Retention cleanup complete. cutoff={cutoff.isoformat()} "
                f"halfhourly={hh_deleted} monthly={monthly_deleted} invoice={invoice_deleted}"
            )
        )
