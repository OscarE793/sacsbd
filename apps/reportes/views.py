# apps/reportes/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.utils import timezone
from django.urls import reverse
from django.contrib import messages
from datetime import datetime, timedelta
import json
import logging

from .utils import (
    ejecutar_procedimiento_almacenado,
    ejecutar_consulta_personalizada,
    obtener_servidores_disponibles,
    obtener_bases_datos,
    formatear_resultado_backup,
    calcular_estadisticas_cumplimiento
)
from .config import STORED_PROCEDURES, QUERIES, DEFAULT_FILTERS, PAGINATION, THRESHOLDS

logger = logging.getLogger(__name__)


@login_required
def buscar_reporte_cumplimiento(request):
    """Buscar resultados de cumplimiento con fechas específicas"""
    try:
        fecha_inicio_param = request.GET.get('fecha')
        fecha_fin_param = request.GET.get('fecha1')
        
        if not fecha_inicio_param or not fecha_fin_param:
            # Redirigir de vuelta con mensaje de error
            messages.error(request, 'Debe proporcionar ambas fechas para realizar la búsqueda.')
            return redirect('reportes:cumplimiento_backup')
        
        # Redirigir a la vista principal con los parámetros
        return redirect(f"{reverse('reportes:cumplimiento_backup')}?fecha={fecha_inicio_param}&fecha1={fecha_fin_param}")
        
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        messages.error(request, f'Error en la búsqueda: {str(e)}')
        return redirect('reportes:cumplimiento_backup')


@login_required  
def reporte_cumplimiento_excel(request):
    """Generar reporte de cumplimiento en Excel para descarga"""
    try:
        from django.http import HttpResponse
        import csv
        from io import StringIO
        
        fecha_inicio_param = request.GET.get('fecha')
        fecha_fin_param = request.GET.get('fecha1')
        
        # Configurar fechas
        if fecha_inicio_param:
            fecha_inicio = datetime.strptime(fecha_inicio_param, '%Y-%m-%d').strftime('%Y/%m/%d')
        else:
            fecha_inicio = datetime.now().replace(day=1).strftime('%Y/%m/%d')
            
        if fecha_fin_param:
            fecha_fin = datetime.strptime(fecha_fin_param, '%Y-%m-%d').strftime('%Y/%m/%d')
        else:
            fecha_fin = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
        
        # Obtener datos usando el mismo procedimiento
        try:
            resultados = ejecutar_procedimiento_almacenado(
                'sp_Programaciondebcks',
                [fecha_inicio, fecha_fin]
            )
            
            # Convertir a formato consistente si es necesario
            if resultados and not isinstance(resultados[0], dict):
                datos_formateados = []
                for fila in resultados:
                    if isinstance(fila, (list, tuple)) and len(fila) >= 6:
                        datos_formateados.append({
                            'SERVIDOR': fila[0],
                            'DatabaseName': fila[1],
                            'IPSERVER': fila[2], 
                            'TOTAL': fila[3],
                            'TOTALPROGRAM': fila[4],
                            'PORCENTAJE': fila[5]
                        })
                resultados = datos_formateados
                
        except Exception as sp_error:
            logger.error(f"Error en SP para Excel: {sp_error}")
            # Usar consulta alternativa
            query = """
                SELECT 
                    bg.SERVIDOR,
                    bg.DatabaseName,
                    bg.IPSERVER,
                    COUNT(*) as TOTAL,
                    30 as TOTALPROGRAM,
                    CAST((COUNT(*) * 100.0 / 30) AS DECIMAL(5,2)) as PORCENTAJE
                FROM BACKUPSGENERADOS bg
                WHERE CONVERT(date, SUBSTRING(bg.FECHA,7,4) + '-' + SUBSTRING(bg.FECHA,4,2) + '-' + SUBSTRING(bg.FECHA,1,2)) 
                      BETWEEN CONVERT(date, %s) AND CONVERT(date, %s)
                GROUP BY bg.SERVIDOR, bg.DatabaseName, bg.IPSERVER
                ORDER BY bg.SERVIDOR, bg.DatabaseName
            """
            fecha_inicio_sql = datetime.strptime(fecha_inicio, '%Y/%m/%d').strftime('%Y-%m-%d')
            fecha_fin_sql = datetime.strptime(fecha_fin, '%Y/%m/%d').strftime('%Y-%m-%d')
            resultados = ejecutar_consulta_personalizada(query, [fecha_inicio_sql, fecha_fin_sql])
        
        # Crear respuesta CSV
        response = HttpResponse(content_type='text/csv')
        filename = f"cumplimiento_backup_{fecha_inicio.replace('/', '-')}_a_{fecha_fin.replace('/', '-')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Escribir CSV
        writer = csv.writer(response)
        writer.writerow([
            'Servidor',
            'Nombre BD', 
            'IP Servidor',
            'Copias Ejecutadas',
            'Copias Programadas',
            'Porcentaje Cumplimiento'
        ])
        
        for resultado in resultados:
            writer.writerow([
                resultado.get('SERVIDOR', ''),
                resultado.get('DatabaseName', ''),
                resultado.get('IPSERVER', ''),
                resultado.get('TOTAL', ''),
                resultado.get('TOTALPROGRAM', ''),
                resultado.get('PORCENTAJE', '')
            ])
        
        logger.info(f"Descarga de reporte: {filename}")
        return response
        
    except Exception as e:
        logger.error(f"Error generando Excel: {e}")
        messages.error(request, f'Error al generar el reporte: {str(e)}')
        return redirect('reportes:cumplimiento_backup')


