# apps/reportes/constants.py
"""
Constantes centralizadas para la aplicación de reportes SACSBD.

Este módulo contiene todas las constantes que estaban hardcodeadas
en views.py para mejorar la mantenibilidad y facilitar cambios futuros.
"""


class DateFormats:
    """Formatos de fecha utilizados en la aplicación"""
    INPUT = '%Y-%m-%d'           # Formato de entrada desde formularios (2024-01-15)
    OUTPUT = '%Y/%m/%d'          # Formato para procedimientos almacenados (2024/01/15)
    DISPLAY = '%d/%m/%Y'         # Formato para mostrar al usuario (15/01/2024)
    SQL = '%Y-%m-%d'             # Formato para consultas SQL (2024-01-15)
    TIMESTAMP = '%Y%m%d_%H%M%S'  # Formato para nombres de archivo (20240115_143022)
    DATETIME_DISPLAY = '%d/%m/%Y %H:%M:%S'  # Formato datetime completo


class DiskThresholds:
    """Umbrales de espacio en disco en MB"""
    CRITICAL_MB = 10240   # 10GB - Nivel crítico (danger)
    WARNING_MB = 51200    # 50GB - Nivel de advertencia (warning)


class StatusClasses:
    """Clases CSS de Bootstrap para estados"""
    SUCCESS = 'success'   # Verde - Todo bien
    WARNING = 'warning'   # Amarillo - Advertencia
    DANGER = 'danger'     # Rojo - Crítico
    INFO = 'info'         # Azul - Información
    PRIMARY = 'primary'   # Azul principal
    SECONDARY = 'secondary'  # Gris


class ExportHeaders:
    """
    Headers para exportación de reportes en diferentes formatos.
    Formato: (clave_diccionario, etiqueta_display)
    """

    CUMPLIMIENTO = [
        ('SERVIDOR', 'Servidor'),
        ('DatabaseName', 'Base de Datos'),
        ('IPSERVER', 'IP Servidor'),
        ('TOTAL', 'Copias Ejecutadas'),
        ('TOTALPROGRAM', 'Copias Programadas'),
        ('PORCENTAJE', '% Cumplimiento'),
    ]

    JOBS = [
        ('RESULTADO', 'Resultado'),
        ('SERVIDOR', 'Servidor'),
        ('IPSERVER', 'IP Servidor'),
        ('FECHA', 'Fecha'),
        ('HORA', 'Hora'),
        ('NOMBRE_DEL_JOB', 'Nombre del Job'),
        ('PASO', 'Paso'),
        ('MENSAJE', 'Mensaje'),
    ]

    ESTADOS_DB = [
        ('SERVIDOR', 'Servidor'),
        ('DATABASE_NAME', 'Base de Datos'),
        ('IPSERVER', 'IP Servidor'),
        ('ESTADO', 'Estado'),
        ('TIPO_ESTADO', 'Tipo Estado'),
        ('FECHA_DE_CREACION', 'Fecha de Registro'),
    ]

    DISK_GROWTH = [
        ('LogDate', 'Fecha/Hora'),
        ('ServerIP', 'Servidor IP'),
        ('DatabaseName', 'Base de Datos'),
        ('FileName', 'Archivo'),
        ('FileSizeMB', 'Tamaño (MB)'),
        ('DiskFreeMB', 'Espacio Libre (MB)'),
        ('PorcentajeLibre', '% Libre'),
        ('Estado', 'Estado'),
        ('FilePath', 'Ruta'),
    ]


class BackupTypes:
    """Tipos de backup y sus descripciones"""
    FULL = 'FULL'
    INCREMENTAL = 'INCREMENTAL'
    DIFF = 'DIFF'
    LOG = 'LOG'

    DESCRIPTIONS = {
        'FULL': 'Completo',
        'INCREMENTAL': 'Incremental',
        'DIFF': 'Diferencial',
        'LOG': 'Log de Transacciones'
    }


class JobStatuses:
    """Estados de jobs y palabras clave para identificarlos"""
    EXITOSO_KEYWORDS = ['exitoso', 'succeeded', 'success']
    FALLIDO_KEYWORDS = ['fallido', 'failed', 'error']
    ADVERTENCIA_KEYWORDS = ['advertencia', 'warning']


