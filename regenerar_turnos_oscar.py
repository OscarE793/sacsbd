# -*- coding: utf-8 -*-
"""
Script para regenerar turnos de un operador especifico.
Uso: python manage.py shell < regenerar_turnos_oscar.py
"""

from datetime import date, time
from decimal import Decimal
from django.contrib.auth.models import User
from apps.horas_extras.models import RegistroTurno, TipoTurno
from apps.horas_extras.utils import GeneradorTurnos

# Configuracion
FECHA_INICIO = date(2025, 12, 1)
FECHA_FIN = date(2026, 2, 28)

def buscar_operador():
    operador = User.objects.filter(
        first_name__icontains="Oscar",
        last_name__icontains="Jaramillo"
    ).first()
    
    if not operador:
        operador = User.objects.filter(username__icontains="oscar").first()
    
    if not operador:
        print("No se encontro el operador. Usuarios disponibles:")
        for u in User.objects.filter(is_active=True)[:10]:
            print("  ID: %s, Username: %s, Nombre: %s" % (u.id, u.username, u.get_full_name()))
        return None
    
    return operador

def regenerar_turnos():
    print("=" * 60)
    print("REGENERACION DE TURNOS - CONTROLADO")
    print("=" * 60)
    
    operador = buscar_operador()
    if not operador:
        print("ERROR: Operador no encontrado. Abortando.")
        return
    
    print("")
    print("Operador encontrado:")
    print("  ID: %s" % operador.id)
    print("  Username: %s" % operador.username)
    print("  Nombre: %s" % operador.get_full_name())
    print("")
    print("Rango de fechas: %s a %s" % (FECHA_INICIO, FECHA_FIN))
    
    turnos_existentes = RegistroTurno.objects.filter(
        operador=operador,
        fecha__range=(FECHA_INICIO, FECHA_FIN)
    )
    count_antes = turnos_existentes.count()
    print("")
    print("Turnos existentes en el rango: %s" % count_antes)
    
    print("")
    print("[PASO 1] Eliminando turnos existentes...")
    turnos_existentes.delete()
    print("  [OK] %s turnos eliminados" % count_antes)
    
    print("")
    print("[PASO 2] Regenerando turnos con nueva logica...")
    
    meses_config = [
        (2025, 12, 'Turno 3-N', True),
        (2026, 1, 'Apoyo-A', None),
        (2026, 2, 'Turno 1-M', None),
    ]
    
    total_generados = 0
    
    for ano, mes, turno_inicial, es_inicio in meses_config:
        turnos = GeneradorTurnos.generar_turnos_mes(
            operador, ano, mes, 
            turno_inicial=turno_inicial,
            es_inicio_ciclo_n=es_inicio
        )
        GeneradorTurnos.guardar_turnos_mes(turnos)
        print("  [OK] %02d/%s: %s turnos generados (inicial: %s)" % (mes, ano, len(turnos), turno_inicial))
        total_generados += len(turnos)
    
    print("")
    print("[PASO 3] Verificacion de turnos nocturnos...")
    
    turnos_noche = RegistroTurno.objects.filter(
        operador=operador,
        fecha__range=(FECHA_INICIO, FECHA_FIN),
        tipo_turno__codigo='Turno 3-N'
    ).order_by('fecha')
    
    print("")
    print("Turnos nocturnos generados: %s" % turnos_noche.count())
    print("")
    print("Detalle de turnos nocturnos:")
    print("-" * 90)
    print("%-12s %-12s %-8s %-8s %-8s %s" % ("Fecha", "Dia", "Inicio", "Fin", "Horas", "Tipo"))
    print("-" * 90)
    
    dias_semana = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
    
    for turno in turnos_noche:
        dia_nombre = dias_semana[turno.fecha.weekday()]
        inicio = turno.hora_inicio_real.strftime('%H:%M') if turno.hora_inicio_real else '-'
        fin = turno.hora_fin_real.strftime('%H:%M') if turno.hora_fin_real else '-'
        
        if turno.hora_inicio_real == time(23, 0) and turno.hora_fin_real == time(23, 59):
            tipo_dias = "<-- PRIMER MIE (1h)"
        elif turno.hora_inicio_real == time(0, 0) and turno.hora_fin_real == time(6, 0):
            tipo_dias = "<-- ULTIMO MIE (6h)"
        else:
            tipo_dias = "    Intermedio (7h)"
        
        print("%-12s %-12s %-8s %-8s %-8s %s" % (turno.fecha, dia_nombre, inicio, fin, turno.horas_trabajadas, tipo_dias))
    
    print("-" * 90)
    
    turnos_descanso = RegistroTurno.objects.filter(
        operador=operador,
        fecha__range=(FECHA_INICIO, FECHA_FIN),
        tipo_turno__codigo='Des o Permi-D'
    ).order_by('fecha')[:10]
    
    print("")
    print("Dias de descanso (primeros 10):")
    print("-" * 50)
    for turno in turnos_descanso:
        dia_nombre = dias_semana[turno.fecha.weekday()]
        print("%-12s %-12s Horas: %s" % (turno.fecha, dia_nombre, turno.horas_trabajadas))
    
    print("-" * 50)
    print("")
    print("[OK] Regeneracion completada exitosamente")
    print("   Total turnos generados: %s" % total_generados)
    print("")
    print("Checklist de validacion:")
    print("   1. Primer miercoles N -> 23:00-23:59 (1h)")
    print("   2. Ultimo miercoles N -> 00:00-06:00 (6h)")
    print("   3. Dias intermedios N -> 23:00-06:00 (7h)")
    print("   4. Dias D (descanso) -> 0h")
    print("   5. Generar reporte y verificar totales")

if __name__ == "__main__":
    regenerar_turnos()
else:
    regenerar_turnos()
