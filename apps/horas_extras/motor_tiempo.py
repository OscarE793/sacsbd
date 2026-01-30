# apps/horas_extras/motor_tiempo.py
"""
CAPA 1: Motor de Tiempo (Neutro)
================================

Funciones para dividir rangos horarios en segmentos.
NO conoce nada de leyes - solo matemáticas de tiempo.

Uso:
    segmentos = segmentar_tiempo(fecha, time(22, 0), time(6, 0))
    # Retorna lista de segmentos por hora
"""

import datetime
from datetime import time, timedelta
from decimal import Decimal
from typing import List, Dict, Optional


def segmentar_tiempo(fecha: datetime.date, hora_inicio: time, hora_fin: time) -> List[Dict]:
    """
    Divide un rango horario en segmentos por hora.
    
    Maneja turnos que cruzan medianoche automáticamente.
    NO sabe nada de leyes - es una función puramente matemática.
    
    Args:
        fecha: Fecha de inicio del turno
        hora_inicio: Hora de inicio (time)
        hora_fin: Hora de fin (time)
        
    Returns:
        Lista de diccionarios con:
        - fecha: date del segmento
        - hora: int (0-23)
        - minutos: int (minutos trabajados en esa hora)
        
    Ejemplo:
        segmentar_tiempo(date(2026, 1, 23), time(22, 30), time(6, 0))
        Returns:
        [
            {'fecha': date(2026, 1, 23), 'hora': 22, 'minutos': 30},
            {'fecha': date(2026, 1, 23), 'hora': 23, 'minutos': 60},
            {'fecha': date(2026, 1, 24), 'hora': 0, 'minutos': 60},
            {'fecha': date(2026, 1, 24), 'hora': 1, 'minutos': 60},
            ...
            {'fecha': date(2026, 1, 24), 'hora': 5, 'minutos': 60},
        ]
    """
    if not hora_inicio or not hora_fin:
        return []
    
    segmentos = []
    
    # Crear datetime completos para facilitar cálculos
    inicio_dt = datetime.datetime.combine(fecha, hora_inicio)
    fin_dt = datetime.datetime.combine(fecha, hora_fin)
    
    # Si hora_fin < hora_inicio, el turno cruza medianoche
    if hora_fin <= hora_inicio:
        fin_dt += timedelta(days=1)
    
    # Iterar hora por hora
    cursor = inicio_dt
    while cursor < fin_dt:
        # Calcular minutos trabajados en esta hora
        inicio_hora = cursor
        fin_hora = cursor.replace(minute=0, second=0) + timedelta(hours=1)
        
        # Si estamos en la primera hora, empezamos desde el minuto real
        if cursor.minute > 0:
            fin_hora = cursor.replace(minute=0, second=0) + timedelta(hours=1)
        
        # No exceder el fin del turno
        if fin_hora > fin_dt:
            fin_hora = fin_dt
        
        minutos_en_hora = int((fin_hora - cursor).total_seconds() / 60)
        
        if minutos_en_hora > 0:
            segmentos.append({
                'fecha': cursor.date(),
                'hora': cursor.hour,
                'minutos': minutos_en_hora
            })
        
        # Avanzar a la siguiente hora completa
        cursor = cursor.replace(minute=0, second=0) + timedelta(hours=1)
    
    return segmentos


def obtener_segmentos_turno(turno) -> List[Dict]:
    """
    Obtiene los segmentos de tiempo para un RegistroTurno.
    
    Usa hora_inicio_real y hora_fin_real si están definidas,
    de lo contrario usa los horarios del TipoTurno para ese día.
    
    Args:
        turno: RegistroTurno instance
        
    Returns:
        Lista de segmentos (ver segmentar_tiempo)
    """
    fecha = turno.fecha
    
    # Priorizar horarios reales sobre programados
    if turno.hora_inicio_real and turno.hora_fin_real:
        hora_inicio = turno.hora_inicio_real
        hora_fin = turno.hora_fin_real
    elif turno.tipo_turno:
        hora_inicio, hora_fin, _ = turno.tipo_turno.get_horario_por_dia(fecha)
    else:
        return []
    
    if not hora_inicio or not hora_fin:
        return []
    
    return segmentar_tiempo(fecha, hora_inicio, hora_fin)


def calcular_horas_totales(segmentos: List[Dict]) -> Decimal:
    """
    Suma todos los minutos de los segmentos y convierte a horas.
    
    Args:
        segmentos: Lista de segmentos
        
    Returns:
        Decimal con horas totales (ej: 7.50)
    """
    total_minutos = sum(seg['minutos'] for seg in segmentos)
    return Decimal(str(total_minutos / 60)).quantize(Decimal('0.01'))


def agrupar_segmentos_por_fecha(segmentos: List[Dict]) -> Dict[datetime.date, List[Dict]]:
    """
    Agrupa segmentos por fecha (útil para turnos que cruzan medianoche).
    
    Args:
        segmentos: Lista de segmentos
        
    Returns:
        Dict con fecha como key y lista de segmentos como value
    """
    agrupados = {}
    for seg in segmentos:
        fecha = seg['fecha']
        if fecha not in agrupados:
            agrupados[fecha] = []
        agrupados[fecha].append(seg)
    return agrupados
