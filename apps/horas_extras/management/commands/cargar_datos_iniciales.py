# apps/horas_extras/management/commands/cargar_datos_iniciales.py
from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import datetime, time, date
from decimal import Decimal
from apps.horas_extras.models import TipoTurno, DiaFestivo, Empleado


class Command(BaseCommand):
    help = 'Carga datos iniciales para el módulo de horas extras según nueva legislación colombiana'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la recreación de datos existentes',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando carga de datos iniciales para Horas Extras...')
        )
        
        try:
            with transaction.atomic():
                self.crear_tipos_turno(options['force'])
                self.crear_dias_festivos_2024(options['force'])
                self.crear_dias_festivos_2025(options['force'])
                self.crear_empleados_ejemplo(options['force'])
                
            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS('✅ ¡Datos iniciales cargados exitosamente!')
            )
            self.stdout.write(
                self.style.SUCCESS('📋 El sistema está listo para usar con la nueva legislación colombiana')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al cargar datos: {str(e)}')
            )
            raise

    def crear_tipos_turno(self, force=False):
        """Crea los tipos de turno según los horarios de la imagen"""
        
        self.stdout.write('📅 Creando tipos de turno...')
        
        if force:
            TipoTurno.objects.all().delete()
            self.stdout.write('  🗑️  Datos existentes eliminados')
        
        # === TURNO MAÑANA ===
        turno_manana, created = TipoTurno.objects.get_or_create(
            nombre='manana',
            defaults={
                'descripcion': 'Turno Mañana',
                'codigo': 'M',
                'es_nocturno': False,
                
                # Martes: 7 AM - 2 PM (7 horas)
                'hora_inicio_martes': time(7, 0),
                'hora_fin_martes': time(14, 0),
                'horas_martes': Decimal('7.00'),
                
                # Miércoles: 7 AM - 2 PM (7 horas)
                'hora_inicio_miercoles': time(7, 0),
                'hora_fin_miercoles': time(14, 0),
                'horas_miercoles': Decimal('7.00'),
                
                # Jueves: 7 AM - 2 PM (7 horas)
                'hora_inicio_jueves': time(7, 0),
                'hora_fin_jueves': time(14, 0),
                'horas_jueves': Decimal('7.00'),
                
                # Viernes: 7 AM - 2 PM (7 horas)
                'hora_inicio_viernes': time(7, 0),
                'hora_fin_viernes': time(14, 0),
                'horas_viernes': Decimal('7.00'),
                
                # Sábado: 6 AM - 2 PM (8 horas)
                'hora_inicio_sabado': time(6, 0),
                'hora_fin_sabado': time(14, 0),
                'horas_sabado': Decimal('8.00'),
                
                # Domingo: 6 AM - 2 PM (8 horas)
                'hora_inicio_domingo': time(6, 0),
                'hora_fin_domingo': time(14, 0),
                'horas_domingo': Decimal('8.00'),
                
                # Lunes: 6 AM - 2 PM (8 horas)
                'hora_inicio_lunes': time(6, 0),
                'hora_fin_lunes': time(14, 0),
                'horas_lunes': Decimal('8.00'),
            }
        )
        
        # === TURNO TARDE ===
        turno_tarde, created = TipoTurno.objects.get_or_create(
            nombre='tarde',
            defaults={
                'descripcion': 'Turno Tarde',
                'codigo': 'T',
                'es_nocturno': False,
                
                # Martes: 4 PM - 11 PM (7 horas)
                'hora_inicio_martes': time(16, 0),
                'hora_fin_martes': time(23, 0),
                'horas_martes': Decimal('7.00'),
                
                # Miércoles: 4 PM - 11 PM (7 horas)
                'hora_inicio_miercoles': time(16, 0),
                'hora_fin_miercoles': time(23, 0),
                'horas_miercoles': Decimal('7.00'),
                
                # Jueves: 4 PM - 11 PM (7 horas)
                'hora_inicio_jueves': time(16, 0),
                'hora_fin_jueves': time(23, 0),
                'horas_jueves': Decimal('7.00'),
                
                # Viernes: 4 PM - 11 PM (7 horas)
                'hora_inicio_viernes': time(16, 0),
                'hora_fin_viernes': time(23, 0),
                'horas_viernes': Decimal('7.00'),
                
                # Sábado: 2 PM - 10 PM (8 horas)
                'hora_inicio_sabado': time(14, 0),
                'hora_fin_sabado': time(22, 0),
                'horas_sabado': Decimal('8.00'),
                
                # Domingo: 2 PM - 10 PM (8 horas)
                'hora_inicio_domingo': time(14, 0),
                'hora_fin_domingo': time(22, 0),
                'horas_domingo': Decimal('8.00'),
                
                # Lunes: 2 PM - 10 PM (8 horas)
                'hora_inicio_lunes': time(14, 0),
                'hora_fin_lunes': time(22, 0),
                'horas_lunes': Decimal('8.00'),
            }
        )
        
        # === TURNO NOCHE ===
        turno_noche, created = TipoTurno.objects.get_or_create(
            nombre='noche',
            defaults={
                'descripcion': 'Turno Noche',
                'codigo': 'N',
                'es_nocturno': True,
                
                # Martes: 11 PM - 6 AM (7 horas)
                'hora_inicio_martes': time(23, 0),
                'hora_fin_martes': time(6, 0),
                'horas_martes': Decimal('7.00'),
                
                # Miércoles: 11 PM - 6 AM (7 horas)
                'hora_inicio_miercoles': time(23, 0),
                'hora_fin_miercoles': time(6, 0),
                'horas_miercoles': Decimal('7.00'),
                
                # Jueves: 11 PM - 6 AM (7 horas)
                'hora_inicio_jueves': time(23, 0),
                'hora_fin_jueves': time(6, 0),
                'horas_jueves': Decimal('7.00'),
                
                # Viernes: 11 PM - 6 AM (7 horas)
                'hora_inicio_viernes': time(23, 0),
                'hora_fin_viernes': time(6, 0),
                'horas_viernes': Decimal('7.00'),
                
                # Sábado: 10 PM - 6 AM (8 horas)
                'hora_inicio_sabado': time(22, 0),
                'hora_fin_sabado': time(6, 0),
                'horas_sabado': Decimal('8.00'),
                
                # Domingo: 10 PM - 6 AM (8 horas)
                'hora_inicio_domingo': time(22, 0),
                'hora_fin_domingo': time(6, 0),
                'horas_domingo': Decimal('8.00'),
                
                # Lunes: 10 PM - 6 AM (8 horas)
                'hora_inicio_lunes': time(22, 0),
                'hora_fin_lunes': time(6, 0),
                'horas_lunes': Decimal('8.00'),
            }
        )
        
        # === TURNO APOYO ===
        turno_apoyo, created = TipoTurno.objects.get_or_create(
            nombre='apoyo',
            defaults={
                'descripcion': 'Turno Apoyo',
                'codigo': 'A',
                'es_nocturno': False,
                
                # Todos los días: 1 PM - 9 PM (8 horas)
                'hora_inicio_martes': time(13, 0),
                'hora_fin_martes': time(21, 0),
                'horas_martes': Decimal('8.00'),
                
                'hora_inicio_miercoles': time(13, 0),
                'hora_fin_miercoles': time(21, 0),
                'horas_miercoles': Decimal('8.00'),
                
                'hora_inicio_jueves': time(13, 0),
                'hora_fin_jueves': time(21, 0),
                'horas_jueves': Decimal('8.00'),
                
                'hora_inicio_viernes': time(13, 0),
                'hora_fin_viernes': time(21, 0),
                'horas_viernes': Decimal('8.00'),
                
                'hora_inicio_sabado': time(13, 0),
                'hora_fin_sabado': time(21, 0),
                'horas_sabado': Decimal('8.00'),
                
                'hora_inicio_domingo': time(13, 0),
                'hora_fin_domingo': time(21, 0),
                'horas_domingo': Decimal('8.00'),
                
                'hora_inicio_lunes': time(13, 0),
                'hora_fin_lunes': time(21, 0),
                'horas_lunes': Decimal('8.00'),
            }
        )
        
        # === DÍA DESCANSO ===
        dia_descanso, created = TipoTurno.objects.get_or_create(
            nombre='descanso',
            defaults={
                'descripcion': 'Día de Descanso',
                'codigo': 'D',
                'es_nocturno': False,
                
                # Sin horarios (día libre)
                'horas_martes': Decimal('0.00'),
                'horas_miercoles': Decimal('0.00'),
                'horas_jueves': Decimal('0.00'),
                'horas_viernes': Decimal('0.00'),
                'horas_sabado': Decimal('0.00'),
                'horas_domingo': Decimal('0.00'),
                'horas_lunes': Decimal('0.00'),
            }
        )
        
        total_turnos = TipoTurno.objects.count()
        self.stdout.write(f'  ✅ {total_turnos} tipos de turno configurados')
        
        # Mostrar resumen de turnos
        for turno in TipoTurno.objects.all():
            self.stdout.write(f'     📋 {turno.codigo} - {turno.descripcion}')

    def crear_dias_festivos_2024(self, force=False):
        """Crea los días festivos de Colombia para 2024"""
        
        self.stdout.write('🎉 Creando días festivos 2024...')
        
        if force:
            DiaFestivo.objects.filter(fecha__year=2024).delete()
        
        festivos_2024 = [
            # Fechas fijas
            ('Año Nuevo', date(2024, 1, 1), 'fijo'),
            ('Día del Trabajo', date(2024, 5, 1), 'fijo'),
            ('Día de la Independencia', date(2024, 7, 20), 'fijo'),
            ('Batalla de Boyacá', date(2024, 8, 7), 'fijo'),
            ('Inmaculada Concepción', date(2024, 12, 8), 'fijo'),
            ('Navidad', date(2024, 12, 25), 'fijo'),
            
            # Lunes festivos (trasladados al lunes siguiente)
            ('Día de los Reyes Magos', date(2024, 1, 8), 'lunes_siguiente'),
            ('Día de San José', date(2024, 3, 25), 'lunes_siguiente'),
            ('San Pedro y San Pablo', date(2024, 7, 1), 'lunes_siguiente'),
            ('Asunción de la Virgen', date(2024, 8, 19), 'lunes_siguiente'),
            ('Día de la Raza', date(2024, 10, 14), 'lunes_siguiente'),
            ('Todos los Santos', date(2024, 11, 4), 'lunes_siguiente'),
            ('Independencia de Cartagena', date(2024, 11, 11), 'lunes_siguiente'),
            
            # Fechas religiosas variables (Semana Santa 2024)
            ('Jueves Santo', date(2024, 3, 28), 'religioso'),
            ('Viernes Santo', date(2024, 3, 29), 'religioso'),
            ('Ascensión del Señor', date(2024, 5, 13), 'religioso'),
            ('Corpus Christi', date(2024, 6, 3), 'religioso'),
            ('Sagrado Corazón de Jesús', date(2024, 6, 10), 'religioso'),
        ]
        
        festivos_creados = 0
        for nombre, fecha, tipo in festivos_2024:
            _, created = DiaFestivo.objects.get_or_create(
                fecha=fecha,
                nombre=nombre,
                defaults={
                    'tipo': tipo,
                    'es_nacional': True,
                    'activo': True,
                    'observaciones': f'Festivo nacional Colombia {fecha.year}'
                }
            )
            if created:
                festivos_creados += 1
        
        festivos_2024_total = DiaFestivo.objects.filter(fecha__year=2024).count()
        self.stdout.write(f'  ✅ {festivos_creados} nuevos festivos 2024 ({festivos_2024_total} total)')

    def crear_dias_festivos_2025(self, force=False):
        """Crea los días festivos de Colombia para 2025"""
        
        self.stdout.write('🎉 Creando días festivos 2025...')
        
        if force:
            DiaFestivo.objects.filter(fecha__year=2025).delete()
        
        festivos_2025 = [
            # Fechas fijas
            ('Año Nuevo', date(2025, 1, 1), 'fijo'),
            ('Día del Trabajo', date(2025, 5, 1), 'fijo'),
            ('Día de la Independencia', date(2025, 7, 20), 'fijo'),
            ('Batalla de Boyacá', date(2025, 8, 7), 'fijo'),
            ('Inmaculada Concepción', date(2025, 12, 8), 'fijo'),
            ('Navidad', date(2025, 12, 25), 'fijo'),
            
            # Lunes festivos (trasladados al lunes siguiente)
            ('Día de los Reyes Magos', date(2025, 1, 6), 'lunes_siguiente'),
            ('Día de San José', date(2025, 3, 24), 'lunes_siguiente'),
            ('San Pedro y San Pablo', date(2025, 6, 30), 'lunes_siguiente'),
            ('Asunción de la Virgen', date(2025, 8, 18), 'lunes_siguiente'),
            ('Día de la Raza', date(2025, 10, 13), 'lunes_siguiente'),
            ('Todos los Santos', date(2025, 11, 3), 'lunes_siguiente'),
            ('Independencia de Cartagena', date(2025, 11, 17), 'lunes_siguiente'),
            
            # Fechas religiosas variables (Semana Santa 2025)
            ('Jueves Santo', date(2025, 4, 17), 'religioso'),
            ('Viernes Santo', date(2025, 4, 18), 'religioso'),
            ('Ascensión del Señor', date(2025, 6, 2), 'religioso'),
            ('Corpus Christi', date(2025, 6, 23), 'religioso'),
            ('Sagrado Corazón de Jesús', date(2025, 6, 30), 'religioso'),
        ]
        
        festivos_creados = 0
        for nombre, fecha, tipo in festivos_2025:
            _, created = DiaFestivo.objects.get_or_create(
                fecha=fecha,
                nombre=nombre,
                defaults={
                    'tipo': tipo,
                    'es_nacional': True,
                    'activo': True,
                    'observaciones': f'Festivo nacional Colombia {fecha.year}'
                }
            )
            if created:
                festivos_creados += 1
        
        festivos_2025_total = DiaFestivo.objects.filter(fecha__year=2025).count()
        self.stdout.write(f'  ✅ {festivos_creados} nuevos festivos 2025 ({festivos_2025_total} total)')

    def crear_empleados_ejemplo(self, force=False):
        """Crea los empleados del centro de cómputo según el archivo Excel"""
        
        self.stdout.write('👥 Creando empleados del centro de cómputo...')
        
        if force:
            Empleado.objects.all().delete()
            self.stdout.write('  🗑️  Empleados existentes eliminados')
        
        empleados_data = [
            {
                'numero_empleado': '001',
                'nombres': 'Jaime Leonardo',
                'apellidos': 'Escobar Escobar',
                'cedula': '79220652',
                'cargo': 'operador_senior',
                'salario_base': Decimal('1800000.00'),
                'fecha_ingreso': date(2020, 1, 15),
                'telefono': '310-555-0001',
                'email': 'leonardo.escobar@empresa.com',
            },
            {
                'numero_empleado': '002',
                'nombres': 'Jefferson',
                'apellidos': 'Rodriguez Lopez',
                'cedula': '80069169',
                'cargo': 'operador_junior',
                'salario_base': Decimal('1600000.00'),
                'fecha_ingreso': date(2021, 3, 10),
                'telefono': '310-555-0002',
                'email': 'jefferson.rodriguez@empresa.com',
            },
            {
                'numero_empleado': '003',
                'nombres': 'Juan David',
                'apellidos': 'Mancipe Bejarano',
                'cedula': '1020738112',
                'cargo': 'operador_junior',
                'salario_base': Decimal('1600000.00'),
                'fecha_ingreso': date(2021, 6, 1),
                'telefono': '310-555-0003',
                'email': 'juan.mancipe@empresa.com',
            },
            {
                'numero_empleado': '004',
                'nombres': 'Mauricio',
                'apellidos': 'Garzón Real',
                'cedula': '80056882',
                'cargo': 'coordinador',
                'salario_base': Decimal('2200000.00'),
                'fecha_ingreso': date(2019, 8, 20),
                'telefono': '310-555-0004',
                'email': 'mauricio.garzon@empresa.com',
            },
            {
                'numero_empleado': '005',
                'nombres': 'Oscar Eduardo',
                'apellidos': 'Jaramillo Plaza',
                'cedula': '1013638917',
                'cargo': 'supervisor',
                'salario_base': Decimal('2500000.00'),
                'fecha_ingreso': date(2018, 2, 5),
                'telefono': '310-555-0005',
                'email': 'oscar.jaramillo@empresa.com',
            },
        ]
        
        empleados_creados = 0
        for emp_data in empleados_data:
            empleado, created = Empleado.objects.get_or_create(
                cedula=emp_data['cedula'],
                defaults=emp_data
            )
            if created:
                empleados_creados += 1
                # Calcular valor hora automáticamente
                empleado.calcular_valor_hora()
                empleado.save()
                self.stdout.write(f'     👤 {empleado.nombres} {empleado.apellidos} - ${empleado.valor_hora:,.0f}/hora')
        
        total_empleados = Empleado.objects.count()
        self.stdout.write(f'  ✅ {empleados_creados} nuevos empleados ({total_empleados} total)')
