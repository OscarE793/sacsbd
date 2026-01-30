# apps/horas_extras/motor_normativo.py
"""
CAPA 2 y 3: Motor Normativo y Consolidador
==========================================

Funciones que aplican la norma laboral colombiana sobre los segmentos de tiempo.
Usa parámetros de ParametroNormativo para determinar clasificaciones.

Clasificaciones:
- HOD: Hora Ordinaria Diurna (base, sin recargo)
- RNO: Recargo Nocturno Ordinario (35%)
- RDF: Recargo Diurno Festivo/Dominical (75%)
- RNF: Recargo Nocturno Festivo/Dominical (110%)
"""

from decimal import Decimal
from datetime import date, time
from typing import Dict, List, Optional
import holidays

from .models_normativo import ParametroNormativo, PoliticaEmpresa
from .motor_tiempo import segmentar_tiempo, obtener_segmentos_turno


# Cache de festivos colombianos
_co_holidays = holidays.CO()


def es_festivo(fecha: date) -> bool:
    """Verifica si una fecha es festivo en Colombia."""
    return fecha in _co_holidays


def es_dominical(fecha: date) -> bool:
    """Verifica si una fecha es domingo."""
    return fecha.weekday() == 6


def clasificar_segmento(
    segmento: Dict,
    es_domingo: bool,
    es_festivo: bool,
    parametros: ParametroNormativo
) -> Dict[str, int]:
    """
    Clasifica un segmento horario según la norma vigente.
    
    Árbol de decisión:
    ┌─────────────────┐
    │ ¿Es festivo o   │
    │   domingo?      │
    └────────┬────────┘
             │
        ┌────┴────┐
        │ SÍ      │ NO
        ▼         ▼
    ┌───────┐ ┌───────┐
    │¿Noche?│ │¿Noche?│
    └───┬───┘ └───┬───┘
      │           │
    SÍ│NO      SÍ│NO
      ▼ ▼        ▼ ▼
    RNF RDF    RNO HOD
    
    Args:
        segmento: {'fecha': date, 'hora': int, 'minutos': int}
        es_domingo: bool
        es_festivo: bool
        parametros: ParametroNormativo con umbrales vigentes
        
    Returns:
        {'hod': 0, 'rno': 0, 'rdf': 0, 'rnf': minutos} (solo una key tendrá valor)
    """
    hora = segmento['hora']
    minutos = segmento['minutos']
    
    # Determinar si es nocturno según parámetros vigentes
    es_nocturno = parametros.es_hora_nocturna(hora)
    
    # Clasificar según árbol de decisión
    resultado = {'hod': 0, 'rno': 0, 'rdf': 0, 'rnf': 0}
    
    if es_festivo or es_domingo:
        if es_nocturno:
            resultado['rnf'] = minutos  # Recargo Nocturno Festivo
        else:
            resultado['rdf'] = minutos  # Recargo Diurno Festivo
    else:
        if es_nocturno:
            resultado['rno'] = minutos  # Recargo Nocturno Ordinario
        else:
            resultado['hod'] = minutos  # Hora Ordinaria Diurna
    
    return resultado


