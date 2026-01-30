from django.core.management.base import BaseCommand
from apps.horas_extras.models_normativo import ParametroNormativo
from datetime import date
from decimal import Decimal

class Command(BaseCommand):
    help = 'Carga la progresión futura de la Ley 2101 (Reducción de Jornada)'

    def handle(self, *args, **kwargs):
        self.stdout.write("Cargando proyección normativa futura...")

        # 1. Ajustar el parámetro actual (44h)
        # Buscamos el parámetro que inicia el 25 de diciembre de 2025
        param_actual = ParametroNormativo.objects.filter(
            vigencia_desde=date(2025, 12, 25)
        ).first()

        if param_actual:
            # Este parámetro (44h) debe terminar el 14 de julio de 2026
            param_actual.vigencia_hasta = date(2026, 7, 14)
            if "Vigente hasta reducción" not in param_actual.descripcion:
                param_actual.descripcion += " (Vigente hasta reducción a 42h)"
            param_actual.save()
            self.stdout.write(self.style.SUCCESS(f"✓ Actualizado fin de vigencia norma 44h: {param_actual.vigencia_hasta}"))

        # 2. Crear el parámetro final (42h) desde el 15 de julio de 2026
        # Ley 2101 de 2021: 42 horas semanales
        # Divisor mensual sugerido: 210 horas
        
        defaults_2026 = {
            'vigencia_hasta': None, # Indefinido por ahora (se actualizará con el paso 3)
            'descripcion': 'Ley 2101 de 2021 - Implementación final jornada 42 horas semanales.',
            
            # Jornada
            'jornada_semanal_max': 42,
            'jornada_diaria_max': 8,
            'divisor_mensual': 210,
            
            # Horario Nocturno (se mantiene la reforma de Dic 2025)
            'hora_inicio_nocturno': '19:00',
            'hora_fin_nocturno': '06:00',
            
            # Recargos
            'recargo_nocturno': Decimal('0.35'),
            'recargo_dominical_festivo': Decimal('0.90'), # Sube al 90% en Julio 2026
            'recargo_nocturno_festivo': Decimal('1.25'), # 35% + 90%
            
            # Extras
            'recargo_extra_diurno': Decimal('0.25'),
            'recargo_extra_nocturno': Decimal('0.75'),
            
            'tope_extra_dia': 2,
            'tope_extra_semana': 12,
        }

        nuevo_param, created = ParametroNormativo.objects.get_or_create(
            vigencia_desde=date(2026, 7, 15),
            defaults=defaults_2026
        )

        if created:
            self.stdout.write(self.style.SUCCESS("✓ Creado parámetro norma 2026 (42h semanales, Domingo 90%)"))
        else:
             # Si ya existe, actualizamos valores clave por si acaso
            for key, value in defaults_2026.items():
                setattr(nuevo_param, key, value)
            nuevo_param.save()
            self.stdout.write(self.style.WARNING("! El parámetro 2026 ya existía (actualizado)"))

        # 3. Crear el parámetro final de Recargos Dominicales (100% desde Julio 2027)
        # La jornada sigue siendo 42h, pero el recargo dominical sube
        
        # Primero cerramos el de 2026
        nuevo_param.vigencia_hasta = date(2027, 6, 30)
        nuevo_param.save()
             
        defaults_2027 = {
            'vigencia_hasta': None,
            'descripcion': 'Ley 2101 y Reforma Laboral - Recargo Dominical al 100%',
            
             # Mismo horario y jornada que 2026
            'jornada_semanal_max': 42,
            'jornada_diaria_max': 8,
            'divisor_mensual': 210,
            'hora_inicio_nocturno': '19:00',
            'hora_fin_nocturno': '06:00',
            
            # CAMBIOS EN RECARGOS DOMINICALES (100%)
            'recargo_nocturno': Decimal('0.35'),
            'recargo_dominical_festivo': Decimal('1.00'), # 100% FULL
            'recargo_nocturno_festivo': Decimal('1.35'), # 35% + 100%
            
            # Extras
            'recargo_extra_diurno': Decimal('0.25'),
            'recargo_extra_nocturno': Decimal('0.75'),
            
            'tope_extra_dia': 2,
            'tope_extra_semana': 12,
        }

        param_2027, created_2027 = ParametroNormativo.objects.get_or_create(
             vigencia_desde=date(2027, 7, 1),
             defaults=defaults_2027
        )
        
        if created_2027:
            self.stdout.write(self.style.SUCCESS("✓ Creado parámetro norma 2027 (Dominical al 100%)"))
        else:
            for key, value in defaults_2027.items():
                setattr(param_2027, key, value)
            param_2027.save()
            self.stdout.write(self.style.WARNING("! El parámetro 2027 ya existía (actualizado)"))
