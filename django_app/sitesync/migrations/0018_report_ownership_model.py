from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models
import uuid


def backfill_report_ownership(apps, schema_editor):
    MonthlyReport = apps.get_model('sitesync', 'MonthlyReport')
    user_app_label, user_model_name = settings.AUTH_USER_MODEL.split('.')
    UserModel = apps.get_model(user_app_label, user_model_name)

    fallback_user = UserModel.objects.filter(is_active=True).order_by('id').first()

    for report in MonthlyReport.objects.all().iterator():
        owner = report.owner_user or report.created_by_user or fallback_user
        created_by = report.created_by_user or owner
        last_modified_by = report.last_modified_by_user or owner
        last_modified_at = report.last_modified_at or report.updated_at or report.created_at

        changed = False
        if report.owner_user_id != getattr(owner, 'id', None):
            report.owner_user = owner
            changed = True
        if report.created_by_user_id != getattr(created_by, 'id', None):
            report.created_by_user = created_by
            changed = True
        if report.last_modified_by_user_id != getattr(last_modified_by, 'id', None):
            report.last_modified_by_user = last_modified_by
            changed = True
        if report.last_modified_at != last_modified_at:
            report.last_modified_at = last_modified_at
            changed = True

        if changed:
            report.save(update_fields=['owner_user', 'created_by_user', 'last_modified_by_user', 'last_modified_at'])


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ('sitesync', '0017_auditlogentry'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='monthlyreport',
            name='created_by_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_monthly_reports', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='monthlyreport',
            name='last_modified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='monthlyreport',
            name='last_modified_by_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='last_modified_monthly_reports', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='monthlyreport',
            name='owner_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owned_monthly_reports', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='ReportOwnershipUnavailabilityApproval',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('approval_reason', models.TextField()),
                ('approved_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('approved', 'Approved'), ('cancelled', 'Cancelled')], default='approved', max_length=16)),
                ('approved_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ownership_unavailability_approvals', to=settings.AUTH_USER_MODEL)),
                ('owner_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ownership_unavailability_records', to=settings.AUTH_USER_MODEL)),
                ('report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unavailability_approvals', to='sitesync.monthlyreport')),
            ],
            options={
                'ordering': ['-approved_at'],
            },
        ),
        migrations.CreateModel(
            name='ReportOwnershipTransferEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('transfer_mode', models.CharField(choices=[('auto_fallback', 'Auto Fallback'), ('manual_owner_transfer', 'Manual Owner Transfer')], max_length=32)),
                ('transfer_reason', models.TextField(blank=True)),
                ('transferred_at', models.DateTimeField(auto_now_add=True)),
                ('approval_record', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transfer_events', to='sitesync.reportownershipunavailabilityapproval')),
                ('executed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ownership_transfers_executed', to=settings.AUTH_USER_MODEL)),
                ('from_owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ownership_transfers_from', to=settings.AUTH_USER_MODEL)),
                ('report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ownership_transfers', to='sitesync.monthlyreport')),
                ('to_owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ownership_transfers_to', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-transferred_at'],
            },
        ),
        migrations.CreateModel(
            name='ReportWriteGrant',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('granted_at', models.DateTimeField(auto_now_add=True)),
                ('revoked_at', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('granted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='report_write_grants_issued', to=settings.AUTH_USER_MODEL)),
                ('granted_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_write_grants', to=settings.AUTH_USER_MODEL)),
                ('report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='write_grants', to='sitesync.monthlyreport')),
                ('revoked_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='report_write_grants_revoked', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-granted_at'],
            },
        ),
        migrations.AddIndex(
            model_name='monthlyreport',
            index=models.Index(fields=['owner_user'], name='sitesync_mo_owner_u_757495_idx'),
        ),
        migrations.AddIndex(
            model_name='monthlyreport',
            index=models.Index(fields=['site', 'owner_user', 'current_status'], name='sitesync_mo_site_id_0d2c7c_idx'),
        ),
        migrations.AddIndex(
            model_name='reportownershipunavailabilityapproval',
            index=models.Index(fields=['report', 'status'], name='sitesync_re_report__48eb45_idx'),
        ),
        migrations.AddIndex(
            model_name='reportownershipunavailabilityapproval',
            index=models.Index(fields=['approved_at'], name='sitesync_re_approve_2da773_idx'),
        ),
        migrations.AddIndex(
            model_name='reportownershiptransferevent',
            index=models.Index(fields=['report', 'transferred_at'], name='sitesync_re_report__2f8f8d_idx'),
        ),
        migrations.AddIndex(
            model_name='reportownershiptransferevent',
            index=models.Index(fields=['to_owner', 'transferred_at'], name='sitesync_re_to_owne_4240c8_idx'),
        ),
        migrations.AddIndex(
            model_name='reportwritegrant',
            index=models.Index(fields=['report', 'is_active'], name='sitesync_re_report__12d4e5_idx'),
        ),
        migrations.AddIndex(
            model_name='reportwritegrant',
            index=models.Index(fields=['granted_user'], name='sitesync_re_granted_85058b_idx'),
        ),
        migrations.AddConstraint(
            model_name='reportwritegrant',
            constraint=models.UniqueConstraint(condition=django.db.models.Q(('is_active', True)), fields=('report', 'granted_user'), name='uniq_active_report_write_grant'),
        ),
        migrations.RunPython(backfill_report_ownership, noop_reverse),
    ]