@login_required
def dashboard_view(request):
    """Dashboard principal con métricas de BACKUPSGENERADOS y JOBSBACKUPGENERADOS"""
    try:
        # Métricas principales - consulta simple y compatible
        metricas_query = """
            SELECT 
                (SELECT COUNT(DISTINCT SERVIDOR) FROM BACKUPSGENERADOS WHERE SERVIDOR IS NOT NULL) as total_servidores,
                (SELECT COUNT(DISTINCT DatabaseName) FROM BACKUPSGENERADOS WHERE DatabaseName IS NOT NULL) as total_bases_datos,
                (SELECT COUNT(*) FROM BACKUPSGENERADOS WHERE FECHA = CONVERT(varchar, GETDATE(), 103)) as backups_hoy,
                (SELECT COUNT(*) FROM BACKUPSGENERADOS WHERE 
                    CONVERT(date, SUBSTRING(FECHA,7,4) + '-' + SUBSTRING(FECHA,4,2) + '-' + SUBSTRING(FECHA,1,2)) 
                    >= DATEADD(day, -7, GETDATE())
                ) as backups_semana,
                (SELECT COUNT(*) FROM JOBSBACKUPGENERADOS WHERE 
                    FECHA_Y_HORA_INICIO >= DATEADD(day, -7, GETDATE()) AND 
                    (RESULTADO LIKE '%Exitoso%' OR RESULTADO LIKE '%exitoso%')
                ) as jobs_exitosos_semana,
                (SELECT COUNT(*) FROM JOBSBACKUPGENERADOS WHERE 
                    FECHA_Y_HORA_INICIO >= DATEADD(day, -7, GETDATE()) AND 
                    (RESULTADO LIKE '%Fallido%' OR RESULTADO LIKE '%fallido%' OR RESULTADO LIKE '%Error%')
                ) as jobs_fallidos_semana
        """
        metricas = ejecutar_consulta_personalizada(metricas_query)
        
        # Estadísticas de jobs recientes - últimos 30 días para tener datos
        stats_jobs_query = """
            SELECT 
                RESULTADO,
                COUNT(*) as cantidad,
                CAST(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() AS DECIMAL(5,2)) as porcentaje
            FROM JOBSBACKUPGENERADOS 
            WHERE FECHA_Y_HORA_INICIO >= DATEADD(day, -30, GETDATE())
            GROUP BY RESULTADO
            ORDER BY cantidad DESC
        """
        stats_jobs = ejecutar_consulta_personalizada(stats_jobs_query)
        
        # Últimos backups - últimos 30 días para tener datos
        ultimos_backups_query = """
            SELECT TOP 10
                SERVIDOR,
                DatabaseName,
                IPSERVER,
                TYPE,
                FECHA,
                HORA,
                DATEDIFF(hour, 
                    CONVERT(datetime, SUBSTRING(FECHA,7,4) + '-' + SUBSTRING(FECHA,4,2) + '-' + SUBSTRING(FECHA,1,2) + ' ' + HORA), 
                    GETDATE()
                ) as horas_transcurridas,
                CASE 
                    WHEN DATEDIFF(hour, 
                        CONVERT(datetime, SUBSTRING(FECHA,7,4) + '-' + SUBSTRING(FECHA,4,2) + '-' + SUBSTRING(FECHA,1,2) + ' ' + HORA), 
                        GETDATE()
                    ) <= 24 THEN 'success'
                    WHEN DATEDIFF(hour, 
                        CONVERT(datetime, SUBSTRING(FECHA,7,4) + '-' + SUBSTRING(FECHA,4,2) + '-' + SUBSTRING(FECHA,1,2) + ' ' + HORA), 
                        GETDATE()
                    ) <= 48 THEN 'warning'
                    ELSE 'danger'
                END as status_class
            FROM BACKUPSGENERADOS
            WHERE CONVERT(date, SUBSTRING(FECHA,7,4) + '-' + SUBSTRING(FECHA,4,2) + '-' + SUBSTRING(FECHA,1,2)) >= DATEADD(day, -30, GETDATE())
            ORDER BY 
                CONVERT(date, SUBSTRING(FECHA,7,4) + '-' + SUBSTRING(FECHA,4,2) + '-' + SUBSTRING(FECHA,1,2)) DESC,
                CONVERT(time, HORA) DESC
        """
        ultimos_backups = ejecutar_consulta_personalizada(ultimos_backups_query)

        context = {
            'metricas': metricas[0] if metricas else {},
            'stats_jobs': stats_jobs,
            'ultimos_backups': ultimos_backups,
            'chart_data': {
                'servidores': metricas[0].get('total_servidores', 0) if metricas else 0,
                'bases_datos': metricas[0].get('total_bases_datos', 0) if metricas else 0,
                'backups_hoy': metricas[0].get('backups_hoy', 0) if metricas else 0,
                'backups_semana': metricas[0].get('backups_semana', 0) if metricas else 0,
            },
            'last_updated': timezone.now(),
        }

        return render(request, 'reportes/dashboard.html', context)

    except Exception as e:
        logger.error(f"Error en dashboard: {e}")
        context = {
            'error': f'Error al cargar las métricas del dashboard: {str(e)}',
            'metricas': {},
            'stats_jobs': [],
            'ultimos_backups': [],
            'chart_data': {'servidores': 0, 'bases_datos': 0, 'backups_hoy': 0, 'backups_semana': 0}
        }
        return render(request, 'reportes/dashboard.html', context)


