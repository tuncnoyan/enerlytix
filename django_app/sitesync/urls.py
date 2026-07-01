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
    path('consumption-display/', views.consumption_display_view, name='consumption_display'),
    path('api/consumption-import/', views.consumption_import_view, name='consumption_import'),
    path('api/consumption-display/', views.consumption_display_api_view, name='consumption_display_api'),
    path('api/import-runs/<uuid:import_run_id>/', views.import_run_detail_view, name='import_run_detail'),
]
