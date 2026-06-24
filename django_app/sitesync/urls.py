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
]
