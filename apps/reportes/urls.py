from django.urls import path
from . import views
# from .views_test import test_basic_connectivity  # Comentado temporalmente

app_name = 'reportes'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard_view, name='dashboard'),
    
    # Reportes principales
    path('cumplimiento/', views.cumplimiento_backup_view, name='cumplimiento_backup'),
    path('jobs-backup/', views.jobs_backup_view, name='jobs_backup'),
    path('archivos-backup/', views.archivos_backup_view, name='archivos_backup'),
    path('estados-db/', views.estados_db_view, name='estados_db'),
    path('ultimos-backup/', views.ultimos_backup_view, name='ultimos_backup'),
    path('listar-bd/', views.listar_bd_view, name='listar_bd'),
    path('disk-growth/', views.disk_growth_view, name='disk_growth'),
    
    # APIs
    path('api/dashboard-metrics/', views.api_dashboard_metrics, name='api_dashboard_metrics'),
    
    # Funciones adicionales de cumplimiento
    path('buscar-reporte/', views.buscar_reporte_cumplimiento, name='buscar_reporte'),
    path('reporte-cumplimiento/', views.reporte_cumplimiento_excel, name='reporte_cumplimiento'),
    
    # Vista de prueba (para debugging) - comentada temporalmente
    # path('test/', test_basic_connectivity, name='test_connectivity'),
]