@login_required
def cumplimiento_backup_view(request):
    """Reporte de cumplimiento usando sp_Programaciondebcks con fechas personalizables"""
    try:
        # Obtener fechas de los parámetros GET
        fecha_inicio_param = request.GET.get('fecha')
        fecha_fin_param = request.GET.get('fecha1')
        
        # Configurar fechas por defecto si no se proporcionan
        if fecha_inicio_param:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_param, '%Y-%m-%d').strftime('%Y/%m/%d')
            except ValueError:
                logger.warning(f"Fecha inicio inválida: {fecha_inicio_param}")
                fecha_inicio = datetime.now().replace(day=1).strftime('%Y/%m/%d')
        else:
            # Primer día del mes actual
            fecha_inicio = datetime.now().replace(day=1).strftime('%Y/%m/%d')
        
        if fecha_fin_param:
            try:
                fecha_fin = datetime.strptime(fecha_fin_param, '%Y-%m-%d').strftime('%Y/%m/%d')
            except ValueError:
                logger.warning(f"Fecha fin inválida: {fecha_fin_param}")
                fecha_fin = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
        else:
            # Día anterior
            fecha_fin = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
        
        logger.info(f"Ejecutando cumplimiento backup: {fecha_inicio} a {fecha_fin}")
        
        # Ejecutar el procedimiento almacenado
        try:
            resultados = ejecutar_procedimiento_almacenado(
                'sp_Programaciondebcks',
                [fecha_inicio, fecha_fin]
            )
            
            # Si el SP no devuelve resultados con nombres de columna, usar índices
            if resultados and not isinstance(resultados[0], dict):
                # Convertir tuplas a formato esperado por el template
                resultados_formateados = []
                for fila in resultados:
                    if isinstance(fila, (list, tuple)) and len(fila) >= 6:
                        resultado_dict = {
                            'SERVIDOR': fila[0],
                            'DatabaseName': fila[1], 
                            'IPSERVER': fila[2],
                            'TOTAL': fila[3],
                            'TOTALPROGRAM': fila[4],
                            'PORCENTAJE': fila[5]
                        }
                        resultados_formateados.append(resultado_dict)
                resultados = resultados_formateados
            
        except Exception as sp_error:
            logger.error(f"Error ejecutando sp_Programaciondebcks1: {sp_error}")
            # Consulta alternativa si el SP falla
            query_alternativa = """
                SELECT 
                    bg.SERVIDOR,
                    bg.DatabaseName,
                    bg.IPSERVER,
                    COUNT(*) as TOTAL,
                    30 as TOTALPROGRAM,
                    CAST((COUNT(*) * 100.0 / 30) AS DECIMAL(5,2)) as PORCENTAJE
                FROM BACKUPSGENERADOS bg
                WHERE CONVERT(date, SUBSTRING(bg.FECHA,7,4) + '-' + SUBSTRING(bg.FECHA,4,2) + '-' + SUBSTRING(bg.FECHA,1,2)) 
                      BETWEEN CONVERT(date, %s) AND CONVERT(date, %s)
                GROUP BY bg.SERVIDOR, bg.DatabaseName, bg.IPSERVER
                ORDER BY PORCENTAJE ASC, bg.SERVIDOR, bg.DatabaseName
            """
            
            # Convertir fechas para la consulta alternativa
            fecha_inicio_sql = datetime.strptime(fecha_inicio, '%Y/%m/%d').strftime('%Y-%m-%d')
            fecha_fin_sql = datetime.strptime(fecha_fin, '%Y/%m/%d').strftime('%Y-%m-%d')
            
            resultados = ejecutar_consulta_personalizada(
                query_alternativa, 
                [fecha_inicio_sql, fecha_fin_sql]
            )
        
        # Estadísticas para el dashboard
        total_registros = len(resultados)
        total_ejecutadas = sum(int(r.get('TOTAL', 0)) for r in resultados)
        total_programadas = sum(int(r.get('TOTALPROGRAM', 0)) for r in resultados)
        
        estadisticas = {
            'total_registros': total_registros,
            'total_ejecutadas': total_ejecutadas,
            'total_programadas': total_programadas,
            'promedio_cumplimiento': round((total_ejecutadas / total_programadas) * 100, 2) if total_programadas > 0 else 0,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin
        }
        
        # Convertir fechas para mostrar en el template
        fecha_inicio_display = datetime.strptime(fecha_inicio, '%Y/%m/%d').strftime('%Y-%m-%d')
        fecha_fin_display = datetime.strptime(fecha_fin, '%Y/%m/%d').strftime('%Y-%m-%d')
        
        context = {
            'resultadosCump': resultados,
            'estadisticas': estadisticas,
            'fecha_inicio': fecha_inicio_display,
            'fecha_fin': fecha_fin_display,
            'total_registros': total_registros
        }
        
        return render(request, 'reportes/cumplimiento_bck.html', context)
        
    except Exception as e:
        logger.error(f"Error en cumplimiento backup: {e}")
        context = {
            'error': f'Error al cargar el reporte de cumplimiento: {str(e)}',
            'resultadosCump': [],
            'estadisticas': {
                'total_registros': 0,
                'total_ejecutadas': 0, 
                'total_programadas': 0,
                'promedio_cumplimiento': 0
            }
        }
        return render(request, 'reportes/cumplimiento_bck.html', context)


