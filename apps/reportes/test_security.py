# apps/reportes/test_security.py
"""
Tests de seguridad para validar protecciones contra SQL injection
y otras vulnerabilidades.
"""
from django.test import TestCase
from .utils_secure import (
    validar_nombre_servidor,
    validar_nombre_base_datos,
    sanitizar_input_like,
    construir_filtro_seguro,
    ALLOWED_STORED_PROCEDURES,
    ejecutar_procedimiento_almacenado_seguro
)


class ValidacionInputsTest(TestCase):
    """Tests para validación de inputs"""

    def test_validar_nombre_servidor_valido(self):
        """Nombres de servidor válidos deben pasar"""
        nombres_validos = [
            'SERVER01',
            'srv-backup',
            'db.server.local',
            'srv_prod_01',
            '192.168.1.1',
            'srv-test.domain.com'
        ]

        for nombre in nombres_validos:
            with self.subTest(nombre=nombre):
                self.assertTrue(validar_nombre_servidor(nombre))

    def test_validar_nombre_servidor_invalido(self):
        """Nombres de servidor con caracteres peligrosos deben fallar"""
        nombres_invalidos = [
            "srv'; DROP TABLE BACKUPSGENERADOS; --",
            "srv OR 1=1",
            "srv<script>",
            "srv; DELETE FROM users",
            "srv' UNION SELECT * FROM sys.tables--"
        ]

        for nombre in nombres_invalidos:
            with self.subTest(nombre=nombre):
                with self.assertRaises(ValueError):
                    validar_nombre_servidor(nombre)

    def test_validar_nombre_servidor_muy_largo(self):
        """Nombres excesivamente largos deben fallar"""
        nombre_largo = 'A' * 101
        with self.assertRaises(ValueError):
            validar_nombre_servidor(nombre_largo)

    def test_validar_nombre_servidor_vacio(self):
        """String vacío debe ser válido (sin filtro)"""
        self.assertTrue(validar_nombre_servidor(''))
        self.assertTrue(validar_nombre_servidor(None))

    def test_validar_nombre_base_datos_valido(self):
        """Nombres de BD válidos deben pasar"""
        nombres_validos = [
            'SACSBD',
            'DB_PROD',
            'test_database',
            'db$temp',
            '#tempdb',
            '@local'
        ]

        for nombre in nombres_validos:
            with self.subTest(nombre=nombre):
                self.assertTrue(validar_nombre_base_datos(nombre))

    def test_validar_nombre_base_datos_invalido(self):
        """Nombres de BD con caracteres peligrosos deben fallar"""
        nombres_invalidos = [
            "db'; DROP TABLE users; --",
            "db OR 1=1",
            "db-test",  # Guión no permitido en nombres de BD
            "db.name",  # Punto no permitido
        ]

        for nombre in nombres_invalidos:
            with self.subTest(nombre=nombre):
                with self.assertRaises(ValueError):
                    validar_nombre_base_datos(nombre)


class SanitizacionTest(TestCase):
    """Tests para sanitización de inputs"""

    def test_sanitizar_input_like_basico(self):
        """Caracteres especiales de LIKE deben ser escapados"""
        tests = [
            ('test%', 'test[%]'),
            ('test_', 'test[_]'),
            ('test[', 'test[[]'),
            ('test%_[', 'test[%][_][[]'),
        ]

        for input_val, esperado in tests:
            with self.subTest(input=input_val):
                resultado = sanitizar_input_like(input_val)
                self.assertEqual(resultado, esperado)

    def test_sanitizar_input_like_vacio(self):
        """Valores vacíos deben retornarse sin cambios"""
        self.assertEqual(sanitizar_input_like(''), '')
        self.assertEqual(sanitizar_input_like(None), None)

    def test_sanitizar_input_like_normal(self):
        """Texto con guión bajo debe escaparse (es wildcard en LIKE)"""
        texto = "SRV01_PROD"
        # El _ debe escaparse porque es wildcard en LIKE
        self.assertEqual(sanitizar_input_like(texto), "SRV01[_]PROD")