def consolidar_jornada(operador, fecha: date) -> Dict[str, Decimal]:
    """
    Proceso completo de clasificación para un día de trabajo.
    
    1. Obtiene parámetros normativos vigentes para la fecha
    2. Segmenta el tiempo del turno
    3. Clasifica cada segmento
    4. Aplica políticas de empresa
    5. Consolida totales
    
    Args:
        operador: User instance
        fecha: date a calcular
        
    Returns:
        {
            'hod': Decimal('6.50'),  # Horas ordinarias diurnas
            'rno': Decimal('1.50'),  # Horas con recargo nocturno
            'rdf': Decimal('0.00'),  # Horas con recargo dominical/festivo
            'rnf': Decimal('0.00'),  # Horas con recargo nocturno festivo
            'total': Decimal('8.00')
        }
    """
    from .models import RegistroTurno
    
    # 1. Obtener parámetros vigentes
    parametros = ParametroNormativo.obtener_vigente(fecha)
    if not parametros:
        # Fallback: usar defaults si no hay parámetros configurados
        parametros = ParametroNormativo()
    
    # 2. Buscar turno del operador para esa fecha
    try:
        turno = RegistroTurno.objects.get(operador=operador, fecha=fecha)
    except RegistroTurno.DoesNotExist:
        return {'hod': Decimal('0'), 'rno': Decimal('0'), 
                'rdf': Decimal('0'), 'rnf': Decimal('0'), 'total': Decimal('0')}
    
    # 3. Obtener segmentos de tiempo
    segmentos = obtener_segmentos_turno(turno)
    
    # 4. Clasificar cada segmento
    totales_minutos = {'hod': 0, 'rno': 0, 'rdf': 0, 'rnf': 0}
    
    for seg in segmentos:
        # Para cada segmento, determinar si su fecha específica es festivo/domingo
        # (importante para turnos que cruzan medianoche)
        seg_fecha = seg['fecha']
        seg_es_domingo = es_dominical(seg_fecha)
        seg_es_festivo = es_festivo(seg_fecha)
        
        clasificacion = clasificar_segmento(
            seg,
            es_domingo=seg_es_domingo,
            es_festivo=seg_es_festivo,
            parametros=parametros
        )
        
        for key, value in clasificacion.items():
            totales_minutos[key] += value
    
    # 5. Aplicar políticas de empresa (CAPA 3)
    politica = PoliticaEmpresa.obtener_vigente(fecha)
    if politica:
        # Redondeo de minutos
        if politica.redondear_minutos > 0:
            for key in totales_minutos:
                resto = totales_minutos[key] % politica.redondear_minutos
                if resto > 0:
                    totales_minutos[key] += (politica.redondear_minutos - resto)
        
        # Sábado como descanso
        if politica.sabado_es_descanso and fecha.weekday() == 5:
            # Mover horas de HOD/RNO a RDF/RNF
            totales_minutos['rdf'] += totales_minutos['hod']
            totales_minutos['rnf'] += totales_minutos['rno']
            totales_minutos['hod'] = 0
            totales_minutos['rno'] = 0
    
    # 6. Convertir a horas (Decimal)
    resultado = {}
    for key, minutos in totales_minutos.items():
        resultado[key] = Decimal(str(minutos / 60)).quantize(Decimal('0.01'))
    
    resultado['total'] = sum(resultado.values())
    
    return resultado


def consolidar_mes(operador, ano: int, mes: int) -> Dict:
    """
    Consolida todos los días de un mes para un operador.
    
    Args:
        operador: User instance
        ano: Año
        mes: Mes (1-12)
        
    Returns:
        {
            'dias': [
                {'fecha': date, 'hod': Decimal, 'rno': Decimal, ...},
                ...
            ],
            'totales': {'hod': Decimal, 'rno': Decimal, 'rdf': Decimal, 'rnf': Decimal, 'total': Decimal}
        }
    """
    import calendar
    from datetime import date as date_class
    
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    
    dias = []
    totales = {'hod': Decimal('0'), 'rno': Decimal('0'), 
               'rdf': Decimal('0'), 'rnf': Decimal('0'), 'total': Decimal('0')}
    
    for dia in range(1, ultimo_dia + 1):
        fecha = date_class(ano, mes, dia)
        resultado_dia = consolidar_jornada(operador, fecha)
        
        dias.append({
            'fecha': fecha,
            **resultado_dia
        })
        
        for key in totales:
            totales[key] += resultado_dia.get(key, Decimal('0'))
    
    return {
        'dias': dias,
        'totales': totales
    }


def obtener_parametros_para_reporte(fecha: date) -> Dict:
    """
    Obtiene los parámetros normativos formateados para mostrar en reportes.
    
    Útil para mostrar al usuario qué norma se está aplicando.
    
    Returns:
        {
            'vigencia_desde': date,
            'hora_inicio_nocturno': '21:00',
            'recargo_nocturno': '35%',
            'recargo_dominical': '75%',
            'jornada_semanal': 44,
            'descripcion': 'Ley 2101...'
        }
    """
    parametros = ParametroNormativo.obtener_vigente(fecha)
    
    if not parametros:
        return {
            'vigencia_desde': None,
            'hora_inicio_nocturno': '21:00',
            'recargo_nocturno': '35%',
            'recargo_dominical': '75%',
            'jornada_semanal': 46,
            'descripcion': 'Parámetros por defecto (sin configurar)'
        }
    
    return {
        'vigencia_desde': parametros.vigencia_desde,
        'hora_inicio_nocturno': parametros.hora_inicio_nocturno.strftime('%H:%M'),
        'recargo_nocturno': f"{int(parametros.recargo_nocturno * 100)}%",
        'recargo_dominical': f"{int(parametros.recargo_dominical_festivo * 100)}%",
        'jornada_semanal': parametros.jornada_semanal_max,
        'descripcion': parametros.descripcion
    }