@login_required
def jobs_backup_view(request):
    """Reporte de jobs usando sp_resultadoJobsBck - coincide exactamente con los campos del SP"""
    try:
        # Filtros
        fecha_inicio = request.GET.get('fecha_inicio', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        fecha_fin = request.GET.get('fecha_fin', timezone.now().strftime('%Y-%m-%d'))
        servidor = request.GET.get('servidor', '')
        resultado_filtro = request.GET.get('resultado', '')

        logger.info(f"Ejecutando jobs backup: {fecha_inicio} a {fecha_fin}")

        # Usar procedimiento almacenado sp_resultadoJobsBck
        try:
            resultados = ejecutar_procedimiento_almacenado(
                'sp_resultadoJobsBck',
                [fecha_inicio, fecha_fin]
            )
            
            # Si el SP devuelve tuplas, convertir a diccionarios con los campos exactos
            if resultados and not isinstance(resultados[0], dict):
                resultados_formateados = []
                for fila in resultados:
                    if isinstance(fila, (list, tuple)) and len(fila) >= 8:
                        resultado_dict = {
                            'RESULTADO': fila[0] if fila[0] else '',
                            'SERVIDOR': fila[1] if fila[1] else '',
                            'IPSERVER': fila[2] if fila[2] else '',
                            'FECHA': fila[3] if fila[3] else '',
                            'HORA': fila[4] if fila[4] else '',
                            'NOMBRE_DEL_JOB': fila[5] if fila[5] else '',
                            'PASO': fila[6] if fila[6] else '',
                            'MENSAJE': fila[7] if fila[7] else ''
                        }
                        resultados_formateados.append(resultado_dict)
                resultados = resultados_formateados
                
        except Exception as proc_error:
            logger.warning(f"Error con sp_resultadoJobsBck: {proc_error}")
            # Consulta directa como alternativa - usando los mismos campos que el SP
            resultados_query = """
                SELECT 
                    RESULTADO,
                    SERVIDOR,
                    IPSERVER,
                    CONVERT(varchar, FECHA_Y_HORA_INICIO, 103) as FECHA,
                    CONVERT(varchar, FECHA_Y_HORA_INICIO, 108) as HORA,
                    NOMBRE_DEL_JOB,
                    CAST(PASO as varchar) as PASO,
                    MENSAJE
                FROM JOBSBACKUPGENERADOS
                WHERE CONVERT(date, FECHA_Y_HORA_INICIO) BETWEEN %s AND %s
                ORDER BY FECHA_Y_HORA_INICIO DESC
            """
            resultados = ejecutar_consulta_personalizada(resultados_query, [fecha_inicio, fecha_fin])

        # Aplicar filtros adicionales en Python si es necesario
        if servidor:
            resultados = [r for r in resultados if servidor.lower() in r.get('SERVIDOR', '').lower()]
        if resultado_filtro:
            resultados = [r for r in resultados if resultado_filtro.lower() in r.get('RESULTADO', '').lower()]

        # Estadísticas
        total = len(resultados)
        exitosos = len([r for r in resultados if 'exitoso' in r.get('RESULTADO', '').lower()])
        fallidos = len([r for r in resultados if 'fallido' in r.get('RESULTADO', '').lower() or 'error' in r.get('RESULTADO', '').lower()])
        otros = total - exitosos - fallidos
        
        stats = {
            'total': total,
            'exitosos': exitosos,
            'fallidos': fallidos,
            'otros': otros,
            'porcentaje_exito': round((exitosos / total) * 100, 2) if total > 0 else 0
        }

        # Paginación
        paginator = Paginator(resultados, PAGINATION['items_per_page'])
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Obtener lista de servidores para el filtro
        try:
            servidores = ejecutar_consulta_personalizada("""
                SELECT DISTINCT SERVIDOR as servidor, IPSERVER as ip_servidor, COUNT(*) as total_jobs
                FROM JOBSBACKUPGENERADOS 
                WHERE SERVIDOR IS NOT NULL AND SERVIDOR != ''
                GROUP BY SERVIDOR, IPSERVER 
                ORDER BY SERVIDOR
            """)
        except Exception:
            servidores = []

        # Obtener tipos de resultado para referencia
        try:
            tipos_resultado = ejecutar_consulta_personalizada("""
                SELECT DISTINCT RESULTADO, COUNT(*) as cantidad
                FROM JOBSBACKUPGENERADOS 
                WHERE RESULTADO IS NOT NULL AND RESULTADO != ''
                GROUP BY RESULTADO 
                ORDER BY cantidad DESC
            """)
        except Exception:
            tipos_resultado = []

        context = {
            'resultados': page_obj,
            'stats': stats,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'servidor': servidor,
            'resultado': resultado_filtro,
            'servidores': servidores,
            'tipos_resultado': tipos_resultado,
        }

        return render(request, 'reportes/jobs_bck.html', context)

    except Exception as e:
        logger.error(f"Error en jobs backup: {e}")
        context = {
            'error': f'Error al cargar los jobs de backup: {str(e)}',
            'resultados': [],
            'stats': {'total': 0, 'exitosos': 0, 'fallidos': 0, 'otros': 0, 'porcentaje_exito': 0},
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'servidor': '',
            'resultado': '',
            'servidores': [],
            'tipos_resultado': []
        }
        return render(request, 'reportes/jobs_bck.html', context)


@login_required
def archivos_backup_view(request):
    """Reporte de archivos usando BACKUPSGENERADOS"""
    try:
        # Filtros
        dias_atras = int(request.GET.get('dias_atras', 30))
        servidor = request.GET.get('servidor', '')
        tipo_backup = request.GET.get('tipo_backup', '')

        query = """
            SELECT 
                BCK_ID,
                SERVIDOR,
                DatabaseName as database_name,
                IPSERVER,
                TYPE as tipo_backup,
                FECHA,
                HORA,
                physical_device_name as ruta_archivo,
                CASE TYPE
                    WHEN 'FULL' THEN 'Completo'
                    WHEN 'INCREMENTAL' THEN 'Incremental'
                    WHEN 'DIFF' THEN 'Diferencial'
                    WHEN 'LOG' THEN 'Log'
                    ELSE ISNULL(TYPE, 'Sin tipo')
                END as tipo_descripcion,
                LEN(physical_device_name) as longitud_ruta
            FROM BACKUPSGENERADOS
            WHERE CONVERT(date, SUBSTRING(FECHA,7,4) + '-' + SUBSTRING(FECHA,4,2) + '-' + SUBSTRING(FECHA,1,2)) >= DATEADD(day, -%s, GETDATE())
                AND physical_device_name IS NOT NULL
        """
        
        params = [dias_atras]
        
        if servidor:
            query += " AND SERVIDOR = %s"
            params.append(servidor)
        if tipo_backup:
            query += " AND TYPE = %s"
            params.append(tipo_backup)
            
        query += """
            ORDER BY 
                CONVERT(date, SUBSTRING(FECHA,7,4) + '-' + SUBSTRING(FECHA,4,2) + '-' + SUBSTRING(FECHA,1,2)) DESC,
                CONVERT(time, HORA) DESC
        """
        
        resultados = ejecutar_consulta_personalizada(query, params)

        # Paginación
        paginator = Paginator(resultados, PAGINATION['items_per_page'])
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'resultados': page_obj,
            'dias_atras': dias_atras,
            'servidor': servidor,
            'tipo_backup': tipo_backup,
            'servidores': ejecutar_consulta_personalizada("""
                SELECT DISTINCT SERVIDOR as servidor, IPSERVER as ip_servidor, COUNT(*) as total_backups
                FROM BACKUPSGENERADOS 
                WHERE SERVIDOR IS NOT NULL 
                GROUP BY SERVIDOR, IPSERVER 
                ORDER BY SERVIDOR
            """),
            'tipos_backup': ejecutar_consulta_personalizada("""
                SELECT DISTINCT TYPE as tipo_backup, COUNT(*) as cantidad
                FROM BACKUPSGENERADOS 
                WHERE TYPE IS NOT NULL
                GROUP BY TYPE 
                ORDER BY cantidad DESC
            """),
        }

        return render(request, 'reportes/archivos_bak.html', context)

    except Exception as e:
        logger.error(f"Error en archivos backup: {e}")
        context = {
            'error': f'Error al cargar los archivos de backup: {str(e)}',
            'resultados': []
        }
        return render(request, 'reportes/archivos_bak.html', context)


