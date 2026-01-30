# -*- coding: utf-8 -*-
"""
Django management command to regenerate shifts for a specific operator.
Usage: python manage.py regenerar_turnos --operador oscar --desde 2025-12-01 --hasta 2026-02-28
"""

from datetime import date, time
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.horas_extras.models import RegistroTurno, TipoTurno
from apps.horas_extras.utils import GeneradorTurnos


class Command(BaseCommand):
    help = 'Regenera turnos para un operador especifico en un rango de fechas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--operador',
            type=str,
            default='oscar',
            help='Nombre parcial del operador (ej: oscar)'
        )
        parser.add_argument(
            '--desde',
            type=str,
            default='2025-12-01',
            help='Fecha inicio (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--hasta',
            type=str,
            default='2026-02-28',
            help='Fecha fin (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--turno-dic',
            type=str,
            default='T',
            help='Turno inicial para diciembre (T/N/D/M) - Dec 1 empieza con T'
        )
        parser.add_argument(
            '--turno-ene',
            type=str,
            default='N',
            help='Turno inicial para enero (T/N/D/M) - Dec 31 empieza ciclo N'
        )
        parser.add_argument(
            '--turno-feb',
            type=str,
            default='T',
            help='Turno inicial para febrero (T/N/D/M)'
        )
        parser.add_argument(
            '--es-inicio-dic',
            action='store_true',
            default=False,
            help='Si el turno de dic es N, indica que es inicio del ciclo N'
        )
        parser.add_argument(
            '--es-inicio-ene',
            action='store_true',
            default=True,
            help='Si el turno de ene es N, indica que es inicio del ciclo N'
        )


    def handle(self, *args, **options):
        operador_query = options['operador']
        fecha_desde = date.fromisoformat(options['desde'])
        fecha_hasta = date.fromisoformat(options['hasta'])
        
        self.stdout.write("=" * 60)
        self.stdout.write("REGENERACION DE TURNOS - CONTROLADO")
        self.stdout.write("=" * 60)
        
        # Buscar operador
        operador = User.objects.filter(
            first_name__icontains=operador_query
        ).first()
        
        if not operador:
            operador = User.objects.filter(
                username__icontains=operador_query
            ).first()
        
        if not operador:
            self.stdout.write(self.style.ERROR("No se encontro el operador"))
            self.stdout.write("Usuarios disponibles:")
            for u in User.objects.filter(is_active=True)[:10]:
                self.stdout.write("  ID: %s, Username: %s, Nombre: %s" % (u.id, u.username, u.get_full_name()))
            return
        
        self.stdout.write("")
        self.stdout.write("Operador encontrado:")
        self.stdout.write("  ID: %s" % operador.id)
        self.stdout.write("  Username: %s" % operador.username)
        self.stdout.write("  Nombre: %s" % operador.get_full_name())
        self.stdout.write("")
        self.stdout.write("Rango de fechas: %s a %s" % (fecha_desde, fecha_hasta))
        
        # Contar y eliminar turnos existentes
        turnos_existentes = RegistroTurno.objects.filter(
            operador=operador,
            fecha__range=(fecha_desde, fecha_hasta)
        )
        count_antes = turnos_existentes.count()
        self.stdout.write("")
        self.stdout.write("Turnos existentes en el rango: %s" % count_antes)
        
        self.stdout.write("")
        self.stdout.write("[PASO 1] Eliminando turnos existentes...")
        turnos_existentes.delete()
        self.stdout.write(self.style.SUCCESS("  [OK] %s turnos eliminados" % count_antes))
        
        # Regenerar turnos mes por mes
        self.stdout.write("")
        self.stdout.write("[PASO 2] Regenerando turnos con nueva logica...")
        
        meses_config = [
            # (año, mes, turno_inicial, es_inicio_ciclo_n)
            # Dec 1 starts with T (mid-cycle), T rotates to N on Dec 3
            (2025, 12, options['turno_dic'], options.get('es_inicio_dic', False)),
            # Jan continues from Dec 31 N cycle (NOT a new cycle start)
            (2026, 1, options['turno_ene'], False),  # N continues from Dec
            # Feb continues from rotation
            (2026, 2, options['turno_feb'], None),
        ]
        
        total_generados = 0
        
        for ano, mes, turno_inicial, es_inicio in meses_config:
            if date(ano, mes, 1) < fecha_desde or date(ano, mes, 1) > fecha_hasta:
                continue
                
            turnos = GeneradorTurnos.generar_turnos_mes(
                operador, ano, mes, 
                turno_inicial=turno_inicial,
                es_inicio_ciclo_n=es_inicio
            )
            GeneradorTurnos.guardar_turnos_mes(turnos)
            self.stdout.write(self.style.SUCCESS(
                "  [OK] %02d/%s: %s turnos generados (inicial: %s, es_inicio_n: %s)" % (
                    mes, ano, len(turnos), turno_inicial, es_inicio
                )
            ))
            total_generados += len(turnos)

        
        # Verificacion de turnos nocturnos
        self.stdout.write("")
        self.stdout.write("[PASO 3] Verificacion de turnos nocturnos...")
        
        turnos_noche = RegistroTurno.objects.filter(
            operador=operador,
            fecha__range=(fecha_desde, fecha_hasta),
            tipo_turno__codigo='N'
        ).order_by('fecha')
        
        self.stdout.write("")
        self.stdout.write("Turnos nocturnos generados: %s" % turnos_noche.count())
        self.stdout.write("")
        self.stdout.write("Detalle de turnos nocturnos:")
        self.stdout.write("-" * 90)
        self.stdout.write("%-12s %-12s %-8s %-8s %-8s %s" % ("Fecha", "Dia", "Inicio", "Fin", "Horas", "Tipo"))
        self.stdout.write("-" * 90)
        
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
            
            self.stdout.write("%-12s %-12s %-8s %-8s %-8s %s" % (
                turno.fecha, dia_nombre, inicio, fin, turno.horas_trabajadas, tipo_dias
            ))
        
        self.stdout.write("-" * 90)
        
        # Verificar dias de descanso
        turnos_descanso = RegistroTurno.objects.filter(
            operador=operador,
            fecha__range=(fecha_desde, fecha_hasta),
            tipo_turno__codigo='D'
        ).order_by('fecha')[:10]
        
        self.stdout.write("")
        self.stdout.write("Dias de descanso (primeros 10):")
        self.stdout.write("-" * 50)
        for turno in turnos_descanso:
            dia_nombre = dias_semana[turno.fecha.weekday()]
            self.stdout.write("%-12s %-12s Horas: %s" % (turno.fecha, dia_nombre, turno.horas_trabajadas))
        
        self.stdout.write("-" * 50)
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("[OK] Regeneracion completada exitosamente"))
        self.stdout.write("   Total turnos generados: %s" % total_generados)
        self.stdout.write("")
        self.stdout.write("Checklist de validacion:")
        self.stdout.write("   1. Primer miercoles N -> 23:00-23:59 (1h)")
        self.stdout.write("   2. Ultimo miercoles N -> 00:00-06:00 (6h)")
        self.stdout.write("   3. Dias intermedios N -> 23:00-06:00 (7h)")
        self.stdout.write("   4. Dias D (descanso) -> 0h")
        self.stdout.write("   5. Generar reporte y verificar totales")
