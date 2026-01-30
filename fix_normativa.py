import os
import django
from datetime import date, time, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sacsbd_project.settings')
django.setup()

from apps.horas_extras.models_normativo import ParametroNormativo
from apps.horas_extras.calculos_legales import CalculadoraLegal
from apps.horas_extras.models import TipoTurno

def fix_normativa():
    print("=== CAMBIANDO INICIO NOCTURNO A 19:00 (7 PM) ===")
    
    fecha_vigencia = date(2025, 12, 25)
    
    # Check existing
    norma = ParametroNormativo.objects.filter(vigencia_desde=fecha_vigencia).first()
    
    if not norma:
        print(f"Creating new ParametroNormativo for {fecha_vigencia}")
        norma = ParametroNormativo(
            vigencia_desde=fecha_vigencia,
            descripcion="Reforma Laboral 2025 (Nocturno desde 19:00)",
            hora_inicio_nocturno=time(19, 0), # 7 PM
            hora_fin_nocturno=time(6, 0)
        )
        norma.save()
    else:
        print(f"Updating existing ParametroNormativo {norma}")
        norma.hora_inicio_nocturno = time(19, 0)
        norma.save()
        
    print(f"✅ Norma actualizada: Inicio Nocturno = {norma.hora_inicio_nocturno}")
    
    # VERIFY CALCULATION
    print("\n=== VERIFICANDO CÁLCULO TURNO T (16:00 - 23:00) ===")
    # 16:00 - 19:00 = 3h HOD
    # 19:00 - 23:00 = 4h RNO
    
    calc = CalculadoraLegal()
    
    class MockTurno:
        def __init__(self, tipo, fecha, inicio, fin, horas):
            self.tipo_turno = tipo
            self.fecha = fecha
            self.hora_inicio_real = inicio
            self.hora_fin_real = fin
            self.horas_trabajadas = horas
    
    # Mock Turno T
    try:
        real_tipo_t = TipoTurno.objects.get(codigo='T')
    except TipoTurno.DoesNotExist:
        # Fallback if T doesn't exist (unlikely in this env)
        print("Warning: Turno T not found in DB, skipping verify")
        return

    turno_t = MockTurno(
        real_tipo_t,
        date(2026, 6, 3), # Wednesday
        time(16, 0),
        time(23, 0),
        Decimal('7.0')
    )
    
    res = calc.calcular_horas_turno(turno_t)
    dia_res = res[date(2026, 6, 3)]
    
    print(f"Resultado: HOD={dia_res['HOD']}, RNO={dia_res['RNO']}")
    
    if dia_res['HOD'] == Decimal('3.0') and dia_res['RNO'] == Decimal('4.0'):
        print("✅ PASS: Correct breakdown (3h HOD + 4h RNO)")
    else:
        print(f"❌ FAIL: Expected 3.0/4.0, got {dia_res['HOD']}/{dia_res['RNO']}")

if __name__ == '__main__':
    fix_normativa()