class ExportFileNames:
    """Patrones para nombres de archivos de exportación"""

    @staticmethod
    def cumplimiento(fecha_inicio, fecha_fin, extension):
        """Genera nombre de archivo para reporte de cumplimiento"""
        fecha_inicio_clean = fecha_inicio.replace('/', '-')
        fecha_fin_clean = fecha_fin.replace('/', '-')
        return f"cumplimiento_backup_{fecha_inicio_clean}_a_{fecha_fin_clean}.{extension}"

    @staticmethod
    def jobs(fecha_inicio, fecha_fin, extension):
        """Genera nombre de archivo para reporte de jobs"""
        return f"jobs_backup_{fecha_inicio}_a_{fecha_fin}.{extension}"

    @staticmethod
    def estados(extension):
        """Genera nombre de archivo para reporte de estados"""
        from datetime import datetime
        return f"estados_bd_{datetime.now().strftime(DateFormats.TIMESTAMP.replace('_', ''))[:8]}.{extension}"

    @staticmethod
    def disk_growth(fecha_inicio, fecha_fin, extension):
        """Genera nombre de archivo para reporte de disk growth"""
        return f"disk_growth_{fecha_inicio}_a_{fecha_fin}.{extension}"

    @staticmethod
    def timestamped(base_name, extension):
        """Genera nombre de archivo con timestamp"""
        from datetime import datetime
        timestamp = datetime.now().strftime(DateFormats.TIMESTAMP)
        return f"{base_name}_{timestamp}.{extension}"


class ExcelStyles:
    """Configuración de estilos para archivos Excel"""

    # Colores (formato hex sin #)
    HEADER_BG_COLOR = '4472C4'      # Azul para headers
    HEADER_FONT_COLOR = 'FFFFFF'    # Blanco para texto de headers
    EVEN_ROW_COLOR = 'D9E2F3'       # Azul claro para filas pares
    ODD_ROW_COLOR = 'FFFFFF'        # Blanco para filas impares
    TITLE_COLOR = '1F4E79'          # Azul oscuro para títulos
    DATE_COLOR = '666666'           # Gris para fechas

    # Tamaños
    HEADER_FONT_SIZE = 11
    TITLE_FONT_SIZE = 14
    DATE_FONT_SIZE = 10

    # Dimensiones
    MAX_COLUMN_WIDTH = 50           # Ancho máximo de columna
    MIN_COLUMN_WIDTH = 10           # Ancho mínimo de columna


class CSVConfig:
    """Configuración para archivos CSV"""
    DELIMITER = ';'                 # Delimitador para mejor compatibilidad con Excel
    ENCODING = 'utf-8'              # Encoding
    BOM = '\ufeff'                  # BOM para que Excel reconozca UTF-8


class DefaultDates:
    """Valores por defecto para rangos de fechas"""
    DIAS_ATRAS_DEFAULT = 30         # 30 días atrás por defecto
    DIAS_SEMANA = 7                 # 7 días para reportes semanales


class DatabaseStatusStates:
    """Estados de bases de datos"""
    ONLINE = 'ONLINE'
    OFFLINE = 'OFFLINE'
    RESTORING = 'RESTORING'
    RECOVERING = 'RECOVERING'
    SUSPECT = 'SUSPECT'


class ReportTitles:
    """Títulos de reportes para exportación"""
    CUMPLIMIENTO = "Reporte de Cumplimiento de Backups"
    JOBS = "Reporte de Jobs de Backup"
    ESTADOS_DB = "Reporte de Estado de Bases de Datos"
    DISK_GROWTH = "Reporte de Crecimiento de Discos"
    ARCHIVOS = "Reporte de Archivos de Backup"
    ULTIMOS = "Últimos Backups por Base de Datos"


class SheetNames:
    """Nombres de hojas para archivos Excel"""
    CUMPLIMIENTO = 'Cumplimiento'
    JOBS = 'Jobs'
    ESTADOS_DB = 'Estados BD'
    DISK_GROWTH = 'Crecimiento Discos'
    DATOS = 'Datos'  # Nombre genérico
