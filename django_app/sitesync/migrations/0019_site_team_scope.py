from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sitesync', '0018_report_ownership_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='team',
            field=models.ForeignKey(blank=True, help_text='Owning team used for report access scope and ownership fallback checks', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sites', to='sitesync.team'),
        ),
    ]
