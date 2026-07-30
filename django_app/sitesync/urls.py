"""
URL routing for the sitesync app.
"""

from django.urls import path
from . import views

app_name = 'sitesync'

urlpatterns = [
    path('', views.site_list_view, name='site_list'),
    path('sync/', views.manual_sync_view, name='manual_sync'),
    path('supplies/', views.supply_list_view, name='supply_list'),
    path('settings/', views.settings_panel_view, name='settings_panel'),
    path('report/', views.report_view, name='report'),
    path('reports/', views.saved_reports_view, name='saved_reports'),
    path('reports/request-assignment/', views.request_team_assignment_view, name='request_team_assignment'),
    path('profile/', views.profile_view, name='profile'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('users/', views.user_admin_view, name='user_admin'),
    path('invitations/<uuid:invitation_id>/accept/', views.accept_invitation_view, name='accept_invitation'),
    path('consumption-display/', views.consumption_display_view, name='consumption_display'),
    path('api/consumption-import/', views.consumption_import_view, name='consumption_import'),
    path('api/consumption-display/', views.consumption_display_api_view, name='consumption_display_api'),
    path('api/report-data/', views.report_data_api_view, name='report_data_api'),
    path('api/import-runs/<uuid:import_run_id>/', views.import_run_detail_view, name='import_run_detail'),
    # Team Management Routes (Phase 4)
    path('teams/<uuid:team_id>/', views.team_detail_view, name='team_detail'),
    path('teams/assignments/', views.user_team_assignment_view, name='user_team_assignment'),
    path('roles/assignments/', views.role_assignment_view, name='role_assignment'),
    # Admin Panel Routes (Phase 5)
    path('panel/', views.admin_panel_view, name='admin_panel'),
    path('panel/users/', views.admin_users_view, name='admin_users'),
    path('panel/teams/', views.admin_teams_view, name='admin_teams'),
    path('panel/hierarchy/', views.admin_hierarchy_view, name='admin_hierarchy'),
    path('panel/roles/', views.admin_roles_view, name='admin_roles'),
    path('panel/audit-logs/', views.admin_audit_logs_view, name='admin_audit_logs'),
    path('panel/audit-logs/export.csv', views.admin_audit_logs_export_csv_view, name='admin_audit_logs_export_csv'),
    path('panel/audit-logs/export.xlsx', views.admin_audit_logs_export_xlsx_view, name='admin_audit_logs_export_xlsx'),
]
