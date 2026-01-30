# -*- coding: utf-8 -*-
"""
Django management command to regenerate shifts using V4 logic.
V4: Real hour ranges per turno + day of week, RNO from 19:00.

Usage: 
    python manage.py regenerar_turnos_v4 --operador oscar
    python manage.py regenerar_turnos_v4 --todos
"""

from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.horas_extras.models import RegistroTurno, TipoTurno, PatronOperador
from apps.horas_extras.utils import GeneradorTurnosV4


class Command(BaseCommand):
    help = 'Regenera turnos con lógica V4 (rangos horarios reales + recargos legales)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--todos',
            action='store_true',
            help='Regenerar turnos para TODOS los operadores con PatronOperador'
        )
        parser.add_argument(
            '--operador',
            type=str,
            default=None,
            help='Nombre parcial del operador (ignorado si se usa --todos)'
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

    def handle(self, *args, **options):
        todos = options['todos']
        operador_query = options['operador']
        fecha_desde = date.fromisoformat(options['desde'])
        fecha_hasta = date.fromisoformat(options['hasta'])
        
        self.stdout.write("=" * 70)
        self.stdout.write("REGENERACIÓN DE TURNOS V4")
        self.stdout.write("=" * 70)
        self.stdout.write("")
        self.stdout.write("CARACTERÍSTICAS V4:")
        self.stdout.write("  - Rangos horarios REALES por turno + día")
        self.stdout.write("  - RNO inicia a las 19:00")
        self.stdout.write("  - Turno N: segmentos separados (madrugada + noche)")
        self.stdout.write("  - Turno A: excluye sábados, domingos y festivos")
        self.stdout.write("=" * 70)
        
        # Obtener lista de operadores
        if todos:
            operador_ids = PatronOperador.objects.values_list('operador_id', flat=True).distinct()
            operadores = list(User.objects.filter(id__in=operador_ids))
            self.stdout.write("")
            self.stdout.write(self.style.WARNING(
                "Modo: TODOS (%s operadores con patrón configurado)" % len(operadores)
            ))
            
            if not operadores:
                self.stdout.write(self.style.ERROR(
                    "\nNo hay operadores con PatronOperador configurado."
                ))
                self.stdout.write("Use: python manage.py set_patron_operador --operador X --fecha Y --turno Z")
                return
                
        elif operador_query:
            operador = User.objects.filter(
                first_name__icontains=operador_query
            ).first()
            
            if not operador:
                operador = User.objects.filter(
                    username__icontains=operador_query
                ).first()
            
            if not operador:
                self.stdout.write(self.style.ERROR("No se encontró el operador"))
                for u in User.objects.filter(is_active=True)[:10]:
                    self.stdout.write("  %s - %s" % (u.username, u.get_full_name()))
                return
            
            if not PatronOperador.objects.filter(operador=operador).exists():
                self.stdout.write(self.style.ERROR(
                    "\nEl operador %s no tiene PatronOperador configurado." % operador.get_full_name()
                ))
                self.stdout.write("Use: python manage.py set_patron_operador --operador %s --fecha Y --turno Z" % operador_query)
                return
            
            operadores = [operador]
            self.stdout.write("")
            self.stdout.write("Modo: OPERADOR INDIVIDUAL")
        else:
            self.stdout.write(self.style.ERROR("Debe especificar --todos o --operador"))
            return
        
        self.stdout.write("Rango: %s a %s" % (fecha_desde, fecha_hasta))
        
        # Procesar cada operador
        total_turnos = 0
        operadores_procesados = 0
        
        for operador in operadores:
            seeds = PatronOperador.objects.filter(operador=operador).order_by('fecha_inicio_patron')
            self.stdout.write("")
            self.stdout.write("Procesando: %s" % operador.get_full_name())
            self.stdout.write("  Seeds configurados: %s" % seeds.count())
            for s in seeds:
                motivo_str = " (%s)" % s.motivo if s.motivo else ""
                self.stdout.write("    - %s desde %s%s" % (s.turno_inicial_patron, s.fecha_inicio_patron, motivo_str))

            
            # Eliminar turnos existentes
            turnos_existentes = RegistroTurno.objects.filter(
                operador=operador,
                fecha__range=(fecha_desde, fecha_hasta)
            )
            count_antes = turnos_existentes.count()
            turnos_existentes.delete()
            
            # Generar turnos con lógica V4
            try:
                turnos = GeneradorTurnosV4.generar_turnos_operador_v4(
                    operador=operador,
                    fecha_inicio=fecha_desde,
                    fecha_fin=fecha_hasta
                )
                
                # Guardar
                GeneradorTurnosV4.guardar_turnos(turnos)
                total_turnos += len(turnos)
                operadores_procesados += 1
                
                self.stdout.write(self.style.SUCCESS(
                    "  [OK] %s turnos generados (antes: %s)" % (len(turnos), count_antes)
                ))
            except ValueError as e:
                self.stdout.write(self.style.ERROR("  [ERROR] %s" % str(e)))
        
        self.stdout.write("")
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS(
            "TOTAL: %s operadores, %s turnos generados" % (operadores_procesados, total_turnos)
        ))
        
        # Verificación
        if operadores_procesados > 0:
            self._verificar_operador(operadores[0], fecha_desde, fecha_hasta)
        
        self.stdout.write("")
        self.stdout.write("=" * 70)
        self.stdout.write("Regeneración completada")
        self.stdout.write("=" * 70)

    def _verificar_operador(self, operador, fecha_desde, fecha_hasta):
        """Verificación de muestra para un operador"""
        self.stdout.write("")
        self.stdout.write("[VERIFICACIÓN V4] Muestra para: %s" % operador.get_full_name())
        self.stdout.write("-" * 70)
        
        # Fechas de prueba con valores esperados V4
        fechas_test = [
            (date(2025, 12, 3), 'N', 1, "Primer Mié N (23:00-00:00)"),
            (date(2025, 12, 4), 'N', 7, "Jue N (00:00-06:00 + 23:00-00:00)"),
            (date(2025, 12, 6), 'N', 8, "Sáb N (00:00-06:00 + 22:00-00:00)"),
            (date(2025, 12, 10), 'N', 6, "Último Mié N (00:00-06:00)"),
            (date(2025, 12, 11), 'D', 0, "Jue D (descanso)"),
            (date(2025, 12, 16), 'D', 0, "Mar D (último día descanso)"),
            (date(2025, 12, 17), 'M', 7, "Mié M (07:00-14:00)"),
            (date(2025, 12, 20), 'M', 8, "Sáb M (06:00-14:00)"),
        ]
        
        dias_semana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        errores = 0
        
        for fecha, turno_esperado, horas_esperadas, descripcion in fechas_test:
            if fecha < fecha_desde or fecha > fecha_hasta:
                continue
                
            turno = RegistroTurno.objects.filter(
                operador=operador,
                fecha=fecha
            ).first()
            
            if turno:
                actual = int(turno.horas_trabajadas)
                ok = "✓" if actual == horas_esperadas else "✗"
                linea = "%s %s (%s) | %s | Esperado: %sh | Actual: %sh | %s" % (
                    ok, fecha, dias_semana[fecha.weekday()], 
                    turno.tipo_turno.codigo, horas_esperadas, actual, descripcion
                )
                if actual != horas_esperadas:
                    errores += 1
                    self.stdout.write(self.style.ERROR(linea))
                else:
                    self.stdout.write(self.style.SUCCESS(linea))
            else:
                errores += 1
                self.stdout.write(self.style.ERROR(
                    "✗ %s | NO EXISTE | Esperado: %sh" % (fecha, horas_esperadas)
                ))
        
        self.stdout.write("-" * 70)
        
        if errores == 0:
            self.stdout.write(self.style.SUCCESS("✓ TODAS LAS VERIFICACIONES PASARON"))
        else:
            self.stdout.write(self.style.ERROR("✗ %s ERRORES ENCONTRADOS" % errores))
