from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitesync', '0025_invitation_lifecycle_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='monthlyreportversion',
            name='selected_supply_ids',
            field=models.JSONField(default=list),
        ),
    ]
