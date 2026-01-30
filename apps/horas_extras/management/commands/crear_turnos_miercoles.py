from django.core.management.base import BaseCommand
from apps.horas_extras.models import TipoTurno
from decimal import Decimal
from datetime import time

class Command(BaseCommand):
    help = 'Crea los tipos de turno especiales para validación de miércoles (N_W1 y N_W2)'

    def handle(self, *args, **kwargs):
        # N_W1: Primer miércoles de turno noche (solo 1 hora: 23:00-24:00)
        # N_W2: Último miércoles de turno noche (solo 6 horas: 00:00-06:00)
        
        turnos_data = [
            {
                'codigo': 'N_W1',
                'nombre': 'noche_w1',  # Nueva opción en TURNO_CHOICES
                'descripcion': 'Noche Miercoles 1h (23:00-24:00)',
                'es_nocturno': True,
                # Solo 1 hora todos los días
                'horas_lunes': Decimal('1.00'),
                'horas_martes': Decimal('1.00'),
                'horas_miercoles': Decimal('1.00'),
                'horas_jueves': Decimal('1.00'),
                'horas_viernes': Decimal('1.00'),
                'horas_sabado': Decimal('1.00'),
                'horas_domingo': Decimal('1.00'),
            },
            {
                'codigo': 'N_W2',
                'nombre': 'noche_w2',  # Nueva opción en TURNO_CHOICES
                'descripcion': 'Noche Miercoles 6h (00:00-06:00)',
                'es_nocturno': True,
                # Solo 6 horas todos los días
                'horas_lunes': Decimal('6.00'),
                'horas_martes': Decimal('6.00'),
                'horas_miercoles': Decimal('6.00'),
                'horas_jueves': Decimal('6.00'),
                'horas_viernes': Decimal('6.00'),
                'horas_sabado': Decimal('6.00'),
                'horas_domingo': Decimal('6.00'),
            }
        ]

        for data in turnos_data:
            codigo = data.pop('codigo')
            tipo, created = TipoTurno.objects.update_or_create(
                codigo=codigo,
                defaults={
                    'activo': True,
                    **data
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Creado turno: {tipo.descripcion} ({codigo})'))
            else:
                self.stdout.write(self.style.WARNING(f'Actualizado turno: {tipo.descripcion} ({codigo})'))

