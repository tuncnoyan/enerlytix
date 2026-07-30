from django.db import migrations, models


def forwards_set_team_levels(apps, schema_editor):
    Team = apps.get_model('sitesync', 'Team')

    levels = {}
    teams = list(Team.objects.all().values('id', 'parent_team_id'))

    # Root teams are level 1.
    for team in teams:
        if team['parent_team_id'] is None:
            levels[team['id']] = 1

    unresolved = {team['id']: team['parent_team_id'] for team in teams if team['id'] not in levels}

    # Resolve children when parent level is known.
    progressed = True
    while unresolved and progressed:
        progressed = False
        for team_id, parent_id in list(unresolved.items()):
            parent_level = levels.get(parent_id)
            if parent_level is None:
                continue
            levels[team_id] = parent_level + 1
            unresolved.pop(team_id)
            progressed = True

    # Fallback for any unresolved/cyclic rows.
    for team_id in unresolved:
        levels[team_id] = 1

    for team in Team.objects.all():
        level = levels.get(team.id, 1)
        if team.level != level:
            team.level = level
            team.save(update_fields=['level'])


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ('sitesync', '0015_rename_sitesync_roleassignment_user_idx_sitesync_ro_user_id_27665e_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='level',
            field=models.PositiveIntegerField(
                db_index=True,
                default=1,
                help_text='Hierarchy level (root teams are level 1, sub-teams increment by 1)',
            ),
        ),
        migrations.RunPython(forwards_set_team_levels, noop_reverse),
    ]
