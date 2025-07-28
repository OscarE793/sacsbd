from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_index, name='index'),
    path('analytics/', views.dashboard_analytics, name='analytics'),
    path('profile/', views.user_profile, name='profile'),
    path('settings/', views.settings_view, name='settings'),
    path('api/metrics/', views.dashboard_api_metrics, name='api_metrics'),
]