@login_required
def estados_db_view(request):
    """Reporte de estados usando sp_estadosdb - coincide exactamente con los campos del SP"""
    try:
        # Filtros
        servidor = request.GET.get('servidor', '')
        estado = request.GET.get('estado', '')

        logger.info("Ejecutando estados de bases de datos")

        # Usar procedimiento almacenado sp_estadosdb
        try:
            resultados = ejecutar_procedimiento_almacenado('sp_estadosdb')
            
            # Si el SP devuelve tuplas, convertir a diccionarios con los campos exactos
            if resultados and not isinstance(resultados[0], dict):
                resultados_formateados = []
                for fila in resultados:
                    if isinstance(fila, (list, tuple)) and len(fila) >= 5:
                        resultado_dict = {
                            'SERVIDOR': fila[0] if fila[0] else '',
                            'DATABASE_NAME': fila[1] if fila[1] else '',  # Puede venir como DATABASE_NAME
                            'BASE_DE_DATOS': fila[1] if fila[1] else '',   # O como BASE_DE_DATOS
                            'FECHA_DE_CREACION': fila[2] if fila[2] else '',
                            'ESTADO': fila[3] if fila[3] else '',
                            'TIPO_ESTADO': fila[4] if fila[4] else ''
                        }
                        resultados_formateados.append(resultado_dict)
                resultados = resultados_formateados
                
        except Exception as proc_error:
            logger.warning(f"Error con sp_estadosdb: {proc_error}")
            # Consulta directa como alternativa - simulando los campos del SP
            resultados_query = """
                SELECT 
                    @@SERVERNAME as SERVIDOR,
                    name as DATABASE_NAME,
                    create_date as FECHA_DE_CREACION,
                    state_desc as ESTADO,
                    CASE 
                        WHEN is_read_only = 0 THEN 'READ_WRITE'
                        ELSE 'READ_ONLY'
                    END as TIPO_ESTADO
                FROM sys.databases
                WHERE database_id > 4  -- Excluir bases del sistema
                ORDER BY name
            """
            resultados = ejecutar_consulta_personalizada(resultados_query)

        # Aplicar filtros adicionales en Python si es necesario
        if servidor:
            resultados = [r for r in resultados if servidor.lower() in r.get('SERVIDOR', '').lower()]
        if estado:
            resultados = [r for r in resultados if estado.lower() in r.get('ESTADO', '').lower()]

        # Estadísticas
        total = len(resultados)
        online = len([r for r in resultados if r.get('ESTADO', '').upper() == 'ONLINE'])
        servidores_unicos = len(set(r.get('SERVIDOR', '') for r in resultados if r.get('SERVIDOR')))
        otros = total - online
        
        stats = {
            'total': total,
            'online': online,
            'otros': otros,
            'servidores': servidores_unicos
        }

        # Paginación
        paginator = Paginator(resultados, PAGINATION['items_per_page'])
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Obtener lista de servidores para el filtro
        try:
            servidores = list(set(r.get('SERVIDOR', '') for r in resultados if r.get('SERVIDOR')))
            servidores = [{'servidor': srv} for srv in sorted(servidores)]
        except Exception:
            servidores = []

        # Obtener lista de estados para el filtro
        try:
            estados_unicos = list(set(r.get('ESTADO', '') for r in resultados if r.get('ESTADO')))
            estados = [{'estado': est} for est in sorted(estados_unicos)]
        except Exception:
            estados = []

        context = {
            'resultados': page_obj,
            'stats': stats,
            'servidor': servidor,
            'estado': estado,
            'servidores': servidores,
            'estados': estados,
        }

        return render(request, 'reportes/estados_db.html', context)

    except Exception as e:
        logger.error(f"Error en estados DB: {e}")
        context = {
            'error': f'Error al cargar los estados de bases de datos: {str(e)}',
            'resultados': [],
            'stats': {'total': 0, 'online': 0, 'otros': 0, 'servidores': 0},
            'servidor': '',
            'estado': '',
            'servidores': [],
            'estados': []
        }
        return render(request, 'reportes/estados_db.html', context)


