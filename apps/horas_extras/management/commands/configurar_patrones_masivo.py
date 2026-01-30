# apps/horas_extras/management/commands/configurar_patrones_masivo.py
"""
Configura PatronOperador para todos los operadores que no lo tienen.

Uso:
    python manage.py configurar_patrones_masivo --fecha 2025-11-26 --turno T
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from datetime import date

from apps.user_management.models import Role, UserRole
from apps.horas_extras.models import PatronOperador


class Command(BaseCommand):
    help = 'Configura PatronOperador para todos los operadores sin patrón'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fecha',
            type=str,
            required=True,
            help='Fecha de inicio del patrón (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--turno',
            type=str,
            required=True,
            choices=['T', 'N', 'D', 'M', 'A'],
            help='Turno inicial (T, N, D, M, A)'
        )
        parser.add_argument(
            '--motivo',
            type=str,
            default='Configuración inicial del sistema',
            help='Motivo del patrón'
        )

    def handle(self, *args, **options):
        fecha_str = options['fecha']
        turno = options['turno']
        motivo = options['motivo']
        
        fecha_inicio = date.fromisoformat(fecha_str)
        
        self.stdout.write("=" * 70)
        self.stdout.write("CONFIGURACIÓN MASIVA DE PATRONES")
        self.stdout.write("=" * 70)
        
        # Obtener operadores activos
        try:
            rol = Role.objects.get(name='operador de centro de computo')
            operadores = User.objects.filter(
                is_active=True,
                userrole__role=rol,
                userrole__activo=True
            ).distinct().order_by('last_name', 'first_name')
        except Role.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'El rol "operador de centro de computo" no existe'
            ))
            return
        
        self.stdout.write(f"\nOperadores encontrados: {operadores.count()}")
        self.stdout.write(f"Fecha inicio: {fecha_inicio}")
        self.stdout.write(f"Turno inicial: {turno}")
        self.stdout.write(f"Motivo: {motivo}\n")
        
        configurados = 0
        ya_existian = 0
        
        for operador in operadores:
            # Verificar si ya tiene patrón para esta fecha
            patron_existente = PatronOperador.objects.filter(
                operador=operador,
                fecha_inicio_patron=fecha_inicio
            ).exists()
            
            if patron_existente:
                self.stdout.write(self.style.WARNING(
                    f"⚠ {operador.get_full_name()} - Ya tiene patrón para {fecha_inicio}"
                ))
                ya_existian += 1
            else:
                # Crear patrón
                PatronOperador.objects.create(
                    operador=operador,
                    fecha_inicio_patron=fecha_inicio,
                    turno_inicial_patron=turno,
                    motivo=motivo
                )
                self.stdout.write(self.style.SUCCESS(
                    f"✓ {operador.get_full_name()} - Patrón {turno} configurado"
                ))
                configurados += 1
        
        self.stdout.write("")
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS(
            f"TOTAL: {configurados} patrones configurados, {ya_existian} ya existían"
        ))
        self.stdout.write("=" * 70)
        
        if configurados > 0:
            self.stdout.write("\n" + self.style.NOTICE(
                "Próximo paso: Regenerar turnos con:\n"
                f"  python manage.py regenerar_turnos_v4 --todos --desde {fecha_inicio} --hasta 2026-02-28"
            ))
