# apps/horas_extras/management/commands/cargar_parametros_normativos.py
"""
Command para cargar parámetros normativos iniciales.

Uso:
    python manage.py cargar_parametros_normativos

Carga dos versiones de parámetros:
1. Pre-reforma (antes del 25/12/2025): Nocturno desde 21:00
2. Post-reforma Ley 2101 (desde 25/12/2025): Nocturno desde 19:00
"""

from django.core.management.base import BaseCommand
from datetime import date, time
from decimal import Decimal

from apps.horas_extras.models_normativo import ParametroNormativo, PoliticaEmpresa


class Command(BaseCommand):
    help = 'Carga parámetros normativos iniciales para Colombia'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Cargando parámetros normativos...'))
        
        # ============================================================
        # PARÁMETROS NORMATIVOS
        # ============================================================
        
        # 1. NORMA PRE-REFORMA (antes del 25/12/2025)
        param_pre, created = ParametroNormativo.objects.get_or_create(
            vigencia_desde=date(2000, 1, 1),
            defaults={
                'vigencia_hasta': date(2025, 12, 24),
                'hora_inicio_nocturno': time(21, 0),  # 9PM
                'hora_fin_nocturno': time(6, 0),       # 6AM
                'recargo_nocturno': Decimal('0.35'),              # 35%
                'recargo_dominical_festivo': Decimal('0.75'),     # 75%
                'recargo_nocturno_festivo': Decimal('1.10'),      # 35% + 75% = 110%
                'recargo_extra_diurno': Decimal('0.25'),          # 25%
                'recargo_extra_nocturno': Decimal('0.75'),        # 75%
                'jornada_diaria_max': 8,
                'jornada_semanal_max': 46,           # Antes de la reforma
                'divisor_mensual': 230,
                'tope_extra_dia': 2,
                'tope_extra_semana': 12,
                'descripcion': 'Norma laboral colombiana pre-reforma Ley 2101. Jornada nocturna desde 21:00.'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Creado: {param_pre}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Ya existía: {param_pre}'))
        
        # 2. NORMA POST-REFORMA LEY 2101 (desde 25/12/2025)
        param_post, created = ParametroNormativo.objects.get_or_create(
            vigencia_desde=date(2025, 12, 25),
            defaults={
                'vigencia_hasta': None,  # Vigente indefinidamente
                'hora_inicio_nocturno': time(19, 0),  # 7PM ← CAMBIO CLAVE
                'hora_fin_nocturno': time(6, 0),       # 6AM
                'recargo_nocturno': Decimal('0.35'),              # 35%
                'recargo_dominical_festivo': Decimal('0.80'),     # 80% ← AUMENTA
                'recargo_nocturno_festivo': Decimal('1.15'),      # 35% + 80% = 115%
                'recargo_extra_diurno': Decimal('0.25'),          # 25%
                'recargo_extra_nocturno': Decimal('0.75'),        # 75%
                'jornada_diaria_max': 8,
                'jornada_semanal_max': 44,           # Reducción gradual 2025
                'divisor_mensual': 220,
                'tope_extra_dia': 2,
                'tope_extra_semana': 12,
                'descripcion': 'Ley 2101 de 2021 - Reducción jornada laboral. Jornada nocturna desde 19:00. Vigente desde 25/12/2025.'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Creado: {param_post}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Ya existía: {param_post}'))
        
        # ============================================================
        # POLÍTICA DE EMPRESA (opcional)
        # ============================================================
        
        politica, created = PoliticaEmpresa.objects.get_or_create(
            vigencia_desde=date(2000, 1, 1),
            defaults={
                'pagar_dominical_100': False,
                'sabado_es_descanso': False,
                'redondear_minutos': 0,
                'usar_banco_horas': False,
                'descripcion': 'Política por defecto - Aplica mínimos legales'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Creada política: {politica}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Ya existía política: {politica}'))
        
        # ============================================================
        # RESUMEN
        # ============================================================
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('RESUMEN DE PARÁMETROS NORMATIVOS'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        for param in ParametroNormativo.objects.all().order_by('vigencia_desde'):
            self.stdout.write(f'''
Vigencia: {param.vigencia_desde} → {param.vigencia_hasta or 'Indefinida'}
  • Jornada nocturna: {param.hora_inicio_nocturno.strftime('%H:%M')} - {param.hora_fin_nocturno.strftime('%H:%M')}
  • Recargo nocturno: {int(param.recargo_nocturno * 100)}%
  • Recargo dominical: {int(param.recargo_dominical_festivo * 100)}%
  • Jornada semanal máx: {param.jornada_semanal_max} horas
  • {param.descripcion[:60]}...
''')
        
        self.stdout.write(self.style.SUCCESS('\n✓ Parámetros normativos cargados correctamente.'))
        self.stdout.write(self.style.NOTICE(
            '\nEl sistema ahora aplicará automáticamente los parámetros correctos '
            'según la fecha del turno.'
        ))
