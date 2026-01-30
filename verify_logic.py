import os
import django
from datetime import date, time, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sacsbd_project.settings')
django.setup()

from django.contrib.auth.models import User
from apps.horas_extras.models import TipoTurno, RegistroTurno, PatronOperador
from apps.horas_extras.utils import GeneradorTurnosV4
from apps.horas_extras.calculos_legales import CalculadoraLegal

def test_logic():
    print("=== INICIANDO VERIFICACIÓN DE LÓGICA V5 ===")
    
    # 1. Setup Data
    user, _ = User.objects.get_or_create(username='test_logic_user', defaults={'first_name': 'Test', 'last_name': 'User'})
    
    # Ensure Shift Types exist
    defaults = {
        'M': {'horas_lunes': 8, 'horas_martes': 7},
        'N': {'horas_lunes': 8, 'horas_martes': 7, 'es_nocturno': True},
        'T': {'horas_lunes': 8, 'horas_martes': 7},
        'A': {'horas_lunes': 8, 'horas_martes': 8},
        'D': {'horas_lunes': 0, 'horas_martes': 0}
    }
    
    for code, data in defaults.items():
        TipoTurno.objects.get_or_create(
            codigo=code, 
            defaults={'nombre': f'Turno {code}', 'descripcion': f'Turno {code}', **data}
        )

    # 2. Test Case: Transition N -> M
    # Scenario: Tue=N, Wed=M
    # Expectation: 
    #   Tue (N): Madrugada (Depends on Mon) + Noche (1h)
    #   Wed (M): 7h (07:00-14:00). NO inherited Madrugada from Tue.
    
    # Let's verify GeneradorTurnosV4 logic specifically for Wed (M)
    # We simulate context manually since we are testing the logic function directly first
    
    print("\n[TEST 1] Verificando lógica de vecindad para Turno M (post-N)")
    # Logic: if M, returns M range. Should NOT check neighbors.
    rangos_m = GeneradorTurnosV4.obtener_rangos_horarios(
        turno='M', 
        fecha=date(2026, 6, 3), # Wednesday
        context_vecindad={'prev': 'N', 'today': 'M', 'next': 'M'}
    )
    print(f"Rangos generado para Miércoles M (con ayer N): {rangos_m}")
    
    if len(rangos_m) == 1 and rangos_m[0]['inicio'] == time(7,0):
        print("✅ PASS: Turno M ignoró vecindad N y devolvió rango correcto (07:00-14:00)")
    else:
        print(f"❌ FAIL: Turno M devolvió rangos inesperados: {rangos_m}")

    print("\n[TEST 2] Verificando lógica de vecindad para Turno N (Madrugada + Noche)")
    # Scenario: Tue=N (prev=N, next=N) -> Should have Madrugada(6h) + Noche(1h) = 7h
    # Date: Tue 2026-06-02
    rangos_n = GeneradorTurnosV4.obtener_rangos_horarios(
        turno='N',
        fecha=date(2026, 6, 2),
        context_vecindad={'prev': 'N', 'today': 'N', 'next': 'N'} 
    )
    print(f"Rangos generado para Martes N (N-N-N): {rangos_n}")
    
    has_madrugada = any(r.get('es_madrugada') for r in rangos_n)
    has_noche = any(r.get('es_noche') for r in rangos_n)
    hours = sum(GeneradorTurnosV4.calcular_horas_segmento(r) for r in rangos_n)
    
    if has_madrugada and has_noche and hours == Decimal('7.0'):
         print("✅ PASS: Turno N (N-N-N) tiene Madrugada y Noche (Total 7h)")
    else:
         print(f"❌ FAIL: Turno N fallo. Madrugada:{has_madrugada}, Noche:{has_noche}, Total:{hours}")

    print("\n[TEST 3] Verificando TOTAL en CalculadoraLegal")
    # Simulate a shift with segments
    calc = CalculadoraLegal()
    
    # Create a mock Turno object
    class MockTurno:
        def __init__(self, tipo, fecha, inicio, fin, horas):
            self.tipo_turno = tipo
            self.fecha = fecha
            self.hora_inicio_real = inicio
            self.hora_fin_real = fin
            self.horas_trabajadas = horas
            
    tipo_m = TipoTurno.objects.get(codigo='M')
    # Wed M: 07:00 - 14:00 (7h)
    turno_m = MockTurno(tipo_m, date(2026, 6, 3), time(7,0), time(14,0), Decimal('7.0'))
    
    res = calc.calcular_horas_turno(turno_m)
    print(f"Resultado CalculadoraLegal para M (7h): {res}")
    
    total = res[date(2026, 6, 3)]['TOTAL']
    hod = res[date(2026, 6, 3)]['HOD']
    
    if total == Decimal('7.0') and hod == Decimal('7.0'):
        print("✅ PASS: TOTAL calculado correctamente (7.0) sin duplicar.")
    else:
        print(f"❌ FAIL: TOTAL incorrecto. Esperado 7.0, Obtenido {total}")

    # Breakdown checks
    sum_parts = (
        res[date(2026, 6, 3)]['HOD'] + 
        res[date(2026, 6, 3)]['RNO'] + 
        res[date(2026, 6, 3)]['RDF'] + 
        res[date(2026, 6, 3)]['RNF']
    )
    if sum_parts == total:
        print("✅ PASS: Suma de partes igual a TOTAL.")
    else:
         print(f"❌ FAIL: Suma de partes ({sum_parts}) != TOTAL ({total})")

if __name__ == '__main__':
    test_logic()
