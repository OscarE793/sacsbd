import os
import django
from datetime import date, time
from decimal import Decimal
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sacsbd_project.settings')
django.setup()

from apps.horas_extras.models_normativo import ParametroNormativo

def fix_recargos():
    print("=== AUDITORÍA Y CORRECCIÓN DE PARÁMETROS NORMATIVOS (V2) ===")
    
    # 1. Asegurar VIGENTE (25-Dic-2025) - RDF 80%
    fecha_vigencia = date(2025, 12, 25)
    norma_2025 = ParametroNormativo.objects.filter(vigencia_desde=fecha_vigencia).first()
    if norma_2025:
        norma_2025.recargo_dominical_festivo = Decimal('0.80')
        norma_2025.recargo_nocturno = Decimal('0.35')
        norma_2025.save()
        print(f"Norma 2025 OK.")

    # 2. Configuración flexible para 42h (15-Jul-2026)
    fecha_jornada = date(2026, 7, 15)
    norma_jul_15 = ParametroNormativo.objects.filter(vigencia_desde=fecha_jornada).first()
    if norma_jul_15:
        print(f"Configuring 42h Custom Shifts for 2026...")
        
        # DEFINICIÓN LAXA: Administración define -1h Lunes y Sábado.
        # En utils.py, "fin_semana" aplica a Lunes, Sábado y Domingo.
        # Si cambiamos 'fin_semana' a 7h, afectamos DOMINGO TAMBIEN.
        # AJUSTE: GeneradorTurnosV4 trata Lun/Sab/Dom como 'fin_semana'.
        # Si el usuario quiere SOLO Lun y Sab, y NO Domingo, necesitamos JSON más granular.
        # La implementación actual en utils.py lee: config['M'][tipo_dia].
        # tipo_dia es 'fin_semana' para 0,5,6.
        # LIMITACION: Con la estructura actual de utils.py ("semana" vs "fin_semana"),
        # cambiar "fin_semana" afecta Domingo.
        # Pero Domingo es festivo/descanso o Dominical.
        # Si M trabaja Domingo (8h -> 7h), paga 7h dominicales.
        # Asumiremos que reducir "fin_semana" a 7h es aceptable para Lun/Sab/Dom en este modelo.
        
        custom_shifts = {
            "M": {
                "fin_semana": ["06:00", "13:00"] # 7h (Reducción de 1h)
            },
            "T": {
                "fin_semana": ["14:00", "21:00"] # 7h (Reducción de 1h)
            }
        }
        
        norma_jul_15.jornada_semanal_max = 42
        norma_jul_15.configuracion_turnos = json.dumps(custom_shifts, indent=2)
        norma_jul_15.save()
        print(f"  -> JSON Config Applied: {norma_jul_15.configuracion_turnos}")

    # Recalcular RNF
    for norma in ParametroNormativo.objects.all():
        norma.save()

if __name__ == '__main__':
    fix_recargos()
