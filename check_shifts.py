# -*- coding: utf-8 -*-
"""
Check specific shift records to debug the issue.
Usage: python manage.py shell < check_shifts.py
"""

from datetime import date
from django.contrib.auth.models import User
from apps.horas_extras.models import RegistroTurno

operador = User.objects.filter(first_name__icontains="Oscar").first()

if not operador:
    print("Operador no encontrado")
else:
    print("Verificando turnos clave:")
    print("-" * 80)
    
    fechas_clave = [
        date(2025, 12, 1),
        date(2025, 12, 2),
        date(2025, 12, 3),
        date(2025, 12, 31),
        date(2026, 1, 1),
        date(2026, 1, 2),
    ]
    
    for fecha in fechas_clave:
        turno = RegistroTurno.objects.filter(
            operador=operador,
            fecha=fecha
        ).first()
        
        if turno:
            tipo = turno.tipo_turno.codigo
            inicio = turno.hora_inicio_real.strftime('%H:%M') if turno.hora_inicio_real else 'None'
            fin = turno.hora_fin_real.strftime('%H:%M') if turno.hora_fin_real else 'None'
            horas = turno.horas_trabajadas
            dia = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom'][fecha.weekday()]
            
            print("%s (%s) | Tipo: %s | %s-%s | Horas: %s" % (
                fecha, dia, tipo, inicio, fin, horas
            ))
        else:
            print("%s | NO EXISTE" % fecha)
    
    print("-" * 80)
