# apps/reportes/test_refactoring.py
"""
Tests para validar la refactorización de Fase 1
"""
from django.test import TestCase
from .data_converters import (
    convert_cumplimiento_result,
    convert_jobs_result,
    normalize_results,
    format_porcentaje,
    format_cumplimiento_results
)
from .constants import (
    DateFormats,
    ExportHeaders,
    ExportFileNames,
    SheetNames,
    ReportTitles
)


class DataConvertersTest(TestCase):
    """Tests para data_converters.py"""

    def test_convert_cumplimiento_result_tuple(self):
        """Verificar conversión de tupla de cumplimiento"""
        tupla = ('SRV01', 'DB_TEST', '192.168.1.1', 25, 30, 83.33)
        resultado = convert_cumplimiento_result(tupla)

        self.assertIsNotNone(resultado)
        self.assertEqual(resultado['SERVIDOR'], 'SRV01')
        self.assertEqual(resultado['DatabaseName'], 'DB_TEST')
        self.assertEqual(resultado['IPSERVER'], '192.168.1.1')
        self.assertEqual(resultado['TOTAL'], 25)
        self.assertEqual(resultado['TOTALPROGRAM'], 30)
        self.assertEqual(resultado['PORCENTAJE'], 83.33)

    def test_convert_cumplimiento_result_invalid(self):
        """Verificar que retorna None para datos inválidos"""
        resultado = convert_cumplimiento_result(('solo', 'dos'))
        self.assertIsNone(resultado)

        resultado = convert_cumplimiento_result(None)
        self.assertIsNone(resultado)

    def test_convert_jobs_result_tuple(self):
        """Verificar conversión de tupla de jobs"""
        tupla = ('Exitoso', 'SRV01', '192.168.1.1', '01/01/2024', '10:30:00', 'BackupJob1', '1', 'OK')
        resultado = convert_jobs_result(tupla)

        self.assertIsNotNone(resultado)
        self.assertEqual(resultado['RESULTADO'], 'Exitoso')
        self.assertEqual(resultado['SERVIDOR'], 'SRV01')
        self.assertEqual(resultado['NOMBRE_DEL_JOB'], 'BackupJob1')

    def test_convert_jobs_result_with_nulls(self):
        """Verificar conversión de jobs con valores None"""
        tupla = (None, 'SRV01', None, '', None, 'Job1', None, None)
        resultado = convert_jobs_result(tupla)

        self.assertIsNotNone(resultado)
        self.assertEqual(resultado['RESULTADO'], '')
        self.assertEqual(resultado['SERVIDOR'], 'SRV01')
        self.assertEqual(resultado['IPSERVER'], '')

    def test_normalize_results_already_dict(self):
        """Verificar que normalize_results mantiene diccionarios sin cambios"""
        datos = [
            {'SERVIDOR': 'SRV01', 'DatabaseName': 'DB01'},
            {'SERVIDOR': 'SRV02', 'DatabaseName': 'DB02'}
        ]
        resultado = normalize_results(datos, convert_cumplimiento_result)

        self.assertEqual(len(resultado), 2)
        self.assertEqual(resultado[0]['SERVIDOR'], 'SRV01')

    def test_normalize_results_tuples(self):
        """Verificar conversión de lista de tuplas"""
        tuplas = [
            ('SRV01', 'DB01', '192.168.1.1', 25, 30, 83.33),
            ('SRV02', 'DB02', '192.168.1.2', 28, 30, 93.33)
        ]
        resultado = normalize_results(tuplas, convert_cumplimiento_result)

        self.assertEqual(len(resultado), 2)
        self.assertEqual(resultado[0]['SERVIDOR'], 'SRV01')
        self.assertEqual(resultado[1]['SERVIDOR'], 'SRV02')

    def test_normalize_results_empty(self):
        """Verificar manejo de lista vacía"""
        resultado = normalize_results([], convert_cumplimiento_result)
        self.assertEqual(resultado, [])

    def test_format_porcentaje(self):
        """Verificar formateo de porcentajes"""
        self.assertEqual(format_porcentaje(83.3333), '83.33%')
        self.assertEqual(format_porcentaje(100), '100.00%')
        self.assertEqual(format_porcentaje(0), '0.00%')
        self.assertEqual(format_porcentaje(None), '0.00%')

    def test_format_cumplimiento_results(self):
        """Verificar formateo de resultados de cumplimiento"""
        datos = [
            {'SERVIDOR': 'SRV01', 'PORCENTAJE': 83.33},
            {'SERVIDOR': 'SRV02', 'PORCENTAJE': 100.0}
        ]
        resultado = format_cumplimiento_results(datos)

        self.assertEqual(resultado[0]['PORCENTAJE'], '83.33%')
        self.assertEqual(resultado[1]['PORCENTAJE'], '100.00%')


