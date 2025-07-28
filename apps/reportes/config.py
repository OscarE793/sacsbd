# apps/reportes/config.py
"""
Configuración completa de procedimientos almacenados y consultas para reportes SACSBD
Compatibilidad con SQL Server 2008/2012/2014+
"""

# Nombres de procedimientos almacenados disponibles en el sistema
STORED_PROCEDURES = {
    # === PROCEDIMIENTOS PRINCIPALES ===
    'backup_history': 'sp_backup_history',                    # Historial de backups
    'insertar_backups': 'sp_BakGenerados',                   # Inserta backups del día
    'contar_backups': 'sp_countBck',                         # Cuenta backups
    'contar_total_backups': 'sp_countTotalBck',              # Cuenta total de backups
    'ejecucion_jobs': 'sp_ejecutonjobs_bck',                 # Ejecución de jobs de backup
    'estados_db': 'sp_estadosdb',                            # Estados de bases de datos
    'backups_por_fecha': 'sp_genBak',                        # Backups por fecha específica
    'historico_backups': 'sp_historicoBck',                  # Histórico de backups
    'lista_estados': 'sp_Lista_Estado',                      # Lista estados detallados
    'lista_usuarios': 'sp_listausuarios',                    # Lista de usuarios
    'porcentaje_backups': 'sp_porcentajeGenBak',             # Porcentaje de backups generados
    'programacion_backups': 'sp_Programaciondebcks',         # Programación vs ejecución
    'promedio_ultimos': 'sp_PromedioUltimosBck',             # Promedio de últimos backups
    'jobs_resultado': 'sp_resultadoJobsBck',                 # Resultados de jobs
    'total_bd': 'sp_TotalBD',                                # Total de bases de datos
    'total_semana': 'sp_TotalSemana',                        # Total backups semana
    'ultimos_backup': 'sp_ultimosbck',                       # Últimos backups (tabla ULTIMOBCK)
    
    # === PROCEDIMIENTOS PARA REPORTES ESPECÍFICOS ===
    'dashboard_metricas': 'sp_countTotalBck',                # Para métricas del dashboard
    'cumplimiento_backup': 'sp_porcentajeGenBak',            # Para reporte de cumplimiento
    'archivos_backup': 'sp_genBak',                          # Para reporte de archivos
}

