from django.urls import path
from . import views

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
    
    # ==========================================================================
    # EXPORTACIÓN A PDF
    # ==========================================================================
    path('cumplimiento/pdf/', views.export_cumplimiento_pdf, name='export_cumplimiento_pdf'),
    path('jobs-backup/pdf/', views.export_jobs_pdf, name='export_jobs_pdf'),
    path('estados-db/pdf/', views.export_estados_pdf, name='export_estados_pdf'),
    path('disk-growth/pdf/', views.export_disk_growth_pdf, name='export_disk_growth_pdf'),
    
    # ==========================================================================
    # EXPORTACIÓN A EXCEL (con formato profesional)
    # ==========================================================================
    path('cumplimiento/excel/', views.export_cumplimiento_excel, name='export_cumplimiento_excel'),
    path('jobs-backup/excel/', views.export_jobs_excel, name='export_jobs_excel'),
    path('estados-db/excel/', views.export_estados_excel, name='export_estados_excel'),
    path('disk-growth/excel/', views.export_disk_growth_excel, name='export_disk_growth_excel'),
    
    # ==========================================================================
    # EXPORTACIÓN A CSV
    # ==========================================================================
    path('cumplimiento/csv/', views.export_cumplimiento_csv, name='export_cumplimiento_csv'),
    path('jobs-backup/csv/', views.export_jobs_csv, name='export_jobs_csv'),
    path('estados-db/csv/', views.export_estados_csv, name='export_estados_csv'),
    path('disk-growth/csv/', views.export_disk_growth_csv, name='export_disk_growth_csv'),
]
