"""
URL routing for the sitesync app.
"""

from django.urls import path
from . import views

app_name = 'sitesync'

urlpatterns = [
    path('', views.site_list_view, name='site_list'),
    path('supplies/', views.supply_list_view, name='supply_list'),
]
