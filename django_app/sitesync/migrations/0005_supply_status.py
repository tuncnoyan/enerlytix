from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitesync', '0004_supply_available_capacity_benchmark'),
    ]

    operations = [
        migrations.AddField(
            model_name='supply',
            name='status',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Supply status from Etainabl (for example: active/inactive)',
                max_length=50,
                null=True,
            ),
        ),
    ]
