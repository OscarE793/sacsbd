# apps/reportes/data_converters.py
"""
Funciones auxiliares para convertir resultados de procedimientos almacenados
de formato tupla/lista a diccionarios con nombres de columnas.

Estas funciones centralizan la lógica de conversión que estaba duplicada
en múltiples vistas en views.py
"""


def convert_cumplimiento_result(fila):
    """
    Convierte una fila de sp_Programaciondebcks a diccionario.

    Args:
        fila: Tupla o lista con datos del SP (SERVIDOR, DatabaseName, IPSERVER, TOTAL, TOTALPROGRAM, PORCENTAJE)

    Returns:
        dict: Diccionario con los datos o None si la fila no es válida
    """
    if isinstance(fila, (list, tuple)) and len(fila) >= 6:
        return {
            'SERVIDOR': fila[0],
            'DatabaseName': fila[1],
            'IPSERVER': fila[2],
            'TOTAL': fila[3],
            'TOTALPROGRAM': fila[4],
            'PORCENTAJE': fila[5]
        }
    return None


def convert_jobs_result(fila):
    """
    Convierte una fila de sp_resultadoJobsBck a diccionario.

    Args:
        fila: Tupla o lista con datos del SP (RESULTADO, SERVIDOR, IPSERVER, FECHA, HORA, NOMBRE_DEL_JOB, PASO, MENSAJE)

    Returns:
        dict: Diccionario con los datos o None si la fila no es válida
    """
    if isinstance(fila, (list, tuple)) and len(fila) >= 8:
        return {
            'RESULTADO': fila[0] if fila[0] else '',
            'SERVIDOR': fila[1] if fila[1] else '',
            'IPSERVER': fila[2] if fila[2] else '',
            'FECHA': fila[3] if fila[3] else '',
            'HORA': fila[4] if fila[4] else '',
            'NOMBRE_DEL_JOB': fila[5] if fila[5] else '',
            'PASO': fila[6] if fila[6] else '',
            'MENSAJE': fila[7] if fila[7] else ''
        }
    return None


def normalize_results(resultados, converter_func):
    """
    Normaliza resultados de procedimientos almacenados usando una función convertidora.

    Si los resultados ya son diccionarios, los devuelve sin cambios.
    Si son tuplas/listas, los convierte usando converter_func.

    Args:
        resultados: Lista de resultados (pueden ser dicts, tuplas o listas)
        converter_func: Función para convertir cada fila (ej: convert_cumplimiento_result)

    Returns:
        list: Lista de diccionarios

    Examples:
        >>> resultados = [(srv1, db1, ip1, 10, 30, 33.33), ...]
        >>> normalized = normalize_results(resultados, convert_cumplimiento_result)
        >>> # Resultado: [{'SERVIDOR': srv1, 'DatabaseName': db1, ...}, ...]
    """
    if not resultados:
        return []

    # Si ya son diccionarios, devolverlos sin cambios
    if isinstance(resultados[0], dict):
        return resultados

    # Convertir usando la función proporcionada
    converted = []
    for fila in resultados:
        result = converter_func(fila)
        if result is not None:
            converted.append(result)

    return converted


def format_porcentaje(valor):
    """
    Formatea un valor numérico como porcentaje con 2 decimales.

    Args:
        valor: Número (int o float) o None

    Returns:
        str: Valor formateado como "XX.XX%" o "0.00%" si es None

    Examples:
        >>> format_porcentaje(33.333)
        '33.33%'
        >>> format_porcentaje(None)
        '0.00%'
    """
    if valor is None:
        return '0.00%'

    try:
        return f"{float(valor):.2f}%"
    except (ValueError, TypeError):
        return '0.00%'


def format_fecha_display(fecha_str, formato_entrada='%Y/%m/%d', formato_salida='%Y-%m-%d'):
    """
    Convierte una fecha de un formato a otro para display.

    Args:
        fecha_str: String con la fecha
        formato_entrada: Formato de entrada (default: '%Y/%m/%d')
        formato_salida: Formato de salida (default: '%Y-%m-%d')

    Returns:
        str: Fecha formateada o la fecha original si hay error

    Examples:
        >>> format_fecha_display('2024/01/15')
        '2024-01-15'
    """
    if not fecha_str:
        return ''

    try:
        from datetime import datetime
        fecha_obj = datetime.strptime(fecha_str, formato_entrada)
        return fecha_obj.strftime(formato_salida)
    except (ValueError, TypeError):
        return fecha_str


def add_cumplimiento_format(resultado):
    """
    Agrega formato de porcentaje a un resultado de cumplimiento.
    Modifica el diccionario in-place.

    Args:
        resultado: Diccionario con clave 'PORCENTAJE'

    Returns:
        dict: El mismo diccionario modificado
    """
    if 'PORCENTAJE' in resultado and resultado['PORCENTAJE'] is not None:
        if isinstance(resultado['PORCENTAJE'], (int, float)):
            resultado['PORCENTAJE'] = format_porcentaje(resultado['PORCENTAJE'])

    return resultado


def format_cumplimiento_results(resultados):
    """
    Formatea una lista de resultados de cumplimiento agregando formato de porcentaje.

    Args:
        resultados: Lista de diccionarios con resultados de cumplimiento

    Returns:
        list: Lista de diccionarios con porcentajes formateados
    """
    return [add_cumplimiento_format(r) for r in resultados]