@login_required
def ultimos_backup_view(request):
    """Reporte de últimos backups usando sp_ultimosbck"""
    try:
        # Usar procedimiento almacenado
        try:
            resultados = ejecutar_procedimiento_almacenado('sp_ultimosbck')
        except Exception as proc_error:
            logger.warning(f"Error con sp_ultimosbck: {proc_error}")
            # Consulta alternativa
            resultados = ejecutar_consulta_personalizada("""
                WITH UltimosBackupsPorBD AS (
                    SELECT 
                        SERVIDOR,
                        DatabaseName,
                        IPSERVER,
                        TYPE,
                        FECHA,
                        HORA,
                        ROW_NUMBER() OVER (
                            PARTITION BY SERVIDOR, DatabaseName 
                            ORDER BY 
                                CONVERT(date, SUBSTRING(FECHA,7,4) + '-' + SUBSTRING(FECHA,4,2) + '-' + SUBSTRING(FECHA,1,2)) DESC,
                                CONVERT(time, HORA) DESC
                        ) as rn,
                        DATEDIFF(hour, 
                            CONVERT(datetime, SUBSTRING(FECHA,7,4) + '-' + SUBSTRING(FECHA,4,2) + '-' + SUBSTRING(FECHA,1,2) + ' ' + HORA), 
                            GETDATE()
                        ) as horas_transcurridas
                    FROM BACKUPSGENERADOS
                    WHERE SERVIDOR IS NOT NULL AND DatabaseName IS NOT NULL
                )
                SELECT 
                    SERVIDOR,
                    DatabaseName,
                    IPSERVER,
                    TYPE,
                    FECHA,
                    HORA,
                    horas_transcurridas,
                    CASE 
                        WHEN horas_transcurridas <= 24 THEN 'success'
                        WHEN horas_transcurridas <= 48 THEN 'warning'
                        ELSE 'danger'
                    END as status_class
                FROM UltimosBackupsPorBD
                WHERE rn = 1
                ORDER BY 
                    CONVERT(date, SUBSTRING(FECHA,7,4) + '-' + SUBSTRING(FECHA,4,2) + '-' + SUBSTRING(FECHA,1,2)) DESC,
                    CONVERT(time, HORA) DESC
            """)

        context = {
            'resultados': resultados,
        }

        return render(request, 'reportes/ultimos_bck.html', context)

    except Exception as e:
        logger.error(f"Error en últimos backup: {e}")
        context = {
            'error': f'Error al cargar los últimos backups: {str(e)}',
            'resultados': []
        }
        return render(request, 'reportes/ultimos_bck.html', context)


