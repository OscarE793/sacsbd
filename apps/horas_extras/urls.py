# apps/horas_extras/urls.py
from django.urls import path, include
from . import views, views_parametros, views_asignacion

app_name = 'horas_extras'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard_horas_extras, name='dashboard'),
    
    # === CALENDARIO DE ASIGNACIÓN ===
    path('asignacion/calendario/', views_asignacion.calendario_asignacion, name='calendario_asignacion'),
    path('api/eventos/', views_asignacion.obtener_eventos_calendario, name='api_eventos_calendario'),
    path('api/asignar/', views_asignacion.asignar_turno_api, name='api_asignar_turno'),

    # === EMPLEADOS ===
    path('empleados/', views.lista_operadores, name='lista_operadores'),
    path('empleados/<int:operador_id>/', views.detalle_operador, name='detalle_operador'),
    
    # === TURNOS ===
    path('turnos/registrar/', views.registrar_turno, name='registrar_turno'),
    path('turnos/<int:turno_id>/editar/', views.editar_turno, name='editar_turno'),

    
    # === CALENDARIO ===
    path('calendario/', views.calendario_turnos, name='calendario'),
    
    # === REPORTES ===
    path('reportes/', views.reportes_horas_extras, name='reportes'),
    path('reportes/preliminar/', views.reporte_preliminar, name='reporte_preliminar'),
    path('reportes/exportar/', views.exportar_reporte_excel, name='exportar_excel'),
    
    # === PARÁMETROS NORMATIVOS ===
    path('parametros/', views_parametros.listar_parametros_normativos, name='listar_parametros_normativos'),
    path('parametros/nuevo/', views_parametros.crear_parametro_normativo, name='crear_parametro_normativo'),
    path('parametros/<int:parametro_id>/', views_parametros.ver_parametro_normativo, name='ver_parametro_normativo'),
    path('parametros/<int:parametro_id>/editar/', views_parametros.editar_parametro_normativo, name='editar_parametro_normativo'),
    path('parametros/<int:parametro_id>/eliminar/', views_parametros.eliminar_parametro_normativo, name='eliminar_parametro_normativo'),
    
    # === AJAX / API ===
    path('ajax/horarios-turno/', views.ajax_horarios_turno, name='ajax_horarios_turno'),
    path('ajax/calendario-data/', views.ajax_calendario_data, name='ajax_calendario_data'),
    path('ajax/asignar-turnos/', views.ajax_asignar_turnos, name='ajax_asignar_turnos'),
]
