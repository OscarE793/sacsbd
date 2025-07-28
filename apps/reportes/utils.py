# apps/reportes/utils.py
from django.db import connection
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def ejecutar_procedimiento_almacenado(proc_name, params=None):
    """
    Ejecuta un procedimiento almacenado y devuelve los resultados
    
    Args:
        proc_name (str): Nombre del procedimiento almacenado
        params (list): Lista de parámetros para el procedimiento
    
    Returns:
        list: Lista de diccionarios con los resultados
    """
    try:
        with connection.cursor() as cursor:
            # Construir la llamada al procedimiento
            if params:
                # Convertir parámetros según el tipo
                formatted_params = []
                for param in params:
                    if isinstance(param, str) and param != '':
                        formatted_params.append(f"'{param}'")
                    elif param == '':
                        formatted_params.append("''")
                    elif param is None:
                        formatted_params.append("NULL")
                    else:
                        formatted_params.append(str(param))
                
                params_str = ', '.join(formatted_params)
                sql = f"EXEC {proc_name} {params_str}"
                logger.info(f"Ejecutando: {sql}")
                cursor.execute(sql)
            else:
                sql = f"EXEC {proc_name}"
                logger.info(f"Ejecutando: {sql}")
                cursor.execute(sql)
            
            # Obtener nombres de columnas
            columns = [col[0] for col in cursor.description] if cursor.description else []
            
            # Obtener resultados
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            logger.info(f"Procedimiento {proc_name} ejecutado exitosamente. {len(results)} registros obtenidos.")
            return results
            
    except Exception as e:
        logger.error(f"Error ejecutando procedimiento {proc_name}: {e}")
        return []

def ejecutar_consulta_personalizada(query, params=None):
    """
    Ejecuta una consulta SQL personalizada
    
    Args:
        query (str): Consulta SQL
        params (list): Parámetros para la consulta
    
    Returns:
        list: Lista de diccionarios con los resultados
    """
    try:
        with connection.cursor() as cursor:
            logger.info(f"Ejecutando consulta personalizada")
            cursor.execute(query, params or [])
            columns = [col[0] for col in cursor.description] if cursor.description else []
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            logger.info(f"Consulta ejecutada exitosamente. {len(results)} registros obtenidos.")
            return results
    except Exception as e:
        logger.error(f"Error ejecutando consulta: {e}")
        return []

def obtener_servidores_disponibles():
    """Obtiene la lista de servidores disponibles desde BACKUPSGENERADOS"""
    try:
        query = """
            SELECT DISTINCT 
                SERVIDOR as servidor, 
                IPSERVER as ip_servidor,
                COUNT(*) as total_backups
            FROM BACKUPSGENERADOS 
            WHERE SERVIDOR IS NOT NULL AND SERVIDOR != ''
            GROUP BY SERVIDOR, IPSERVER 
            ORDER BY SERVIDOR
        """
        return ejecutar_consulta_personalizada(query)
    except Exception as e:
        logger.error(f"Error obteniendo servidores: {e}")
        return []

def obtener_bases_datos():
    """Obtiene la lista de bases de datos desde BACKUPSGENERADOS"""
    try:
        query = """
            SELECT DISTINCT 
                DatabaseName as database_name, 
                SERVIDOR as servidor,
                IPSERVER as ip_servidor,
                COUNT(*) as total_backups
            FROM BACKUPSGENERADOS 
            WHERE DatabaseName IS NOT NULL AND DatabaseName != ''
            GROUP BY DatabaseName, SERVIDOR, IPSERVER
            ORDER BY DatabaseName, SERVIDOR
        """
        return ejecutar_consulta_personalizada(query)
    except Exception as e:
        logger.error(f"Error obteniendo bases de datos: {e}")
        return []

def formatear_resultado_backup(resultado):
    """
    Formatea los resultados de backup para mejor presentación
    """
    if not resultado:
        return resultado
    
    # Agregar clases CSS basadas en el estado
    if 'RESULTADO' in resultado:
        resultado_texto = str(resultado['RESULTADO']).lower()
        if 'exitoso' in resultado_texto or 'succeeded' in resultado_texto:
            resultado['css_class'] = 'success'
            resultado['icono'] = 'ki-check-circle'
        elif 'fallido' in resultado_texto or 'failed' in resultado_texto or 'error' in resultado_texto:
            resultado['css_class'] = 'danger'
            resultado['icono'] = 'ki-cross-circle'
        else:
            resultado['css_class'] = 'warning'
            resultado['icono'] = 'ki-information'
    
    # Formatear fechas si es necesario
    if 'FECHA' in resultado and 'HORA' in resultado:
        try:
            fecha_hora_str = f"{resultado['FECHA']} {resultado['HORA']}"
            # Intentar parsear la fecha en formato DD/MM/YYYY HH:MM:SS
            fecha_hora = datetime.strptime(fecha_hora_str, "%d/%m/%Y %H:%M:%S")
            resultado['fecha_formateada'] = fecha_hora.strftime("%d/%m/%Y")
            resultado['hora_formateada'] = fecha_hora.strftime("%H:%M:%S")
            resultado['fecha_hora_completa'] = fecha_hora
        except ValueError:
            # Si no se puede parsear, mantener valores originales
            resultado['fecha_formateada'] = resultado['FECHA']
            resultado['hora_formateada'] = resultado['HORA']
    
    # Formatear tipo de backup
    if 'TYPE' in resultado:
        tipos_backup = {
            'FULL': 'Completo',
            'INCREMENTAL': 'Incremental',
            'DIFF': 'Diferencial',
            'LOG': 'Log de Transacciones'
        }
        resultado['tipo_descripcion'] = tipos_backup.get(resultado['TYPE'], resultado['TYPE'])
    
    return resultado

