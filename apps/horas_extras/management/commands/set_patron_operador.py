# -*- coding: utf-8 -*-
"""
Django management command to set/add a shift pattern seed for an operator.
Supports MULTIPLE seeds per operator (for vacations, relocations, etc.)

Usage: 
    python manage.py set_patron_operador --operador oscar --fecha 2025-11-26 --turno T
    python manage.py set_patron_operador --operador oscar --fecha 2026-02-15 --turno M --motivo "Regreso vacaciones"
"""

from datetime import date
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.horas_extras.models import PatronOperador


class Command(BaseCommand):
    help = 'Configura/añade un seed del patrón de turnos para un operador (soporta múltiples)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--operador',
            type=str,
            required=True,
            help='Nombre parcial o username del operador'
        )
        parser.add_argument(
            '--fecha',
            type=str,
            required=True,
            help='Fecha donde comienza este patrón (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--turno',
            type=str,
            required=True,
            choices=['T', 'N', 'D', 'M', 'A'],
            help='Turno que el operador tiene en esa fecha (T/N/D/M/A)'
        )
        parser.add_argument(
            '--motivo',
            type=str,
            default='',
            help='Motivo del cambio (vacaciones, reubicación, etc.)'
        )

    def handle(self, *args, **options):
        operador_query = options['operador']
        fecha_patron = date.fromisoformat(options['fecha'])
        turno_patron = options['turno'].upper()
        motivo = options['motivo']
        
        self.stdout.write("=" * 60)
        self.stdout.write("SET PATRÓN OPERADOR (Multi-seed)")
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
            self.stdout.write(self.style.ERROR("No se encontró el operador"))
            self.stdout.write("Operadores disponibles:")
            for u in User.objects.filter(is_active=True)[:15]:
                self.stdout.write("  %s - %s" % (u.username, u.get_full_name()))
            return
        
        self.stdout.write("Operador: %s (ID: %s)" % (operador.get_full_name(), operador.id))
        self.stdout.write("Fecha inicio: %s" % fecha_patron)
        self.stdout.write("Turno: %s" % turno_patron)
        if motivo:
            self.stdout.write("Motivo: %s" % motivo)
        
        # Crear o actualizar seed para esta fecha específica
        patron, created = PatronOperador.objects.update_or_create(
            operador=operador,
            fecha_inicio_patron=fecha_patron,
            defaults={
                'turno_inicial_patron': turno_patron,
                'motivo': motivo
            }
        )

        
        if created:
            self.stdout.write(self.style.SUCCESS("\n✓ Patrón CREADO exitosamente"))
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ Patrón ACTUALIZADO exitosamente"))
        
        # Mostrar ejemplo de cálculo
        self.stdout.write("\n" + "-" * 60)
        self.stdout.write("EJEMPLO DE CÁLCULO (próximos 14 días desde la fecha ancla):")
        self.stdout.write("-" * 60)
        
        dias_semana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        
        from datetime import timedelta
        for i in range(14):
            fecha = fecha_patron + timedelta(days=i)
            turno = patron.calcular_turno_fecha(fecha)
            dia = dias_semana[fecha.weekday()]
            self.stdout.write("  %s (%s) -> %s" % (fecha, dia, turno))
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Ahora puede regenerar turnos con:")
        self.stdout.write("  python manage.py regenerar_turnos_v3 --operador %s" % operador_query)
        self.stdout.write("=" * 60)
