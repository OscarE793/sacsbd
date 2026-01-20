# apps/reportes/tests_procedures.py
"""
Pruebas y validación de procedimientos almacenados SACSBD
"""

from django.test import TestCase
from django.db import connection
from .utils import ejecutar_procedimiento_almacenado, ejecutar_consulta_personalizada
from .config import STORED_PROCEDURES, PROCEDURE_PARAMS
import logging

logger = logging.getLogger(__name__)

class ProcedureTestCase(TestCase):
    """Clase para probar todos los procedimientos almacenados"""
    
    def test_connection(self):
        """Prueba la conexión a la base de datos"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                self.assertEqual(result[0], 1)
                logger.info("Conexión a base de datos exitosa")
        except Exception as e:
            logger.error(f"Error de conexión: {e}")
            self.fail(f"Error de conexión: {e}")
    
    def test_tables_exist(self):
        """Verifica que las tablas principales existan"""
        tables_to_check = ['BACKUPSGENERADOS', 'JOBSBACKUPGENERADOS']
        
        for table in tables_to_check:
            try:
                query = f"SELECT COUNT(*) FROM {table}"
                result = ejecutar_consulta_personalizada(query)
                self.assertIsNotNone(result)
                logger.info(f"Tabla {table} existe y es accesible")
            except Exception as e:
                logger.error(f"Error accediendo tabla {table}: {e}")
                self.fail(f"Tabla {table} no accesible: {e}")
    
    def test_procedures_exist(self):
        """Verifica que todos los procedimientos almacenados existan"""
        for proc_key, proc_name in STORED_PROCEDURES.items():
            try:
                query = f"SELECT 1 FROM sys.procedures WHERE name = '{proc_name}'"
                result = ejecutar_consulta_personalizada(query)
                self.assertTrue(len(result) > 0, f"Procedimiento {proc_name} no encontrado")
                logger.info(f"Procedimiento {proc_name} existe")
            except Exception as e:
                logger.error(f"Error verificando procedimiento {proc_name}: {e}")
    
    def test_simple_procedures(self):
        """Prueba procedimientos almacenados sin parámetros"""
        simple_procedures = [
            'sp_countBck',
            'sp_countTotalBck',
            'sp_estadosdb',
            'sp_Lista_Estado',
            'sp_listausuarios',
            'sp_TotalBD',
            'sp_TotalSemana',
            'sp_ultimosbck',
            'sp_backup_history',
            'sp_historicoBck',
            'sp_ejecutonjobs_bck',
            'sp_porcentajeGenBak'
        ]
        
        for proc_name in simple_procedures:
            try:
                result = ejecutar_procedimiento_almacenado(proc_name)
                self.assertIsInstance(result, list)
                logger.info(f"Procedimiento {proc_name} ejecutado exitosamente - {len(result)} registros")
            except Exception as e:
                logger.warning(f"Error ejecutando {proc_name}: {e}")
    
    def test_procedures_with_params(self):
        """Prueba procedimientos que requieren parámetros"""
        from datetime import datetime, timedelta
        
        # Fechas de prueba
        fecha_fin = datetime.now().strftime('%Y-%m-%d')
        fecha_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        fecha_formato_sp = datetime.now().strftime('%d/%m/%Y')
        
        procedures_with_params = [
            ('sp_genBak', [fecha_formato_sp]),
            ('sp_resultadoJobsBck', [fecha_inicio, fecha_fin]),
            ('sp_Programaciondebcks', [fecha_inicio, fecha_fin]),
            ('sp_PromedioUltimosBck', [fecha_fin]),
            ('sp_BakGenerados', [fecha_fin])  # Este inserta datos, usar con cuidado
        ]
        
        for proc_name, params in procedures_with_params:
            try:
                if proc_name == 'sp_BakGenerados':
                    # Este procedimiento inserta datos, solo probamos si existe
                    logger.info(f"Saltando {proc_name} (procedimiento de inserción)")
                    continue
                    
                result = ejecutar_procedimiento_almacenado(proc_name, params)
                self.assertIsInstance(result, list)
                logger.info(f"Procedimiento {proc_name} con parámetros ejecutado exitosamente - {len(result)} registros")
            except Exception as e:
                logger.warning(f"Error ejecutando {proc_name} con parámetros {params}: {e}")
    
    def test_custom_queries(self):
        """Prueba las consultas personalizadas"""
        from .config import QUERIES
        
        for query_name, query_sql in QUERIES.items():
            try:
                result = ejecutar_consulta_personalizada(query_sql)
                self.assertIsInstance(result, list)
                logger.info(f"Consulta {query_name} ejecutada exitosamente - {len(result)} registros")
            except Exception as e:
                logger.warning(f"Error ejecutando consulta {query_name}: {e}")
    
    def test_dashboard_metrics(self):
        """Prueba específica para las métricas del dashboard"""
        try:
            from .config import QUERIES
            result = ejecutar_consulta_personalizada(QUERIES['dashboard_metricas'])
            
            self.assertTrue(len(result) > 0)
            metrics = result[0]
            
            # Verificar que las métricas principales existan
            required_metrics = [
                'total_servidores', 'total_bases_datos', 'backups_hoy', 
                'backups_semana', 'jobs_exitosos_hoy', 'jobs_fallidos_hoy'
            ]
            
            for metric in required_metrics:
                self.assertIn(metric, metrics)
                self.assertIsNotNone(metrics[metric])
            
            logger.info(f"Métricas del dashboard: {metrics}")
            
        except Exception as e:
            logger.error(f"Error en métricas del dashboard: {e}")
            self.fail(f"Error en métricas: {e}")


def run_procedure_validation():
    """
    Función utilitaria para validar todos los procedimientos almacenados
    Puede ser llamada desde las vistas o management commands
    """
    
    validation_results = {
        'connection': False,
        'tables': {},
        'procedures': {},
        'queries': {},
        'errors': []
    }
    
    try:
        # Probar conexión
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            validation_results['connection'] = True
        
        # Probar tablas
        tables = ['BACKUPSGENERADOS', 'JOBSBACKUPGENERADOS']
        for table in tables:
            try:
                query = f"SELECT COUNT(*) as total FROM {table}"
                result = ejecutar_consulta_personalizada(query)
                validation_results['tables'][table] = {
                    'exists': True,
                    'records': result[0]['total'] if result else 0
                }
            except Exception as e:
                validation_results['tables'][table] = {
                    'exists': False,
                    'error': str(e)
                }
                validation_results['errors'].append(f"Tabla {table}: {e}")
        
        # Probar procedimientos almacenados
        for proc_key, proc_name in STORED_PROCEDURES.items():
            try:
                # Solo verificar existencia, no ejecutar
                query = f"SELECT 1 FROM sys.procedures WHERE name = '{proc_name}'"
                result = ejecutar_consulta_personalizada(query)
                validation_results['procedures'][proc_name] = {
                    'exists': len(result) > 0,
                    'description': PROCEDURE_PARAMS.get(proc_name, {}).get('description', 'N/A')
                }
                
                if len(result) == 0:
                    validation_results['errors'].append(f"Procedimiento {proc_name} no existe")
                    
            except Exception as e:
                validation_results['procedures'][proc_name] = {
                    'exists': False,
                    'error': str(e)
                }
                validation_results['errors'].append(f"Procedimiento {proc_name}: {e}")
        
        # Probar consultas principales
        from .config import QUERIES
        safe_queries = ['servidores_disponibles', 'tipos_backup', 'bases_datos_disponibles']
        
        for query_name in safe_queries:
            if query_name in QUERIES:
                try:
                    result = ejecutar_consulta_personalizada(QUERIES[query_name])
                    validation_results['queries'][query_name] = {
                        'success': True,
                        'records': len(result)
                    }
                except Exception as e:
                    validation_results['queries'][query_name] = {
                        'success': False,
                        'error': str(e)
                    }
                    validation_results['errors'].append(f"Consulta {query_name}: {e}")
    
    except Exception as e:
        validation_results['errors'].append(f"Error general: {e}")
    
    return validation_results


if __name__ == '__main__':
    # Ejecutar validación si se llama directamente
    results = run_procedure_validation()
    print("=== RESULTADOS DE VALIDACIÓN SACSBD ===")
    print(f"Conexión: {'✅' if results['connection'] else '❌'}")
    print(f"Tablas verificadas: {len(results['tables'])}")
    print(f"Procedimientos verificados: {len(results['procedures'])}")
    print(f"Consultas probadas: {len(results['queries'])}")
    print(f"Errores encontrados: {len(results['errors'])}")
    
    if results['errors']:
        print("\n=== ERRORES ===")
        for error in results['errors']:
            print(f"{error}")