class ConstruccionFiltrosTest(TestCase):
    """Tests para construcción segura de filtros"""

    def test_construir_filtro_seguro_basico(self):
        """Construcción básica de filtros debe funcionar"""
        query_base = "SELECT * FROM tabla WHERE 1=1"
        filtros = {'servidor': 'SRV01'}
        params = []

        query_final = construir_filtro_seguro(query_base, filtros, params)

        self.assertIn("AND servidor LIKE %s", query_final)
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0], '%SRV01%')

    def test_construir_filtro_seguro_multiples(self):
        """Múltiples filtros deben agregarse correctamente"""
        query_base = "SELECT * FROM tabla WHERE 1=1"
        filtros = {
            'servidor': 'SRV01',
            'estado': 'ONLINE'
        }
        params = []

        query_final = construir_filtro_seguro(query_base, filtros, params)

        self.assertEqual(len(params), 2)
        self.assertIn('%SRV01%', params)
        self.assertIn('%ONLINE%', params)

    def test_construir_filtro_seguro_sanitiza(self):
        """Valores con caracteres especiales deben sanitizarse"""
        query_base = "SELECT * FROM tabla WHERE 1=1"
        filtros = {'servidor': 'SRV%01'}  # % debe escaparse
        params = []

        construir_filtro_seguro(query_base, filtros, params)

        # El % debe estar escapado en el parámetro
        self.assertEqual(params[0], '%SRV[%]01%')

    def test_construir_filtro_seguro_campo_no_permitido(self):
        """Campos no permitidos deben ser ignorados"""
        query_base = "SELECT * FROM tabla WHERE 1=1"
        filtros = {
            'servidor': 'SRV01',
            'campo_malicioso': 'valor'  # Este campo no está en la whitelist
        }
        params = []

        query_final = construir_filtro_seguro(query_base, filtros, params)

        # Solo debe haber 1 parámetro (el campo malicioso se ignora)
        self.assertEqual(len(params), 1)
        self.assertNotIn('campo_malicioso', query_final)

    def test_construir_filtro_seguro_valores_vacios(self):
        """Filtros con valores vacíos deben ser ignorados"""
        query_base = "SELECT * FROM tabla WHERE 1=1"
        filtros = {
            'servidor': '',
            'estado': None
        }
        params = []

        query_final = construir_filtro_seguro(query_base, filtros, params)

        # No debe haber parámetros agregados
        self.assertEqual(len(params), 0)
        self.assertEqual(query_final, query_base)


class WhitelistSPTest(TestCase):
    """Tests para whitelist de procedimientos almacenados"""

    def test_whitelist_contiene_sps_conocidos(self):
        """Whitelist debe contener los SPs que usamos"""
        sps_requeridos = [
            'sp_Programaciondebcks',
            'sp_resultadoJobsBck',
            'sp_ultimosbck',
            'sp_DashboardMetrics',
            'sp_MonitorDatabaseStatus',
        ]

        for sp in sps_requeridos:
            with self.subTest(sp=sp):
                self.assertIn(sp, ALLOWED_STORED_PROCEDURES)

    def test_ejecutar_sp_no_permitido_falla(self):
        """Intentar ejecutar SP no permitido debe fallar"""
        with self.assertRaises(ValueError) as context:
            ejecutar_procedimiento_almacenado_seguro('sp_malicioso', [])

        self.assertIn("no permitido", str(context.exception))

    def test_ejecutar_sp_con_sql_injection_falla(self):
        """Intentar inyectar SQL en nombre de SP debe fallar"""
        intentos_maliciosos = [
            "sp_Programaciondebcks; DROP TABLE users; --",
            "sp_Programaciondebcks' OR '1'='1",
            "sp_Programaciondebcks'; DELETE FROM backups; --"
        ]

        for intento in intentos_maliciosos:
            with self.subTest(intento=intento):
                with self.assertRaises(ValueError):
                    ejecutar_procedimiento_almacenado_seguro(intento, [])


class IntegracionSeguridadTest(TestCase):
    """Tests de integración de seguridad"""

    def test_pipeline_completo_validacion(self):
        """Pipeline completo de validación debe funcionar"""
        # Simular input del usuario
        servidor_usuario = "SRV%01"  # Usuario intenta usar % en LIKE

        # 1. Validar formato (el % no es válido en nombre de servidor)
        # Nota: En uso real, se rechazaría por validar_nombre_servidor()
        # Para este test, simulamos sanitizar un valor que ya pasó validación

        # 2. Sanitizar
        servidor_sanitizado = sanitizar_input_like(servidor_usuario)

        # 3. Verificar que está escapado
        self.assertEqual(servidor_sanitizado, "SRV[%]01")

        # 4. Construir filtro (sanitiza de nuevo dentro de la función)
        query_base = "SELECT * FROM servidores WHERE 1=1"
        filtros = {'servidor': servidor_usuario}  # Usar original, no sanitizado
        params = []

        query_final = construir_filtro_seguro(query_base, filtros, params)

        # 5. Verificar resultado seguro
        self.assertIn("AND servidor LIKE %s", query_final)
        # El valor en params ya debe estar sanitizado
        self.assertIn('[%]', params[0])  # Verificar que el % está escapado

    def test_prevencion_sql_injection_basico(self):
        """Intento básico de SQL injection debe ser prevenido"""
        # Intento de inyección
        servidor_malicioso = "'; DROP TABLE users; --"

        # Debe fallar la validación
        with self.assertRaises(ValueError):
            validar_nombre_servidor(servidor_malicioso)

    def test_prevencion_sql_injection_union(self):
        """Intento de UNION SELECT debe ser prevenido"""
        servidor_malicioso = "' UNION SELECT * FROM sys.tables--"

        with self.assertRaises(ValueError):
            validar_nombre_servidor(servidor_malicioso)