def calcular_estadisticas_cumplimiento(resultados):
    """
    Calcula estadísticas de cumplimiento de backups
    """
    total = len(resultados)
    if total == 0:
        return {
            'total': 0, 
            'exitosos': 0, 
            'fallidos': 0, 
            'porcentaje_exito': 0,
            'compliant': 0,
            'warning': 0,
            'critical': 0
        }
    
    # Para jobs (basado en RESULTADO)
    exitosos = 0
    fallidos = 0
    
    # Para backups (basado en estado_cumplimiento)
    compliant = 0
    warning = 0
    critical = 0
    
    for resultado in resultados:
        # Estadísticas de jobs
        if 'RESULTADO' in resultado:
            resultado_texto = str(resultado['RESULTADO']).lower()
            if 'exitoso' in resultado_texto or 'succeeded' in resultado_texto:
                exitosos += 1
            elif 'fallido' in resultado_texto or 'failed' in resultado_texto or 'error' in resultado_texto:
                fallidos += 1
        
        # Estadísticas de cumplimiento de backups
        if 'estado_cumplimiento' in resultado:
            estado = resultado['estado_cumplimiento']
            if estado == 'Compliant':
                compliant += 1
            elif estado == 'Warning':
                warning += 1
            elif estado == 'Critical':
                critical += 1
    
    porcentaje_exito = round((exitosos / total) * 100, 2) if total > 0 else 0
    porcentaje_cumplimiento = round((compliant / total) * 100, 2) if total > 0 else 0
    
    return {
        'total': total,
        'exitosos': exitosos,
        'fallidos': fallidos,
        'porcentaje_exito': porcentaje_exito,
        'compliant': compliant,
        'warning': warning,
        'critical': critical,
        'porcentaje_cumplimiento': porcentaje_cumplimiento
    }

def convertir_fecha_formato_sp(fecha_str):
    """
    Convierte fecha de formato YYYY-MM-DD a DD/MM/YYYY para usar en sp_genBak
    """
    try:
        fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d")
        return fecha_obj.strftime("%d/%m/%Y")
    except ValueError:
        return fecha_str

def obtener_backups_por_fecha(fecha):
    """
    Obtiene backups por fecha específica usando sp_genBak
    """
    try:
        from .config import STORED_PROCEDURES
        
        # Convertir fecha al formato esperado por el procedimiento
        fecha_formateada = convertir_fecha_formato_sp(fecha)
        
        resultados = ejecutar_procedimiento_almacenado(
            STORED_PROCEDURES['backups_por_fecha'],
            [fecha_formateada]
        )
        
        # Formatear resultados
        return [formatear_resultado_backup(r) for r in resultados]
        
    except Exception as e:
        logger.error(f"Error obteniendo backups por fecha {fecha}: {e}")
        return []

def obtener_jobs_por_rango_fechas(fecha_inicio, fecha_fin):
    """
    Obtiene jobs por rango de fechas usando sp_resultadoJobsBck
    """
    try:
        from .config import STORED_PROCEDURES
        
        resultados = ejecutar_procedimiento_almacenado(
            STORED_PROCEDURES['jobs_resultado'],
            [fecha_inicio, fecha_fin]
        )
        
        # Formatear resultados
        return [formatear_resultado_backup(r) for r in resultados]
        
    except Exception as e:
        logger.error(f"Error obteniendo jobs entre {fecha_inicio} y {fecha_fin}: {e}")
        return []

def obtener_programacion_vs_ejecucion(fecha_inicio, fecha_fin):
    """
    Obtiene comparación de programación vs ejecución usando sp_Programaciondebcks
    """
    try:
        from .config import STORED_PROCEDURES
        
        resultados = ejecutar_procedimiento_almacenado(
            STORED_PROCEDURES['programacion_backups'],
            [fecha_inicio, fecha_fin]
        )
        
        return resultados
        
    except Exception as e:
        logger.error(f"Error obteniendo programación vs ejecución entre {fecha_inicio} y {fecha_fin}: {e}")
        return []

def validar_conexion_bd():
    """
    Valida que la conexión a la base de datos funcione correctamente
    """
    try:
        query = "SELECT 1 as test"
        resultado = ejecutar_consulta_personalizada(query)
        return len(resultado) > 0
    except Exception as e:
        logger.error(f"Error validando conexión BD: {e}")
        return False

def obtener_estadisticas_generales():
    """
    Obtiene estadísticas generales del sistema
    """
    try:
        query = """
            SELECT 
                (SELECT COUNT(DISTINCT SERVIDOR) FROM BACKUPSGENERADOS) as total_servidores,
                (SELECT COUNT(DISTINCT DatabaseName) FROM BACKUPSGENERADOS) as total_bases_datos,
                (SELECT COUNT(*) FROM BACKUPSGENERADOS) as total_backups,
                (SELECT COUNT(*) FROM JOBSBACKUPGENERADOS) as total_jobs,
                (SELECT COUNT(*) FROM BACKUPSGENERADOS WHERE FECHA = CONVERT(varchar, GETDATE(), 103)) as backups_hoy,
                (SELECT COUNT(*) FROM JOBSBACKUPGENERADOS WHERE CONVERT(date, FECHA_Y_HORA_INICIO) = CONVERT(date, GETDATE())) as jobs_hoy
        """
        
        resultado = ejecutar_consulta_personalizada(query)
        return resultado[0] if resultado else {}
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas generales: {e}")
        return {}
