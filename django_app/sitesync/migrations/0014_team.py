# Generated migration for Team, UserTeamAssignment, and RoleAssignment models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('sitesync', '0013_invitation'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, help_text='Display name for the team', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('manager', models.ForeignKey(blank=True, help_text='User assigned as team manager', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='managed_teams', to=settings.AUTH_USER_MODEL)),
                ('parent_team', models.ForeignKey(blank=True, help_text='Parent team for hierarchical structure (null for root teams)', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='sub_teams', to='sitesync.team')),
                ('team_lead', models.ForeignKey(blank=True, help_text='User assigned as team lead', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='led_teams', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='UserTeamAssignment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('assigned_by', models.ForeignKey(blank=True, help_text='Administrator who performed the assignment', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='team_assignments_made', to=settings.AUTH_USER_MODEL)),
                ('team', models.ForeignKey(help_text='Team the user is assigned to', on_delete=django.db.models.deletion.CASCADE, related_name='user_assignments', to='sitesync.team')),
                ('user', models.ForeignKey(help_text='User assigned to the team', on_delete=django.db.models.deletion.CASCADE, related_name='team_assignments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['team__name', 'user__username'],
                'unique_together': {('user', 'team')},
            },
        ),
        migrations.CreateModel(
            name='RoleAssignment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('role_name', models.CharField(choices=[('admin', 'Administrator'), ('manager', 'Manager'), ('team_lead', 'Team Lead'), ('user', 'User')], help_text='The role being assigned', max_length=20)),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('assigned_by', models.ForeignKey(blank=True, help_text='Administrator who assigned the role', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='role_assignments_made', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(help_text='User being assigned a role', on_delete=django.db.models.deletion.CASCADE, related_name='role_assignments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user__username', 'role_name'],
                'unique_together': {('user', 'role_name')},
            },
        ),
        migrations.AddIndex(
            model_name='team',
            index=models.Index(fields=['name'], name='sitesync_team_name_idx'),
        ),
        migrations.AddIndex(
            model_name='team',
            index=models.Index(fields=['manager'], name='sitesync_team_manager_idx'),
        ),
        migrations.AddIndex(
            model_name='team',
            index=models.Index(fields=['parent_team'], name='sitesync_team_parent_team_idx'),
        ),
        migrations.AddIndex(
            model_name='userteamassignment',
            index=models.Index(fields=['user'], name='sitesync_userteamassignment_user_idx'),
        ),
        migrations.AddIndex(
            model_name='userteamassignment',
            index=models.Index(fields=['team'], name='sitesync_userteamassignment_team_idx'),
        ),
        migrations.AddIndex(
            model_name='userteamassignment',
            index=models.Index(fields=['user', 'team'], name='sitesync_userteamassignment_user_team_idx'),
        ),
        migrations.AddIndex(
            model_name='roleassignment',
            index=models.Index(fields=['user'], name='sitesync_roleassignment_user_idx'),
        ),
        migrations.AddIndex(
            model_name='roleassignment',
            index=models.Index(fields=['role_name'], name='sitesync_roleassignment_role_name_idx'),
        ),
        migrations.AddIndex(
            model_name='roleassignment',
            index=models.Index(fields=['user', 'role_name'], name='sitesync_roleassignment_user_role_name_idx'),
        ),
    ]