@login_required
def listar_bd_view(request):
    """Listado de bases de datos usando BACKUPSGENERADOS"""
    try:
        # Consulta compatible con SQL Server 2008+
        query = """
            SELECT 
                bg.DatabaseName as database_name,
                bg.SERVIDOR as servidor,
                bg.IPSERVER as ip_servidor,
                COUNT(*) as total_backups,
                MAX(CONVERT(date, SUBSTRING(bg.FECHA,7,4) + '-' + SUBSTRING(bg.FECHA,4,2) + '-' + SUBSTRING(bg.FECHA,1,2))) as ultimo_backup,
                COUNT(DISTINCT bg.TYPE) as tipos_backup_count,
                STUFF((
                    SELECT DISTINCT ', ' + TYPE
                    FROM BACKUPSGENERADOS bg2
                    WHERE bg2.DatabaseName = bg.DatabaseName AND bg2.SERVIDOR = bg.SERVIDOR
                    FOR XML PATH('')
                ), 1, 2, '') as tipos_backup
            FROM BACKUPSGENERADOS bg
            WHERE bg.DatabaseName IS NOT NULL AND bg.SERVIDOR IS NOT NULL
            GROUP BY bg.DatabaseName, bg.SERVIDOR, bg.IPSERVER
            ORDER BY bg.SERVIDOR, bg.DatabaseName
        """
        
        resultados = ejecutar_consulta_personalizada(query)

        context = {
            'resultados': resultados,
        }

        return render(request, 'reportes/listar_bd.html', context)

    except Exception as e:
        logger.error(f"Error en listar BD: {e}")
        context = {
            'error': f'Error al cargar el listado de bases de datos: {str(e)}',
            'resultados': []
        }
        return render(request, 'reportes/listar_bd.html', context)


