# fix_namespace.py
"""
Script para reemplazar namespace 'recargos:' por 'horas_extras:' en todo el proyecto.
"""
import os
import re

# Archivos a modificar (basado en grep_search)
archivos = [
    r"templates\partials\sidebar.html",
    r"templates\horas_extras\turnos\generar.html",
    r"templates\horas_extras\reporte_unificado.html",
    r"templates\horas_extras\turnos\form.html",
    r"templates\horas_extras\reportes\resultado.html",
    r"templates\horas_extras\reportes\filtro.html",
    r"templates\horas_extras\empleados\detalle.html",
    r"templates\horas_extras\empleados\lista.html",
    r"templates\horas_extras\dashboard.html",
    r"templates\horas_extras\calendario\calendario.html",
    r"templates\base.html",
    r"apps\horas_extras\views.py",
]

BASE_DIR = r"c:\Users\Oscar Jaramillo\Documents\sacsbd"

def reemplazar_en_archivo(ruta_completa):
    """Reemplaza 'recargos:' por 'horas_extras:' en un archivo"""
    try:
        with open(ruta_completa, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Contar reemplazos
        count = contenido.count("recargos:")
        
        if count > 0:
            # Reemplazar
            nuevo_contenido = contenido.replace("recargos:", "horas_extras:")
            
            # Guardar
            with open(ruta_completa, 'w', encoding='utf-8') as f:
                f.write(nuevo_contenido)
            
            print(f"✓ {ruta_completa}: {count} reemplazos")
            return count
        else:
            print(f"  {ruta_completa}: sin cambios")
            return 0
    except Exception as e:
        print(f"✗ {ruta_completa}: ERROR - {e}")
        return 0

def main():
    print("=" * 70)
    print("REEMPLAZO MASIVO: 'recargos:' → 'horas_extras:'")
    print("=" * 70)
    print()
    
    total_reemplazos = 0
    
    for archivo_rel in archivos:
        ruta_completa = os.path.join(BASE_DIR, archivo_rel)
        if os.path.exists(ruta_completa):
            count = reemplazar_en_archivo(ruta_completa)
            total_reemplazos += count
        else:
            print(f"⚠ {ruta_completa}: NO EXISTE")
    
    print()
    print("=" * 70)
    print(f"TOTAL: {total_reemplazos} reemplazos en {len(archivos)} archivos")
    print("=" * 70)
    print()
    print("✅ Ahora puedes ejecutar: python manage.py runserver")

if __name__ == "__main__":
    main()
