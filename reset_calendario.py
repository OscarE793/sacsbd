import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sacsbd_project.settings')
django.setup()

from apps.horas_extras.models import RegistroTurno, ResumenMensual, PatronOperador

def limpiar_datos():
    print("=== LIMPIEZA DE CALENDARIO ===")
    
    confirm = input("¿Está seguro de eliminar TODOS los registros de turnos y resúmenes? (s/n): ")
    if confirm.lower() != 's':
        print("Operación cancelada.")
        return

    # 1. Eliminar Resúmenes (Dependent on stats)
    count_resumen = ResumenMensual.objects.count()
    ResumenMensual.objects.all().delete()
    print(f"✅ Eliminados {count_resumen} registros de ResumenMensual.")

    # 2. Eliminar Registros de Turno (The daily blocks)
    count_registros = RegistroTurno.objects.count()
    RegistroTurno.objects.all().delete()
    print(f"✅ Eliminados {count_registros} registros de RegistroTurno.")

    # 3. Optional: Patrones?
    # Usually users want to keep the patterns (assignments) and just regenerate dates.
    # We will leave patterns intact unless explicitly asked.
    
    print("\nLa base de datos de turnos está limpia.")
    print("Ahora puede ir a 'Generar Turnos' para recrear el calendario con la nueva lógica.")

if __name__ == "__main__":
    limpiar_datos()