@login_required
@require_http_methods(["GET"])
def api_dashboard_metrics(request):
    """API para métricas del dashboard en tiempo real"""
    try:
        metrics_query = """
            SELECT 
                (SELECT COUNT(DISTINCT SERVIDOR) FROM BACKUPSGENERADOS WHERE SERVIDOR IS NOT NULL) as total_servidores,
                (SELECT COUNT(DISTINCT DatabaseName) FROM BACKUPSGENERADOS WHERE DatabaseName IS NOT NULL) as total_bases_datos,
                (SELECT COUNT(*) FROM BACKUPSGENERADOS) as total_backups_registrados,
                (SELECT COUNT(*) FROM JOBSBACKUPGENERADOS) as total_jobs_registrados
        """
        
        metrics = ejecutar_consulta_personalizada(metrics_query)
        
        return JsonResponse({
            'success': True,
            'data': metrics[0] if metrics else {},
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error en API metrics: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def disk_growth_view(request):
    """Reporte de crecimiento de discos usando DiskGrowthLog y sp_MonitorDiskGrowth"""
    try:
        # Filtros
        fecha_inicio = request.GET.get('fecha_inicio', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        fecha_fin = request.GET.get('fecha_fin', timezone.now().strftime('%Y-%m-%d'))
        servidor = request.GET.get('servidor', '')
        base_datos = request.GET.get('base_datos', '')
        
        logger.info(f"Ejecutando reporte de disk growth: {fecha_inicio} a {fecha_fin}")
        
        # Primero, ejecutar el SP para actualizar los datos más recientes
        try:
            ejecutar_procedimiento_almacenado('usp_MonitorDiskGrowth')
            logger.info("SP usp_MonitorDiskGrowth ejecutado exitosamente")
        except Exception as sp_error:
            logger.warning(f"Error ejecutando usp_MonitorDiskGrowth: {sp_error}")
            # Continuar con el reporte aunque falle el SP
        
        # Consultar datos históricos de la tabla DiskGrowthLog
        query = """
            SELECT 
                LogID,
                ServerIP,
                DatabaseName,
                FileName,
                FilePath,
                FileSizeMB,
                DiskFreeMB,
                LogDate,
                CAST((DiskFreeMB * 100.0 / (FileSizeMB + DiskFreeMB)) AS DECIMAL(5,2)) as PorcentajeLibre,
                CASE 
                    WHEN DiskFreeMB < 10240 THEN 'danger'  -- Menos de 10GB
                    WHEN DiskFreeMB < 51200 THEN 'warning' -- Menos de 50GB
                    ELSE 'success'
                END as status_class
            FROM DiskGrowthLog
            WHERE CONVERT(date, LogDate) BETWEEN %s AND %s
        """
        
        params = [fecha_inicio, fecha_fin]
        
        # Aplicar filtros adicionales
        if servidor:
            query += " AND ServerIP LIKE %s"
            params.append(f'%{servidor}%')
        if base_datos:
            query += " AND DatabaseName LIKE %s"
            params.append(f'%{base_datos}%')
            
        query += " ORDER BY LogDate DESC, ServerIP, DatabaseName, FileName"
        
        resultados = ejecutar_consulta_personalizada(query, params)
        
        # Calcular estadísticas
        if resultados:
            total_registros = len(resultados)
            espacio_total_usado = sum(float(r.get('FileSizeMB', 0)) for r in resultados)
            espacio_total_libre = sum(float(r.get('DiskFreeMB', 0)) for r in resultados)
            servidores_unicos = len(set(r.get('ServerIP', '') for r in resultados))
            bases_unicas = len(set(r.get('DatabaseName', '') for r in resultados))
            
            # Identificar discos con poco espacio
            discos_criticos = len([r for r in resultados if r.get('status_class') == 'danger'])
            discos_advertencia = len([r for r in resultados if r.get('status_class') == 'warning'])
            
            estadisticas = {
                'total_registros': total_registros,
                'espacio_usado_gb': round(espacio_total_usado / 1024, 2),
                'espacio_libre_gb': round(espacio_total_libre / 1024, 2),
                'servidores': servidores_unicos,
                'bases_datos': bases_unicas,
                'discos_criticos': discos_criticos,
                'discos_advertencia': discos_advertencia
            }
        else:
            estadisticas = {
                'total_registros': 0,
                'espacio_usado_gb': 0,
                'espacio_libre_gb': 0,
                'servidores': 0,
                'bases_datos': 0,
                'discos_criticos': 0,
                'discos_advertencia': 0
            }
        
        # Paginación
        paginator = Paginator(resultados, PAGINATION['items_per_page'])
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Obtener lista de servidores únicos para el filtro
        try:
            servidores = ejecutar_consulta_personalizada("""
                SELECT DISTINCT ServerIP as servidor, COUNT(*) as total_logs
                FROM DiskGrowthLog 
                WHERE ServerIP IS NOT NULL AND ServerIP != ''
                GROUP BY ServerIP 
                ORDER BY ServerIP
            """)
        except Exception:
            servidores = []
            
        # Obtener lista de bases de datos únicas para el filtro
        try:
            bases_datos = ejecutar_consulta_personalizada("""
                SELECT DISTINCT DatabaseName as base_datos, COUNT(*) as total_logs
                FROM DiskGrowthLog 
                WHERE DatabaseName IS NOT NULL AND DatabaseName != ''
                GROUP BY DatabaseName 
                ORDER BY DatabaseName
            """)
        except Exception:
            bases_datos = []
        
        # Obtener tendencia de crecimiento (últimos 7 días)
        try:
            tendencia_query = """
                SELECT 
                    CONVERT(date, LogDate) as Fecha,
                    ServerIP,
                    DatabaseName,
                    MAX(FileSizeMB) as TamanoMB,
                    MIN(DiskFreeMB) as EspacioLibreMB
                FROM DiskGrowthLog
                WHERE LogDate >= DATEADD(day, -7, GETDATE())
            """
            if servidor:
                tendencia_query += f" AND ServerIP LIKE '%{servidor}%'"
            if base_datos:
                tendencia_query += f" AND DatabaseName LIKE '%{base_datos}%'"
            tendencia_query += """
                GROUP BY CONVERT(date, LogDate), ServerIP, DatabaseName
                ORDER BY Fecha DESC
            """
            tendencia = ejecutar_consulta_personalizada(tendencia_query)
        except Exception:
            tendencia = []
        
        context = {
            'resultados': page_obj,
            'estadisticas': estadisticas,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'servidor': servidor,
            'base_datos': base_datos,
            'servidores': servidores,
            'bases_datos': bases_datos,
            'tendencia': tendencia[:50] if tendencia else []  # Limitar a 50 registros para el gráfico
        }
        
        return render(request, 'reportes/disk_growth.html', context)
        
    except Exception as e:
        logger.error(f"Error en disk growth: {e}")
        context = {
            'error': f'Error al cargar el reporte de crecimiento de discos: {str(e)}',
            'resultados': [],
            'estadisticas': {
                'total_registros': 0,
                'espacio_usado_gb': 0,
                'espacio_libre_gb': 0,
                'servidores': 0,
                'bases_datos': 0,
                'discos_criticos': 0,
                'discos_advertencia': 0
            },
            'fecha_inicio': fecha_inicio if 'fecha_inicio' in locals() else '',
            'fecha_fin': fecha_fin if 'fecha_fin' in locals() else '',
            'servidor': '',
            'base_datos': '',
            'servidores': [],
            'bases_datos': [],
            'tendencia': []
        }
        return render(request, 'reportes/disk_growth.html', context)