# Consultas directas optimizadas para SQL Server 2008+ (sin TRY_CONVERT)
QUERIES = {
    'servidores_disponibles': """
        SELECT DISTINCT 
            SERVIDOR as servidor, 
            IPSERVER as ip_servidor,
            COUNT(*) as total_backups
        FROM BACKUPSGENERADOS 
        WHERE SERVIDOR IS NOT NULL AND SERVIDOR != ''
        GROUP BY SERVIDOR, IPSERVER 
        ORDER BY SERVIDOR
    """,
    
    'bases_datos_disponibles': """
        SELECT DISTINCT 
            DatabaseName as database_name, 
            SERVIDOR as servidor,
            IPSERVER as ip_servidor,
            COUNT(*) as total_backups
        FROM BACKUPSGENERADOS 
        WHERE DatabaseName IS NOT NULL AND DatabaseName != ''
        GROUP BY DatabaseName, SERVIDOR, IPSERVER
        ORDER BY DatabaseName, SERVIDOR
    """,
    
    'tipos_backup': """
        SELECT DISTINCT 
            TYPE as tipo_backup, 
            COUNT(*) as cantidad,
            CASE TYPE
                WHEN 'FULL' THEN 'Completo'
                WHEN 'INCREMENTAL' THEN 'Incremental'
                WHEN 'DIFF' THEN 'Diferencial'
                WHEN 'LOG' THEN 'Log de Transacciones'
                ELSE ISNULL(TYPE, 'Sin tipo')
            END as descripcion
        FROM BACKUPSGENERADOS 
        WHERE TYPE IS NOT NULL
        GROUP BY TYPE 
        ORDER BY cantidad DESC
    """,
    
    'resumen_jobs': """
        SELECT 
            RESULTADO,
            COUNT(*) as cantidad,
            CAST(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() AS DECIMAL(5,2)) as porcentaje
        FROM JOBSBACKUPGENERADOS 
        WHERE FECHA_Y_HORA_INICIO >= DATEADD(day, -7, GETDATE())
        GROUP BY RESULTADO
        ORDER BY cantidad DESC
    """,
    
    'dashboard_metricas': """
        SELECT 
            (SELECT COUNT(DISTINCT SERVIDOR) FROM BACKUPSGENERADOS WHERE SERVIDOR IS NOT NULL) as total_servidores,
            (SELECT COUNT(DISTINCT DatabaseName) FROM BACKUPSGENERADOS WHERE DatabaseName IS NOT NULL) as total_bases_datos,
            (SELECT COUNT(*) FROM BACKUPSGENERADOS WHERE FECHA = CONVERT(varchar, GETDATE(), 103)) as backups_hoy,
            (SELECT COUNT(*) FROM BACKUPSGENERADOS WHERE 
                CONVERT(date, SUBSTRING(FECHA,7,4) + '-' + SUBSTRING(FECHA,4,2) + '-' + SUBSTRING(FECHA,1,2)) 
                >= DATEADD(day, -7, GETDATE())
            ) as backups_semana,
            (SELECT COUNT(*) FROM JOBSBACKUPGENERADOS WHERE 
                FECHA_Y_HORA_INICIO >= DATEADD(day, -1, GETDATE()) AND 
                (RESULTADO LIKE '%Exitoso%' OR RESULTADO LIKE '%exitoso%')
            ) as jobs_exitosos_hoy,
            (SELECT COUNT(*) FROM JOBSBACKUPGENERADOS WHERE 
                FECHA_Y_HORA_INICIO >= DATEADD(day, -1, GETDATE()) AND 
                (RESULTADO LIKE '%Fallido%' OR RESULTADO LIKE '%fallido%' OR RESULTADO LIKE '%Error%')
            ) as jobs_fallidos_hoy,
            (SELECT COUNT(*) FROM BACKUPSGENERADOS) as total_backups_registrados,
            (SELECT COUNT(*) FROM JOBSBACKUPGENERADOS) as total_jobs_registrados
    """,
    
    'cumplimiento_backup': """
        WITH UltimosBackups AS (
            SELECT 
                SERVIDOR,
                DatabaseName,
                IPSERVER,
                TYPE,
                FECHA,
                HORA,
                physical_device_name,
                BCK_ID,
                ROW_NUMBER() OVER (
                    PARTITION BY SERVIDOR, DatabaseName, TYPE 
                    ORDER BY 
                        CONVERT(date, SUBSTRING(FECHA,7,4) + '-' + SUBSTRING(FECHA,4,2) + '-' + SUBSTRING(FECHA,1,2)) DESC,
                        CONVERT(time, HORA) DESC
                ) as rn,
                DATEDIFF(hour, 
                    CONVERT(datetime, SUBSTRING(FECHA,7,4) + '-' + SUBSTRING(FECHA,4,2) + '-' + SUBSTRING(FECHA,1,2) + ' ' + HORA), 
                    GETDATE()
                ) as horas_desde_backup
            FROM BACKUPSGENERADOS
            WHERE CONVERT(date, SUBSTRING(FECHA,7,4) + '-' + SUBSTRING(FECHA,4,2) + '-' + SUBSTRING(FECHA,1,2)) >= DATEADD(day, -30, GETDATE())
                AND SERVIDOR IS NOT NULL 
                AND DatabaseName IS NOT NULL
        )
        SELECT 
            SERVIDOR as servidor,
            DatabaseName as base_datos,
            IPSERVER as ip_servidor,
            TYPE as tipo_backup,
            FECHA as fecha_backup,
            HORA as hora_backup,
            horas_desde_backup,
            CASE 
                WHEN horas_desde_backup <= 24 THEN 'Compliant'
                WHEN horas_desde_backup <= 48 THEN 'Warning' 
                ELSE 'Critical'
            END as estado_cumplimiento,
            CASE 
                WHEN horas_desde_backup <= 24 THEN 'success'
                WHEN horas_desde_backup <= 48 THEN 'warning'
                ELSE 'danger'
            END as css_class
        FROM UltimosBackups
        WHERE rn = 1
        ORDER BY horas_desde_backup DESC, SERVIDOR, DatabaseName
    """,
    
    'archivos_backup': """
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
        WHERE CONVERT(date, SUBSTRING(FECHA,7,4) + '-' + SUBSTRING(FECHA,4,2) + '-' + SUBSTRING(FECHA,1,2)) >= DATEADD(day, -30, GETDATE())
            AND physical_device_name IS NOT NULL
        ORDER BY 
            CONVERT(date, SUBSTRING(FECHA,7,4) + '-' + SUBSTRING(FECHA,4,2) + '-' + SUBSTRING(FECHA,1,2)) DESC,
            CONVERT(time, HORA) DESC
    """,
    
    'jobs_detallados': """
        SELECT 
            SERVIDOR,
            RESULTADO,
            FECHA_Y_HORA_INICIO,
            NOMBRE_DEL_JOB,
            PASO,
            NOMBRE_DEL_PASO,
            MENSAJE,
            IPSERVER,
            CASE 
                WHEN RESULTADO LIKE '%Exitoso%' OR RESULTADO LIKE '%exitoso%' THEN 'success'
                WHEN RESULTADO LIKE '%Fallido%' OR RESULTADO LIKE '%fallido%' OR RESULTADO LIKE '%Error%' THEN 'danger'
                WHEN RESULTADO LIKE '%Advertencia%' OR RESULTADO LIKE '%Warning%' THEN 'warning'
                ELSE 'secondary'
            END as css_class,
            CASE 
                WHEN RESULTADO LIKE '%Exitoso%' OR RESULTADO LIKE '%exitoso%' THEN 'ki-check-circle'
                WHEN RESULTADO LIKE '%Fallido%' OR RESULTADO LIKE '%fallido%' OR RESULTADO LIKE '%Error%' THEN 'ki-cross-circle'
                ELSE 'ki-information'
            END as icono
        FROM JOBSBACKUPGENERADOS
        WHERE FECHA_Y_HORA_INICIO >= DATEADD(day, -30, GETDATE())
        ORDER BY FECHA_Y_HORA_INICIO DESC
    """,
    
    'ultimos_backups_por_bd': """
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
    """
}

