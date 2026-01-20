# apps/reportes/utils_secure.py
"""
Versión segura de las funciones de utilidad con protección contra SQL injection.
Este archivo contiene las versiones corregidas que deben reemplazar a utils.py
"""

from django.db import connection
import logging
import re

logger = logging.getLogger(__name__)

# Whitelist de procedimientos almacenados permitidos
ALLOWED_STORED_PROCEDURES = {
    'sp_backup_history',
    'sp_BakGenerados',
    'sp_countBck',
    'sp_countTotalBck',
    'sp_ejecutonjobs_bck',
    'sp_estadosdb',
    'sp_genBak',
    'sp_historicoBck',
    'sp_Lista_Estado',
    'sp_listausuarios',
    'sp_porcentajeGenBak',
    'sp_Programaciondebcks',
    'sp_PromedioUltimosBck',
    'sp_resultadoJobsBck',
    'sp_TotalBD',
    'sp_TotalSemana',
    'sp_ultimosbck',
    'sp_DashboardMetrics',
    'sp_MonitorDatabaseStatus',
    'usp_MonitorDiskGrowth',
}


def ejecutar_procedimiento_almacenado_seguro(proc_name, params=None):
    """
    Ejecuta un procedimiento almacenado de forma SEGURA usando callproc().

    Cambios respecto a la versión anterior:
    1. Valida que el SP esté en la whitelist
    2. Usa cursor.callproc() en lugar de EXEC con f-strings
    3. No concatena valores en el SQL string

    Args:
        proc_name (str): Nombre del procedimiento almacenado
        params (list): Lista de parámetros para el procedimiento

    Returns:
        list: Lista de diccionarios con los resultados

    Raises:
        ValueError: Si el procedimiento no está permitido
    """
    # 1. Validar que el SP está permitido (previene ejecución de SPs arbitrarios)
    if proc_name not in ALLOWED_STORED_PROCEDURES:
        error_msg = f"Procedimiento no permitido: {proc_name}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    try:
        with connection.cursor() as cursor:
            # 2. Usar callproc() - Método SEGURO del DB-API
            if params:
                logger.info(f"Ejecutando: {proc_name} con {len(params)} parámetros")
                cursor.callproc(proc_name, params)  # ✅ SEGURO
            else:
                logger.info(f"Ejecutando: {proc_name}")
                cursor.callproc(proc_name)  # ✅ SEGURO

            # Obtener nombres de columnas
            columns = [col[0] for col in cursor.description] if cursor.description else []

            # Obtener resultados
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            logger.info(f"Procedimiento {proc_name} ejecutado exitosamente. {len(results)} registros obtenidos.")
            return results

    except ValueError:
        # Re-raise ValueError para que se propague
        raise
    except Exception as e:
        logger.error(f"Error ejecutando procedimiento {proc_name}: {e}")
        return []


def ejecutar_procedimiento_almacenado_alternativo(proc_name, params=None):
    """
    Alternativa usando EXEC con placeholders (si callproc no funciona en tu entorno).

    Esta es una segunda opción en caso de que callproc() tenga problemas con tu driver.

    Args:
        proc_name (str): Nombre del procedimiento almacenado
        params (list): Lista de parámetros para el procedimiento

    Returns:
        list: Lista de diccionarios con los resultados
    """
    # Validar whitelist
    if proc_name not in ALLOWED_STORED_PROCEDURES:
        error_msg = f"Procedimiento no permitido: {proc_name}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    try:
        with connection.cursor() as cursor:
            if params:
                # Crear placeholders para cada parámetro
                placeholders = ', '.join(['%s'] * len(params))
                sql = f"EXEC {proc_name} {placeholders}"  # Solo estructura, sin valores

                logger.info(f"Ejecutando: {sql} con {len(params)} parámetros")
                cursor.execute(sql, params)  # ✅ SEGURO - parámetros separados
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

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error ejecutando procedimiento {proc_name}: {e}")
        return []


def validar_nombre_servidor(servidor):
    """
    Valida que un nombre de servidor contenga solo caracteres permitidos.

    Args:
        servidor (str): Nombre del servidor a validar

    Returns:
        bool: True si es válido, False si no

    Raises:
        ValueError: Si contiene caracteres no permitidos
    """
    if not servidor:
        return True  # Vacío es válido (significa "sin filtro")

    # Solo permitir: letras, números, puntos, guiones y guiones bajos
    if not re.match(r'^[a-zA-Z0-9._-]+$', servidor):
        raise ValueError(f"Nombre de servidor inválido: {servidor}. Solo se permiten letras, números, puntos, guiones y guiones bajos.")

    # Limitar longitud
    if len(servidor) > 100:
        raise ValueError(f"Nombre de servidor demasiado largo: {len(servidor)} caracteres (máximo 100)")

    return True