class ConstantsTest(TestCase):
    """Tests para constants.py"""

    def test_date_formats_defined(self):
        """Verificar que los formatos de fecha están definidos"""
        self.assertEqual(DateFormats.INPUT, '%Y-%m-%d')
        self.assertEqual(DateFormats.OUTPUT, '%Y/%m/%d')
        self.assertEqual(DateFormats.SQL, '%Y-%m-%d')

    def test_export_headers_cumplimiento(self):
        """Verificar headers de exportación de cumplimiento"""
        headers = ExportHeaders.CUMPLIMIENTO

        self.assertIsInstance(headers, list)
        self.assertTrue(len(headers) > 0)
        self.assertEqual(headers[0][0], 'SERVIDOR')
        self.assertEqual(headers[0][1], 'Servidor')

    def test_export_headers_jobs(self):
        """Verificar headers de exportación de jobs"""
        headers = ExportHeaders.JOBS

        self.assertIsInstance(headers, list)
        self.assertTrue(len(headers) >= 8)
        # Verificar que tiene las columnas esperadas
        keys = [h[0] for h in headers]
        self.assertIn('RESULTADO', keys)
        self.assertIn('SERVIDOR', keys)
        self.assertIn('NOMBRE_DEL_JOB', keys)

    def test_export_filenames_timestamped(self):
        """Verificar generación de nombres de archivo con timestamp"""
        filename = ExportFileNames.timestamped('test_report', 'xlsx')

        self.assertTrue(filename.startswith('test_report_'))
        self.assertTrue(filename.endswith('.xlsx'))

    def test_sheet_names_defined(self):
        """Verificar que los nombres de hojas están definidos"""
        self.assertEqual(SheetNames.CUMPLIMIENTO, 'Cumplimiento')
        self.assertEqual(SheetNames.JOBS, 'Jobs')
        self.assertEqual(SheetNames.ESTADOS_DB, 'Estados BD')

    def test_report_titles_defined(self):
        """Verificar que los títulos de reporte están definidos"""
        self.assertTrue(len(ReportTitles.CUMPLIMIENTO) > 0)
        self.assertTrue(len(ReportTitles.JOBS) > 0)
        self.assertTrue(len(ReportTitles.ESTADOS_DB) > 0)


class IntegrationTest(TestCase):
    """Tests de integración para verificar que todo funciona junto"""

    def test_full_conversion_pipeline(self):
        """Verificar pipeline completo de conversión y formateo"""
        # Simular datos de SP como tuplas
        datos_sp = [
            ('SRV01', 'DB_PROD', '192.168.1.1', 28, 30, 93.33),
            ('SRV02', 'DB_TEST', '192.168.1.2', 25, 30, 83.33)
        ]

        # Normalizar
        resultados = normalize_results(datos_sp, convert_cumplimiento_result)

        # Verificar conversión
        self.assertEqual(len(resultados), 2)
        self.assertIsInstance(resultados[0], dict)

        # Formatear porcentajes
        resultados = format_cumplimiento_results(resultados)

        # Verificar formateo
        self.assertEqual(resultados[0]['PORCENTAJE'], '93.33%')
        self.assertEqual(resultados[1]['PORCENTAJE'], '83.33%')

        # Verificar que se mantiene toda la información
        self.assertEqual(resultados[0]['SERVIDOR'], 'SRV01')
        self.assertEqual(resultados[0]['DatabaseName'], 'DB_PROD')
        self.assertEqual(resultados[0]['TOTAL'], 28)
