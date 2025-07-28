# apps/reportes/management/commands/validate_procedures.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.reportes.tests_procedures import run_procedure_validation
from apps.reportes.config import STORED_PROCEDURES, REPORTES_CONFIG
import json

class Command(BaseCommand):
    help = 'Valida todos los procedimientos almacenados y consultas de SACSBD'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Muestra información detallada de cada procedimiento'
        )
        parser.add_argument(
            '--export',
            type=str,
            help='Exporta los resultados a un archivo JSON'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Iniciando validación de procedimientos almacenados SACSBD...')
        )
        
        # Ejecutar validación
        results = run_procedure_validation()
        
        # Agregar timestamp
        results['validation_timestamp'] = timezone.now().isoformat()
        
        # Mostrar resultados en consola
        self._display_results(results, options.get('detailed', False))
        
        # Exportar si se solicita
        if options.get('export'):
            self._export_results(results, options['export'])
        
        # Resumen final
        total_errors = len(results['errors'])
        if total_errors == 0:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Validación completada exitosamente sin errores')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Validación completada con {total_errors} errores')
            )
    
    def _display_results(self, results, detailed=False):
        """Muestra los resultados de la validación"""
        
        # Estado de conexión
        connection_status = '✅ Conectado' if results['connection'] else '❌ Sin conexión'
        self.stdout.write(f"\n📡 Conexión a BD: {connection_status}")
        
        # Estado de tablas
        self.stdout.write(f"\n📊 Tablas principales:")
        for table_name, table_info in results['tables'].items():
            if table_info['exists']:
                records = table_info.get('records', 0)
                self.stdout.write(f"  ✅ {table_name} - {records:,} registros")
            else:
                error = table_info.get('error', 'No accesible')
                self.stdout.write(f"  ❌ {table_name} - {error}")
        
        # Estado de procedimientos
        self.stdout.write(f"\n⚙️ Procedimientos almacenados:")
        total_procedures = len(results['procedures'])
        existing_procedures = sum(1 for p in results['procedures'].values() if p.get('exists', False))
        
        self.stdout.write(f"  Total: {total_procedures} | Existentes: {existing_procedures}")
        
        if detailed:
            for proc_name, proc_info in results['procedures'].items():
                if proc_info.get('exists', False):
                    desc = proc_info.get('description', 'Sin descripción')
                    self.stdout.write(f"    ✅ {proc_name} - {desc}")
                else:
                    error = proc_info.get('error', 'No encontrado')
                    self.stdout.write(f"    ❌ {proc_name} - {error}")
        
        # Estado de consultas
        self.stdout.write(f"\n🔍 Consultas personalizadas:")
        total_queries = len(results['queries'])
        successful_queries = sum(1 for q in results['queries'].values() if q.get('success', False))
        
        self.stdout.write(f"  Total: {total_queries} | Exitosas: {successful_queries}")
        
        if detailed:
            for query_name, query_info in results['queries'].items():
                if query_info.get('success', False):
                    records = query_info.get('records', 0)
                    self.stdout.write(f"    ✅ {query_name} - {records} registros")
                else:
                    error = query_info.get('error', 'Error desconocido')
                    self.stdout.write(f"    ❌ {query_name} - {error}")
        
        # Errores encontrados
        if results['errors']:
            self.stdout.write(f"\n🚨 Errores encontrados ({len(results['errors'])}):")
            for i, error in enumerate(results['errors'], 1):
                self.stdout.write(f"  {i}. {error}")
        
        # Información adicional
        self.stdout.write(f"\n📋 Información del sistema:")
        self.stdout.write(f"  • Procedimientos configurados: {len(STORED_PROCEDURES)}")
        self.stdout.write(f"  • Reportes disponibles: {len(REPORTES_CONFIG)}")
        self.stdout.write(f"  • Timestamp: {results['validation_timestamp']}")
    
    def _export_results(self, results, filename):
        """Exporta los resultados a un archivo JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            self.stdout.write(
                self.style.SUCCESS(f'📄 Resultados exportados a: {filename}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error exportando resultados: {e}')
            )
    
    def _get_procedure_recommendations(self, results):
        """Genera recomendaciones basadas en los resultados"""
        recommendations = []
        
        if not results['connection']:
            recommendations.append("Verificar la configuración de conexión a la base de datos")
        
        missing_procedures = [
            name for name, info in results['procedures'].items() 
            if not info.get('exists', False)
        ]
        
        if missing_procedures:
            recommendations.append(f"Crear o verificar los siguientes procedimientos: {', '.join(missing_procedures)}")
        
        failed_queries = [
            name for name, info in results['queries'].items() 
            if not info.get('success', False)
        ]
        
        if failed_queries:
            recommendations.append(f"Revisar las siguientes consultas: {', '.join(failed_queries)}")
        
        return recommendations