# Configuración de filtros por defecto
DEFAULT_FILTERS = {
    'dias_atras': 30,
    'tipos_backup': ['FULL', 'INCREMENTAL', 'DIFF'],
    'estados_job': ['Exitoso', 'Fallido'],
    'servidores_excluir': []
}

# Configuración de paginación
PAGINATION = {
    'items_per_page': 25,
    'max_items_per_page': 100
}

# Configuración de alertas y umbrales
THRESHOLDS = {
    'backup_critico_horas': 48,      # Horas sin backup para considerar crítico
    'backup_warning_horas': 24,      # Horas sin backup para considerar warning
    'job_failure_threshold': 5,      # Número de fallos consecutivos para alerta
    'disk_space_warning': 85,        # % de espacio usado para warning
    'disk_space_critical': 95        # % de espacio usado para crítico
}

# Configuración de colores para gráficos
CHART_COLORS = {
    'success': '#50cd89',
    'warning': '#ffc700', 
    'danger': '#f1416c',
    'info': '#009ef7',
    'primary': '#3f4254',
    'secondary': '#7e8299'
}

# Mensajes de estado personalizados
STATUS_MESSAGES = {
    'backup': {
        'FULL': 'Backup completo',
        'INCREMENTAL': 'Backup incremental',
        'DIFF': 'Backup diferencial',
        'LOG': 'Backup de log'
    },
    'job': {
        'exitoso': 'Job ejecutado exitosamente',
        'fallido': 'Job falló en la ejecución',
        'advertencia': 'Job completado con advertencias',
        'en_ejecucion': 'Job en ejecución'
    },
    'cumplimiento': {
        'Compliant': 'Backup actualizado',
        'Warning': 'Backup con retraso menor',
        'Critical': 'Backup crítico - requiere atención'
    }
}