def validar_nombre_base_datos(database):
    """
    Valida que un nombre de base de datos contenga solo caracteres permitidos.

    Args:
        database (str): Nombre de la base de datos a validar

    Returns:
        bool: True si es válido, False si no
    """
    if not database:
        return True

    # SQL Server permite: letras, números, _, $, #, @
    if not re.match(r'^[a-zA-Z0-9_$#@]+$', database):
        raise ValueError(f"Nombre de base de datos inválido: {database}")

    if len(database) > 128:  # Límite de SQL Server
        raise ValueError(f"Nombre de base de datos demasiado largo: {len(database)} caracteres")

    return True


def sanitizar_input_like(valor):
    """
    Sanitiza un valor para usar en cláusulas LIKE.

    Escapa los caracteres especiales de LIKE: %, _, [, ]

    Args:
        valor (str): Valor a sanitizar

    Returns:
        str: Valor sanitizado
    """
    if not valor:
        return valor

    # Escapar caracteres especiales de LIKE
    valor = valor.replace('[', '[[]')  # [ debe escaparse primero
    valor = valor.replace('%', '[%]')
    valor = valor.replace('_', '[_]')

    return valor


def construir_filtro_seguro(query_base, filtros, params):
    """
    Construye filtros SQL de forma segura.

    Args:
        query_base (str): Query base sin filtros
        filtros (dict): Diccionario con filtros {campo: valor}
        params (list): Lista donde se agregarán los parámetros

    Returns:
        str: Query con filtros agregados

    Example:
        query = "SELECT * FROM tabla WHERE 1=1"
        filtros = {'servidor': 'SRV01', 'estado': 'ONLINE'}
        params = []
        query_final = construir_filtro_seguro(query, filtros, params)
        # query_final: "SELECT * FROM tabla WHERE 1=1 AND servidor LIKE %s AND estado = %s"
        # params: ['%SRV01%', 'ONLINE']
    """
    query = query_base

    for campo, valor in filtros.items():
        if valor:  # Solo agregar filtro si hay valor
            # Validar que el campo sea seguro (whitelist)
            campos_permitidos = {
                'servidor', 'SERVIDOR', 'ServerName', 'ServerIP',
                'database', 'DatabaseName', 'DATABASE_NAME',
                'estado', 'ESTADO', 'StateDesc',
                'resultado', 'RESULTADO',
                'tipo_backup', 'TYPE'
            }

            if campo not in campos_permitidos:
                logger.warning(f"Campo no permitido en filtro: {campo}")
                continue

            # Agregar filtro con placeholder
            query += f" AND {campo} LIKE %s"

            # Sanitizar y agregar a params
            valor_sanitizado = sanitizar_input_like(valor)
            params.append(f'%{valor_sanitizado}%')

    return query


# Función wrapper para mantener compatibilidad con código existente
def ejecutar_procedimiento_almacenado(proc_name, params=None):
    """
    Wrapper que usa la versión segura por defecto.
    Mantiene compatibilidad con código existente.
    """
    return ejecutar_procedimiento_almacenado_seguro(proc_name, params)


# Re-exportar la función segura de utils.py (ya es segura)
def ejecutar_consulta_personalizada(query, params=None):
    """
    Ejecuta una consulta SQL personalizada de forma SEGURA.

    Esta función YA es segura en utils.py porque usa parámetros separados.
    Se re-exporta aquí para completitud.

    Args:
        query (str): Consulta SQL con placeholders %s
        params (list): Parámetros para la consulta

    Returns:
        list: Lista de diccionarios con los resultados
    """
    try:
        with connection.cursor() as cursor:
            logger.info(f"Ejecutando consulta personalizada")
            cursor.execute(query, params or [])  # ✅ YA ES SEGURO
            columns = [col[0] for col in cursor.description] if cursor.description else []
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            logger.info(f"Consulta ejecutada exitosamente. {len(results)} registros obtenidos.")
            return results
    except Exception as e:
        logger.error(f"Error ejecutando consulta: {e}")
        return []
