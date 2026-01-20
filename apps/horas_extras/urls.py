# apps/horas_extras/urls.py
from django.urls import path, include
from . import views

app_name = 'horas_extras'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard_horas_extras, name='dashboard'),
    
    # === EMPLEADOS ===
    path('empleados/', views.lista_empleados, name='lista_empleados'),
    path('empleados/<int:empleado_id>/', views.detalle_empleado, name='detalle_empleado'),
    
    # === TURNOS ===
    path('turnos/registrar/', views.registrar_turno, name='registrar_turno'),
    path('turnos/<int:turno_id>/editar/', views.editar_turno, name='editar_turno'),
    path('turnos/generar/', views.generar_turnos_automaticos, name='generar_turnos'),
    
    # === CALENDARIO ===
    path('calendario/', views.calendario_turnos, name='calendario'),
    
    # === REPORTES ===
    path('reportes/', views.reportes_horas_extras, name='reportes'),
    path('reportes/exportar/', views.exportar_reporte_excel, name='exportar_excel'),
    
    # === AJAX / API ===
    path('ajax/horarios-turno/', views.ajax_horarios_turno, name='ajax_horarios_turno'),
    path('ajax/calendario-data/', views.ajax_calendario_data, name='ajax_calendario_data'),
    path('ajax/calcular-recargos/', views.calcular_recargos_lote, name='calcular_recargos_lote'),
]
