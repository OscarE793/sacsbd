# apps/horas_extras/management/commands/crear_turnos_correctos.py
from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import time
from decimal import Decimal
from apps.horas_extras.models import TipoTurno


class Command(BaseCommand):
    help = 'Crea los 5 tipos de turno correctos según las especificaciones del sistema'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('[INICIO] Creando tipos de turno correctos...'))

        try:
            with transaction.atomic():
                # Eliminar turnos existentes
                TipoTurno.objects.all().delete()
                self.stdout.write('[INFO] Turnos existentes eliminados')

                self.crear_turnos()

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('[OK] Tipos de turno creados exitosamente!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[ERROR] Error al crear turnos: {str(e)}'))
            raise

    def crear_turnos(self):
        """Crea los 5 tipos de turno según especificaciones"""

        # ===================================================================
        # TURNO APOYO: 13:00 PM - 21:00 PM (Lunes a Viernes, NO Sáb/Dom)
        # ===================================================================
        self.stdout.write('[TURNO] Creando Turno Apoyo...')
        TipoTurno.objects.create(
            nombre='apoyo',
            descripcion='Turno Apoyo',
            codigo='Apoyo-A',
            es_nocturno=False,

            # Lunes: 13:00 - 21:00 (8 horas)
            hora_inicio_lunes=time(13, 0),
            hora_fin_lunes=time(21, 0),
            horas_lunes=Decimal('8.00'),

            # Martes: 13:00 - 20:00 (7 horas)
            hora_inicio_martes=time(13, 0),
            hora_fin_martes=time(20, 0),
            horas_martes=Decimal('7.00'),

            # Miércoles: 13:00 - 20:00 (7 horas)
            hora_inicio_miercoles=time(13, 0),
            hora_fin_miercoles=time(20, 0),
            horas_miercoles=Decimal('7.00'),

            # Jueves: 13:00 - 20:00 (7 horas)
            hora_inicio_jueves=time(13, 0),
            hora_fin_jueves=time(20, 0),
            horas_jueves=Decimal('7.00'),

            # Viernes: 13:00 - 20:00 (7 horas)
            hora_inicio_viernes=time(13, 0),
            hora_fin_viernes=time(20, 0),
            horas_viernes=Decimal('7.00'),

            # Sábado: NO TRABAJA
            hora_inicio_sabado=None,
            hora_fin_sabado=None,
            horas_sabado=Decimal('0.00'),

            # Domingo: NO TRABAJA
            hora_inicio_domingo=None,
            hora_fin_domingo=None,
            horas_domingo=Decimal('0.00'),
        )
        self.stdout.write('[OK] Turno Apoyo creado')

        # ===================================================================
        # TURNO 1 MAÑANA: 06:00 AM - 14:00 PM (Todos los días)
        # ===================================================================
        self.stdout.write('[TURNO] Creando Turno 1 Mañana...')
        TipoTurno.objects.create(
            nombre='manana',
            descripcion='Turno Mañana',
            codigo='Turno 1-M',
            es_nocturno=False,

            # Lunes: 06:00 - 14:00 (8 horas)
            hora_inicio_lunes=time(6, 0),
            hora_fin_lunes=time(14, 0),
            horas_lunes=Decimal('8.00'),

            # Martes: 07:00 - 14:00 (7 horas)
            hora_inicio_martes=time(7, 0),
            hora_fin_martes=time(14, 0),
            horas_martes=Decimal('7.00'),

            # Miércoles: 07:00 - 14:00 (7 horas)
            hora_inicio_miercoles=time(7, 0),
            hora_fin_miercoles=time(14, 0),
            horas_miercoles=Decimal('7.00'),

            # Jueves: 07:00 - 14:00 (7 horas)
            hora_inicio_jueves=time(7, 0),
            hora_fin_jueves=time(14, 0),
            horas_jueves=Decimal('7.00'),

            # Viernes: 07:00 - 14:00 (7 horas)
            hora_inicio_viernes=time(7, 0),
            hora_fin_viernes=time(14, 0),
            horas_viernes=Decimal('7.00'),

            # Sábado: 06:00 - 14:00 (8 horas)
            hora_inicio_sabado=time(6, 0),
            hora_fin_sabado=time(14, 0),
            horas_sabado=Decimal('8.00'),

            # Domingo: 06:00 - 14:00 (8 horas)
            hora_inicio_domingo=time(6, 0),
            hora_fin_domingo=time(14, 0),
            horas_domingo=Decimal('8.00'),
        )
        self.stdout.write('[OK] Turno 1 Mañana creado')

        # ===================================================================
        # TURNO 2 TARDE: 14:00 PM - 22:00 PM (Todos los días)
        # ===================================================================
        self.stdout.write('[TURNO] Creando Turno 2 Tarde...')
        TipoTurno.objects.create(
            nombre='tarde',
            descripcion='Turno Tarde',
            codigo='Turno 2-T',
            es_nocturno=False,

            # Lunes: 14:00 - 22:00 (8 horas)
            hora_inicio_lunes=time(14, 0),
            hora_fin_lunes=time(22, 0),
            horas_lunes=Decimal('8.00'),

            # Martes: 14:00 - 21:00 (7 horas)
            hora_inicio_martes=time(14, 0),
            hora_fin_martes=time(21, 0),
            horas_martes=Decimal('7.00'),

            # Miércoles: 14:00 - 21:00 (7 horas)
            hora_inicio_miercoles=time(14, 0),
            hora_fin_miercoles=time(21, 0),
            horas_miercoles=Decimal('7.00'),

            # Jueves: 14:00 - 21:00 (7 horas)
            hora_inicio_jueves=time(14, 0),
            hora_fin_jueves=time(21, 0),
            horas_jueves=Decimal('7.00'),

            # Viernes: 14:00 - 21:00 (7 horas)
            hora_inicio_viernes=time(14, 0),
            hora_fin_viernes=time(21, 0),
            horas_viernes=Decimal('7.00'),

            # Sábado: 14:00 - 22:00 (8 horas)
            hora_inicio_sabado=time(14, 0),
            hora_fin_sabado=time(22, 0),
            horas_sabado=Decimal('8.00'),

            # Domingo: 14:00 - 22:00 (8 horas)
            hora_inicio_domingo=time(14, 0),
            hora_fin_domingo=time(22, 0),
            horas_domingo=Decimal('8.00'),
        )
        self.stdout.write('[OK] Turno 2 Tarde creado')

        # ===================================================================
        # TURNO 3 NOCHE: 22:00 PM - 06:00 AM (Todos los días)
        # ===================================================================
        self.stdout.write('[TURNO] Creando Turno 3 Noche...')
        TipoTurno.objects.create(
            nombre='noche',
            descripcion='Turno Noche',
            codigo='Turno 3-N',
            es_nocturno=True,

            # Lunes: 22:00 - 06:00 (8 horas)
            hora_inicio_lunes=time(22, 0),
            hora_fin_lunes=time(6, 0),
            horas_lunes=Decimal('8.00'),

            # Martes: 23:00 - 06:00 (7 horas)
            hora_inicio_martes=time(23, 0),
            hora_fin_martes=time(6, 0),
            horas_martes=Decimal('7.00'),

            # Miércoles: 23:00 - 06:00 (7 horas)
            hora_inicio_miercoles=time(23, 0),
            hora_fin_miercoles=time(6, 0),
            horas_miercoles=Decimal('7.00'),

            # Jueves: 23:00 - 06:00 (7 horas)
            hora_inicio_jueves=time(23, 0),
            hora_fin_jueves=time(6, 0),
            horas_jueves=Decimal('7.00'),

            # Viernes: 23:00 - 06:00 (7 horas)
            hora_inicio_viernes=time(23, 0),
            hora_fin_viernes=time(6, 0),
            horas_viernes=Decimal('7.00'),

            # Sábado: 22:00 - 06:00 (8 horas)
            hora_inicio_sabado=time(22, 0),
            hora_fin_sabado=time(6, 0),
            horas_sabado=Decimal('8.00'),

            # Domingo: 22:00 - 06:00 (8 horas)
            hora_inicio_domingo=time(22, 0),
            hora_fin_domingo=time(6, 0),
            horas_domingo=Decimal('8.00'),
        )
        self.stdout.write('[OK] Turno 3 Noche creado')

        # ===================================================================
        # DESCANSO: Día libre
        # ===================================================================
        self.stdout.write('[TURNO] Creando Descanso...')
        TipoTurno.objects.create(
            nombre='descanso',
            descripcion='Día Descanso',
            codigo='Des o Permi-D',
            es_nocturno=False,

            # Todos los días: 0 horas
            hora_inicio_lunes=None,
            hora_fin_lunes=None,
            horas_lunes=Decimal('0.00'),

            hora_inicio_martes=None,
            hora_fin_martes=None,
            horas_martes=Decimal('0.00'),

            hora_inicio_miercoles=None,
            hora_fin_miercoles=None,
            horas_miercoles=Decimal('0.00'),

            hora_inicio_jueves=None,
            hora_fin_jueves=None,
            horas_jueves=Decimal('0.00'),

            hora_inicio_viernes=None,
            hora_fin_viernes=None,
            horas_viernes=Decimal('0.00'),

            hora_inicio_sabado=None,
            hora_fin_sabado=None,
            horas_sabado=Decimal('0.00'),

            hora_inicio_domingo=None,
            hora_fin_domingo=None,
            horas_domingo=Decimal('0.00'),
        )
        self.stdout.write('[OK] Descanso creado')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('[RESUMEN] Se crearon 5 tipos de turno:'))
        self.stdout.write('  1. Apoyo-A: 13:00-21:00 (Lun-Vie, 7-8h)')
        self.stdout.write('  2. Turno 1-M: 06:00-14:00 (Todos los días, 7-8h)')
        self.stdout.write('  3. Turno 2-T: 14:00-22:00 (Todos los días, 7-8h)')
        self.stdout.write('  4. Turno 3-N: 22:00-06:00 (Todos los días, 7-8h)')
        self.stdout.write('  5. Des o Permi-D: Descanso')
