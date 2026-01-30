# apps/horas_extras/management/commands/configurar_horas_turnos.py
"""
Comando para configurar las horas correctas por día para cada TipoTurno.
Ejecutar con: python manage.py configurar_horas_turnos
"""

from django.core.management.base import BaseCommand
from decimal import Decimal
from datetime import time
from apps.horas_extras.models import TipoTurno


class Command(BaseCommand):
    help = 'Configura las horas correctas por día de la semana para cada TipoTurno'

    def handle(self, *args, **options):
        self.stdout.write('Configurando horas por día para TipoTurno...\n')
        
        # ========== TURNO M (MAÑANA) ==========
        # Lun/Sáb/Dom: 8h (06:00-14:00)
        # Mar/Mié/Jue/Vie: 7h (07:00-14:00)
        try:
            turno_m = TipoTurno.objects.get(codigo='M')
            turno_m.hora_inicio_lunes = time(6, 0)
            turno_m.hora_fin_lunes = time(14, 0)
            turno_m.horas_lunes = Decimal('8.00')
            
            turno_m.hora_inicio_martes = time(7, 0)
            turno_m.hora_fin_martes = time(14, 0)
            turno_m.horas_martes = Decimal('7.00')
            
            turno_m.hora_inicio_miercoles = time(7, 0)
            turno_m.hora_fin_miercoles = time(14, 0)
            turno_m.horas_miercoles = Decimal('7.00')
            
            turno_m.hora_inicio_jueves = time(7, 0)
            turno_m.hora_fin_jueves = time(14, 0)
            turno_m.horas_jueves = Decimal('7.00')
            
            turno_m.hora_inicio_viernes = time(7, 0)
            turno_m.hora_fin_viernes = time(14, 0)
            turno_m.horas_viernes = Decimal('7.00')
            
            turno_m.hora_inicio_sabado = time(6, 0)
            turno_m.hora_fin_sabado = time(14, 0)
            turno_m.horas_sabado = Decimal('8.00')
            
            turno_m.hora_inicio_domingo = time(6, 0)
            turno_m.hora_fin_domingo = time(14, 0)
            turno_m.horas_domingo = Decimal('8.00')
            
            turno_m.es_nocturno = False
            turno_m.save()
            self.stdout.write(self.style.SUCCESS('✓ Turno M configurado'))
        except TipoTurno.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠ Turno M no encontrado'))
        
        # ========== TURNO T (TARDE) ==========
        # Lun/Sáb/Dom: 8h (14:00-22:00)
        # Mar/Mié/Jue/Vie: 7h (16:00-23:00)
        try:
            turno_t = TipoTurno.objects.get(codigo='T')
            turno_t.hora_inicio_lunes = time(14, 0)
            turno_t.hora_fin_lunes = time(22, 0)
            turno_t.horas_lunes = Decimal('8.00')
            
            turno_t.hora_inicio_martes = time(16, 0)
            turno_t.hora_fin_martes = time(23, 0)
            turno_t.horas_martes = Decimal('7.00')
            
            turno_t.hora_inicio_miercoles = time(16, 0)
            turno_t.hora_fin_miercoles = time(23, 0)
            turno_t.horas_miercoles = Decimal('7.00')
            
            turno_t.hora_inicio_jueves = time(16, 0)
            turno_t.hora_fin_jueves = time(23, 0)
            turno_t.horas_jueves = Decimal('7.00')
            
            turno_t.hora_inicio_viernes = time(16, 0)
            turno_t.hora_fin_viernes = time(23, 0)
            turno_t.horas_viernes = Decimal('7.00')
            
            turno_t.hora_inicio_sabado = time(14, 0)
            turno_t.hora_fin_sabado = time(22, 0)
            turno_t.horas_sabado = Decimal('8.00')
            
            turno_t.hora_inicio_domingo = time(14, 0)
            turno_t.hora_fin_domingo = time(22, 0)
            turno_t.horas_domingo = Decimal('8.00')
            
            turno_t.es_nocturno = False
            turno_t.save()
            self.stdout.write(self.style.SUCCESS('✓ Turno T configurado'))
        except TipoTurno.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠ Turno T no encontrado'))
        
        # ========== TURNO N (NOCHE) ==========
        # Sáb/Dom/Lun: 8h (22:00-06:00)
        # Mar/Jue/Vie: 7h (23:00-06:00)
        # Mié: 7h (23:00-06:00) - El caso especial se maneja con N_W1/N_W2
        try:
            turno_n = TipoTurno.objects.get(codigo='N')
            turno_n.hora_inicio_lunes = time(22, 0)
            turno_n.hora_fin_lunes = time(6, 0)  # Cruza medianoche
            turno_n.horas_lunes = Decimal('8.00')
            
            turno_n.hora_inicio_martes = time(23, 0)
            turno_n.hora_fin_martes = time(6, 0)
            turno_n.horas_martes = Decimal('7.00')
            
            turno_n.hora_inicio_miercoles = time(23, 0)
            turno_n.hora_fin_miercoles = time(6, 0)
            turno_n.horas_miercoles = Decimal('7.00')  # Por defecto; N_W1/N_W2 para casos especiales
            
            turno_n.hora_inicio_jueves = time(23, 0)
            turno_n.hora_fin_jueves = time(6, 0)
            turno_n.horas_jueves = Decimal('7.00')
            
            turno_n.hora_inicio_viernes = time(23, 0)
            turno_n.hora_fin_viernes = time(6, 0)
            turno_n.horas_viernes = Decimal('7.00')
            
            turno_n.hora_inicio_sabado = time(22, 0)
            turno_n.hora_fin_sabado = time(6, 0)
            turno_n.horas_sabado = Decimal('8.00')
            
            turno_n.hora_inicio_domingo = time(22, 0)
            turno_n.hora_fin_domingo = time(6, 0)
            turno_n.horas_domingo = Decimal('8.00')
            
            turno_n.es_nocturno = True
            turno_n.save()
            self.stdout.write(self.style.SUCCESS('✓ Turno N configurado'))
        except TipoTurno.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠ Turno N no encontrado'))
        
        # ========== TURNO N_W1 (Noche Miércoles 1h) ==========
        # Solo miércoles: 1h (23:00-00:00)
        try:
            turno_nw1 = TipoTurno.objects.get(codigo='N_W1')
            # Todos los días en 0 excepto miércoles
            turno_nw1.horas_lunes = Decimal('0.00')
            turno_nw1.horas_martes = Decimal('0.00')
            turno_nw1.hora_inicio_miercoles = time(23, 0)
            turno_nw1.hora_fin_miercoles = time(0, 0)
            turno_nw1.horas_miercoles = Decimal('1.00')
            turno_nw1.horas_jueves = Decimal('0.00')
            turno_nw1.horas_viernes = Decimal('0.00')
            turno_nw1.horas_sabado = Decimal('0.00')
            turno_nw1.horas_domingo = Decimal('0.00')
            turno_nw1.es_nocturno = True
            turno_nw1.save()
            self.stdout.write(self.style.SUCCESS('✓ Turno N_W1 configurado (Mié 1h)'))
        except TipoTurno.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠ Turno N_W1 no encontrado'))
        
        # ========== TURNO N_W2 (Noche Miércoles 6h) ==========
        # Solo miércoles: 6h (00:00-06:00) - Es la continuación del jueves
        try:
            turno_nw2 = TipoTurno.objects.get(codigo='N_W2')
            turno_nw2.horas_lunes = Decimal('0.00')
            turno_nw2.horas_martes = Decimal('0.00')
            turno_nw2.hora_inicio_miercoles = time(0, 0)
            turno_nw2.hora_fin_miercoles = time(6, 0)
            turno_nw2.horas_miercoles = Decimal('6.00')
            turno_nw2.horas_jueves = Decimal('0.00')
            turno_nw2.horas_viernes = Decimal('0.00')
            turno_nw2.horas_sabado = Decimal('0.00')
            turno_nw2.horas_domingo = Decimal('0.00')
            turno_nw2.es_nocturno = True
            turno_nw2.save()
            self.stdout.write(self.style.SUCCESS('✓ Turno N_W2 configurado (Mié 6h)'))
        except TipoTurno.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠ Turno N_W2 no encontrado'))
        
        # ========== TURNO A (APOYO) ==========
        # Lun-Vie: 8h (13:00-21:00)
        # Sáb/Dom: 0h
        try:
            turno_a = TipoTurno.objects.get(codigo='A')
            turno_a.hora_inicio_lunes = time(13, 0)
            turno_a.hora_fin_lunes = time(21, 0)
            turno_a.horas_lunes = Decimal('8.00')
            
            turno_a.hora_inicio_martes = time(13, 0)
            turno_a.hora_fin_martes = time(21, 0)
            turno_a.horas_martes = Decimal('8.00')
            
            turno_a.hora_inicio_miercoles = time(13, 0)
            turno_a.hora_fin_miercoles = time(21, 0)
            turno_a.horas_miercoles = Decimal('8.00')
            
            turno_a.hora_inicio_jueves = time(13, 0)
            turno_a.hora_fin_jueves = time(21, 0)
            turno_a.horas_jueves = Decimal('8.00')
            
            turno_a.hora_inicio_viernes = time(13, 0)
            turno_a.hora_fin_viernes = time(21, 0)
            turno_a.horas_viernes = Decimal('8.00')
            
            turno_a.hora_inicio_sabado = None
            turno_a.hora_fin_sabado = None
            turno_a.horas_sabado = Decimal('0.00')
            
            turno_a.hora_inicio_domingo = None
            turno_a.hora_fin_domingo = None
            turno_a.horas_domingo = Decimal('0.00')
            
            turno_a.es_nocturno = False
            turno_a.save()
            self.stdout.write(self.style.SUCCESS('✓ Turno A configurado (0h fines de semana)'))
        except TipoTurno.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠ Turno A no encontrado'))
        
        # ========== TURNO D (DESCANSO) ==========
        # Todos los días: 0h
        try:
            turno_d = TipoTurno.objects.get(codigo='D')
            turno_d.horas_lunes = Decimal('0.00')
            turno_d.horas_martes = Decimal('0.00')
            turno_d.horas_miercoles = Decimal('0.00')
            turno_d.horas_jueves = Decimal('0.00')
            turno_d.horas_viernes = Decimal('0.00')
            turno_d.horas_sabado = Decimal('0.00')
            turno_d.horas_domingo = Decimal('0.00')
            turno_d.es_nocturno = False
            turno_d.save()
            self.stdout.write(self.style.SUCCESS('✓ Turno D configurado (0h todos los días)'))
        except TipoTurno.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠ Turno D no encontrado'))
        
        self.stdout.write('\n' + self.style.SUCCESS('=== Configuración completada ==='))
        self.stdout.write('\nResumen de horas por turno:')
        self.stdout.write('  M: Lun/Sáb/Dom=8h, Mar-Vie=7h')
        self.stdout.write('  T: Lun/Sáb/Dom=8h, Mar-Vie=7h')
        self.stdout.write('  N: Lun/Sáb/Dom=8h, Mar/Jue/Vie=7h, Mié=7h (usar N_W1/N_W2 para casos especiales)')
        self.stdout.write('  A: Lun-Vie=8h, Sáb/Dom=0h')
        self.stdout.write('  D: Todos=0h')
        self.stdout.write('  N_W1: Mié=1h (primer miércoles del bloque N)')
        self.stdout.write('  N_W2: Mié=6h (último miércoles del bloque N)')
