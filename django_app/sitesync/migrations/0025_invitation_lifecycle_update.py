from django.db import migrations, models
from django.utils import timezone


def convert_expired_to_revoked(apps, schema_editor):
    Invitation = apps.get_model('sitesync', 'Invitation')
    Invitation.objects.filter(status='expired').update(status='revoked', revoked_at=timezone.now())


def noop_reverse(apps, schema_editor):
    # Keep downgrade non-destructive; revoked rows remain revoked.
    return


class Migration(migrations.Migration):

    dependencies = [
        ('sitesync', '0024_rename_sitesync_mo_valida_9f0c0e_idx_sitesync_mo_validat_14a887_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invitation',
            name='expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='invitation',
            name='revoked_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='invitation',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('accepted', 'Accepted'),
                    ('revoked', 'Revoked'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
        migrations.RunPython(convert_expired_to_revoked, noop_reverse),
    ]
