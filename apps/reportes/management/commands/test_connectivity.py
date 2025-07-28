# apps/reportes/management/commands/test_connectivity.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.reportes.utils import ejecutar_consulta_personalizada

class Command(BaseCommand):
    help = 'Prueba la conectividad básica del sistema SACSBD'
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Iniciando pruebas de conectividad SACSBD...\n')
        )
        
        # 1. Probar conexión básica
        self.stdout.write('1. Probando conexión a base de datos...')
        try:
            result = ejecutar_consulta_personalizada("SELECT 1 as test")
            if result and result[0].get('test') == 1:
                self.stdout.write(self.style.SUCCESS('   ✅ Conexión exitosa'))
            else:
                self.stdout.write(self.style.ERROR('   ❌ Conexión fallida'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error de conexión: {e}'))
            return
        
        # 2. Probar tablas principales
        self.stdout.write('\n2. Probando acceso a tablas principales...')
        tables = ['BACKUPSGENERADOS', 'JOBSBACKUPGENERADOS']
        
        for table in tables:
            try:
                result = ejecutar_consulta_personalizada(f"SELECT COUNT(*) as total FROM {table}")
                total = result[0]['total'] if result else 0
                self.stdout.write(self.style.SUCCESS(f'   ✅ {table}: {total:,} registros'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ {table}: {e}'))
        
        # 3. Probar consultas básicas
        self.stdout.write('\n3. Probando consultas básicas...')
        queries = {
            'Servidores distintos': "SELECT COUNT(DISTINCT SERVIDOR) as total FROM BACKUPSGENERADOS WHERE SERVIDOR IS NOT NULL",
            'Bases de datos distintas': "SELECT COUNT(DISTINCT DatabaseName) as total FROM BACKUPSGENERADOS WHERE DatabaseName IS NOT NULL",
            'Tipos de backup': "SELECT COUNT(DISTINCT TYPE) as total FROM BACKUPSGENERADOS WHERE TYPE IS NOT NULL",
            'Jobs en última semana': "SELECT COUNT(*) as total FROM JOBSBACKUPGENERADOS WHERE FECHA_Y_HORA_INICIO >= DATEADD(day, -7, GETDATE())"
        }
        
        for desc, query in queries.items():
            try:
                result = ejecutar_consulta_personalizada(query)
                total = result[0]['total'] if result else 0
                self.stdout.write(self.style.SUCCESS(f'   ✅ {desc}: {total}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ {desc}: {e}'))
        
        # 4. Probar procedimientos almacenados simples
        self.stdout.write('\n4. Probando procedimientos almacenados...')
        from apps.reportes.utils import ejecutar_procedimiento_almacenado
        
        simple_procedures = ['sp_countTotalBck', 'sp_TotalBD', 'sp_estadosdb']
        
        for proc in simple_procedures:
            try:
                result = ejecutar_procedimiento_almacenado(proc)
                count = len(result) if result else 0
                self.stdout.write(self.style.SUCCESS(f'   ✅ {proc}: {count} registros'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠️ {proc}: {e}'))
        
        # 5. Probar consultas del dashboard
        self.stdout.write('\n5. Probando consultas del dashboard...')
        try:
            from apps.reportes.config import QUERIES
            result = ejecutar_consulta_personalizada(QUERIES['dashboard_metricas'])
            if result:
                metrics = result[0]
                self.stdout.write(self.style.SUCCESS('   ✅ Métricas del dashboard:'))
                self.stdout.write(f'      • Servidores: {metrics.get("total_servidores", 0)}')
                self.stdout.write(f'      • Bases de datos: {metrics.get("total_bases_datos", 0)}')
                self.stdout.write(f'      • Backups hoy: {metrics.get("backups_hoy", 0)}')
                self.stdout.write(f'      • Backups semana: {metrics.get("backups_semana", 0)}')
            else:
                self.stdout.write(self.style.WARNING('   ⚠️ Sin datos en métricas'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error en métricas: {e}'))
        
        # Resumen final
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Pruebas completadas - {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
        )
        self.stdout.write(
            self.style.HTTP_INFO('\n📋 Para probar desde la web: http://127.0.0.1:8000/reportes/test/')
        )