# Mapeo detallado de procedimientos con sus parámetros
PROCEDURE_PARAMS = {
    'sp_backup_history': {
        'params': [],
        'types': [],
        'description': 'Obtiene el historial completo de backups'
    },
    'sp_BakGenerados': {
        'params': ['fecha_backup'],
        'types': ['date'],
        'description': 'Inserta backups del día en BACKUPSGENERADOS'
    },
    'sp_countBck': {
        'params': [],
        'types': [],
        'description': 'Cuenta el número de backups'
    },
    'sp_countTotalBck': {
        'params': [],
        'types': [],
        'description': 'Cuenta el total de backups en el sistema'
    },
    'sp_ejecutonjobs_bck': {
        'params': [],
        'types': [],
        'description': 'Obtiene información de ejecución de jobs de backup'
    },
    'sp_estadosdb': {
        'params': [],
        'types': [],
        'description': 'Obtiene estados de bases de datos desde ESTADODB'
    },
    'sp_genBak': {
        'params': ['fecha_backup'],
        'types': ['VARCHAR(20)'],
        'description': 'Obtiene backups por fecha específica (formato DD/MM/YYYY)'
    },
    'sp_historicoBck': {
        'params': [],
        'types': [],
        'description': 'Obtiene el histórico de backups'
    },
    'sp_Lista_Estado': {
        'params': [],
        'types': [],
        'description': 'Lista detallada de estados de bases de datos'
    },
    'sp_listausuarios': {
        'params': [],
        'types': [],
        'description': 'Lista de usuarios del sistema'
    },
    'sp_porcentajeGenBak': {
        'params': [],
        'types': [],
        'description': 'Porcentaje de backups generados'
    },
    'sp_Programaciondebcks': {
        'params': ['fecha_inicio', 'fecha_fin'],
        'types': ['date', 'date'],
        'description': 'Compara programación vs ejecución de backups'
    },
    'sp_PromedioUltimosBck': {
        'params': ['fecha'],
        'types': ['date'],
        'description': 'Obtiene promedio de tamaños de backup por fecha'
    },
    'sp_resultadoJobsBck': {
        'params': ['fecha_inicio', 'fecha_fin'],
        'types': ['date', 'date'],
        'description': 'Obtiene resultados de jobs entre fechas'
    },
    'sp_TotalBD': {
        'params': [],
        'types': [],
        'description': 'Total de bases de datos en el sistema'
    },
    'sp_TotalSemana': {
        'params': [],
        'types': [],
        'description': 'Total de backups de la semana'
    },
    'sp_ultimosbck': {
        'params': [],
        'types': [],
        'description': 'Últimos backups desde tabla ULTIMOBCK'
    }
}

# Configuración de reportes disponibles
REPORTES_CONFIG = {
    'cumplimiento_backup': {
        'titulo': 'Cumplimiento de Backup',
        'descripcion': 'Análisis de cumplimiento de backups por servidor y base de datos',
        'procedimiento': 'sp_porcentajeGenBak',
        'query_alternativa': 'cumplimiento_backup',
        'filtros': ['fecha_inicio', 'fecha_fin', 'servidor', 'tipo_backup'],
        'exportable': True
    },
    'jobs_backup': {
        'titulo': 'Jobs de Backup',
        'descripcion': 'Estado y resultados de jobs de backup ejecutados',
        'procedimiento': 'sp_resultadoJobsBck',
        'query_alternativa': 'jobs_detallados',
        'filtros': ['fecha_inicio', 'fecha_fin', 'servidor', 'resultado'],
        'exportable': True
    },
    'archivos_backup': {
        'titulo': 'Archivos de Backup',
        'descripcion': 'Ubicación y detalles de archivos de backup generados',
        'procedimiento': 'sp_genBak',
        'query_alternativa': 'archivos_backup',
        'filtros': ['dias_atras', 'servidor', 'tipo_backup'],
        'exportable': True
    },
    'estados_db': {
        'titulo': 'Estados de Bases de Datos',
        'descripcion': 'Estado actual de todas las bases de datos monitoreadas',
        'procedimiento': 'sp_Lista_Estado',
        'query_alternativa': None,
        'filtros': [],
        'exportable': True
    },
    'ultimos_backup': {
        'titulo': 'Últimos Backups',
        'descripcion': 'Último backup realizado por cada base de datos',
        'procedimiento': 'sp_ultimosbck',
        'query_alternativa': 'ultimos_backups_por_bd',
        'filtros': [],
        'exportable': True
    },
    'listar_bd': {
        'titulo': 'Inventario de Bases de Datos',
        'descripcion': 'Listado completo de bases de datos con información de backups',
        'procedimiento': None,
        'query_alternativa': 'bases_datos_disponibles',
        'filtros': ['servidor'],
        'exportable': True
    }
}

# Configuración de exportación de datos
EXPORT_CONFIG = {
    'formats': ['xlsx', 'csv', 'pdf'],
    'max_records': 10000,
    'chunk_size': 1000,
    'filename_pattern': 'SACSBD_{reporte}_{fecha}_{hora}'
}

# Configuración de cacheo
CACHE_CONFIG = {
    'dashboard_metrics': 300,      # 5 minutos
    'server_list': 3600,          # 1 hora
    'database_list': 3600,        # 1 hora
    'backup_stats': 900           # 15 minutos
}

# Configuración de monitoreo y alertas
MONITORING_CONFIG = {
    'check_interval_minutes': 15,
    'alert_thresholds': {
        'backup_failure_rate': 10,  # % de fallos para alertar
        'job_failure_consecutive': 3,  # Fallos consecutivos para alertar
        'backup_delay_hours': 48   # Horas de retraso para alertar
    },
    'notification_channels': ['email', 'dashboard'],
    'critical_databases': []  # Lista de bases críticas que requieren monitoreo especial
}
