# apps/reportes/pdf_generator.py
"""
Módulo para generación de reportes en PDF usando ReportLab
Sistema SACSBD - Heon Health On Line S.A.
"""

from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, Image, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Line
import logging

logger = logging.getLogger(__name__)


class NumberedCanvas(canvas.Canvas):
    """Canvas personalizado para agregar números de página"""
    
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
    
    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()
    
    def save(self):
        """Agregar números de página al guardar"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
    
    def draw_page_number(self, page_count):
        """Dibujar número de página en el pie"""
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.grey)
        page_num = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(
            self._pagesize[0] - 0.5 * inch,
            0.5 * inch,
            page_num
        )


class SACBDPDFGenerator:
    """Generador de PDFs para reportes SACSBD"""
    
    # Colores corporativos
    COLORS = {
        'primary': colors.HexColor('#1e3a5f'),      # Azul oscuro
        'secondary': colors.HexColor('#36b9cc'),    # Azul claro
        'success': colors.HexColor('#1cc88a'),      # Verde
        'warning': colors.HexColor('#f6c23e'),      # Amarillo
        'danger': colors.HexColor('#e74a3b'),       # Rojo
        'light': colors.HexColor('#f8f9fc'),        # Gris claro
        'dark': colors.HexColor('#5a5c69'),         # Gris oscuro
        'white': colors.white,
        'black': colors.black,
    }
    
    def __init__(self, title, subtitle="", orientation='portrait'):
        """
        Inicializar generador de PDF
        
        Args:
            title: Título del reporte
            subtitle: Subtítulo opcional
            orientation: 'portrait' o 'landscape'
        """
        self.title = title
        self.subtitle = subtitle
        self.orientation = orientation
        self.buffer = BytesIO()
        
        # Configurar tamaño de página
        if orientation == 'landscape':
            self.pagesize = landscape(letter)
        else:
            self.pagesize = letter
            
        # Crear documento
        self.doc = SimpleDocTemplate(
            self.buffer,
            pagesize=self.pagesize,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Estilos
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
        # Elementos del documento
        self.elements = []
        
    def _setup_custom_styles(self):
        """Configurar estilos personalizados"""
        # Título principal
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=self.COLORS['primary'],
            alignment=TA_CENTER,
            spaceAfter=6
        ))
        
        # Subtítulo
        self.styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=self.COLORS['dark'],
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        # Encabezado de sección
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=self.COLORS['primary'],
            spaceBefore=15,
            spaceAfter=10
        ))
        
        # Texto de estadísticas
        self.styles.add(ParagraphStyle(
            name='StatText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.COLORS['dark']
        ))
        
        # Texto pequeño
        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=self.COLORS['dark']
        ))
        
        # Pie de página
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        ))
        
    def add_header(self):
        """Agregar encabezado del reporte"""
        # Logo y título
        # Por ahora solo texto, se puede agregar logo después
        
        # Título
        self.elements.append(Paragraph(self.title, self.styles['ReportTitle']))
        
        # Subtítulo
        if self.subtitle:
            self.elements.append(Paragraph(self.subtitle, self.styles['ReportSubtitle']))
        
        # Fecha de generación
        fecha_gen = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        self.elements.append(Paragraph(
            f"Generado: {fecha_gen}",
            self.styles['SmallText']
        ))
        
        # Línea separadora
        self.elements.append(Spacer(1, 10))
        self.elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=self.COLORS['primary'],
            spaceBefore=5,
            spaceAfter=15
        ))
        
    def add_statistics_cards(self, stats_data):
        """
        Agregar tarjetas de estadísticas
        
        Args:
            stats_data: Lista de diccionarios con 'label', 'value', 'color' (opcional)
        """
        if not stats_data:
            return
            
        # Crear tabla de estadísticas
        num_cols = min(4, len(stats_data))
        
        # Preparar datos para la tabla
        header_row = []
        value_row = []
        
        for stat in stats_data[:num_cols]:
            header_row.append(Paragraph(
                f"<b>{stat.get('label', '')}</b>",
                self.styles['SmallText']
            ))
            value_row.append(Paragraph(
                f"<font size='14'><b>{stat.get('value', 0)}</b></font>",
                self.styles['StatText']
            ))
        
        # Crear tabla
        stats_table = Table(
            [header_row, value_row],
            colWidths=[self.pagesize[0] / num_cols - 0.5*inch] * num_cols
        )
        
        stats_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['light']),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.COLORS['dark']),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, self.COLORS['light']),
            ('BOX', (0, 0), (-1, -1), 1, self.COLORS['primary']),
        ]))
        
        self.elements.append(stats_table)
        self.elements.append(Spacer(1, 15))
        
    def add_section_header(self, text):
        """Agregar encabezado de sección"""
        self.elements.append(Paragraph(text, self.styles['SectionHeader']))
        
    def add_table(self, headers, data, col_widths=None, highlight_column=None):
        """
        Agregar tabla de datos
        
        Args:
            headers: Lista de encabezados de columna
            data: Lista de listas con los datos
            col_widths: Lista de anchos de columna (opcional)
            highlight_column: Índice de columna para resaltar según valor (opcional)
        """
        if not data:
            self.elements.append(Paragraph(
                "No hay datos para mostrar",
                self.styles['Normal']
            ))
            return
            
        # Preparar encabezados
        header_row = [Paragraph(f"<b>{h}</b>", self.styles['SmallText']) for h in headers]
        
        # Preparar datos
        table_data = [header_row]
        for row in data:
            formatted_row = []
            for i, cell in enumerate(row):
                # Convertir a string y limitar longitud
                cell_text = str(cell) if cell is not None else ''
                if len(cell_text) > 50:
                    cell_text = cell_text[:47] + '...'
                formatted_row.append(Paragraph(cell_text, self.styles['SmallText']))
            table_data.append(formatted_row)
        
        # Calcular anchos de columna si no se proporcionan
        if col_widths is None:
            available_width = self.pagesize[0] - 1*inch
            col_widths = [available_width / len(headers)] * len(headers)
        
        # Crear tabla
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Estilo base de la tabla
        style = [
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.COLORS['white']),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Cuerpo
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BOX', (0, 0), (-1, -1), 1, self.COLORS['primary']),
        ]
        
        # Filas alternadas
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                style.append(('BACKGROUND', (0, i), (-1, i), self.COLORS['light']))
        
        # Aplicar resaltado condicional si se especifica
        if highlight_column is not None and len(data) > 0:
            for i, row in enumerate(data, start=1):
                try:
                    value = float(row[highlight_column]) if row[highlight_column] else 0
                    if value >= 90:
                        style.append(('BACKGROUND', (highlight_column, i), (highlight_column, i), 
                                    colors.HexColor('#d4edda')))  # Verde claro
                    elif value >= 70:
                        style.append(('BACKGROUND', (highlight_column, i), (highlight_column, i), 
                                    colors.HexColor('#fff3cd')))  # Amarillo claro
                    else:
                        style.append(('BACKGROUND', (highlight_column, i), (highlight_column, i), 
                                    colors.HexColor('#f8d7da')))  # Rojo claro
                except (ValueError, IndexError, TypeError):
                    pass
        
        table.setStyle(TableStyle(style))
        self.elements.append(table)
        self.elements.append(Spacer(1, 15))
        
    def add_filters_info(self, filters):
        """
        Agregar información de filtros aplicados
        
        Args:
            filters: Diccionario con los filtros aplicados
        """
        if not filters:
            return
            
        filter_text = "Filtros aplicados: "
        filter_parts = []
        
        for key, value in filters.items():
            if value:
                filter_parts.append(f"{key}: {value}")
        
        if filter_parts:
            filter_text += " | ".join(filter_parts)
            self.elements.append(Paragraph(filter_text, self.styles['SmallText']))
            self.elements.append(Spacer(1, 10))
            
    def add_page_break(self):
        """Agregar salto de página"""
        self.elements.append(PageBreak())
        
    def add_spacer(self, height=10):
        """Agregar espacio vertical"""
        self.elements.append(Spacer(1, height))
        
    def add_text(self, text, style='Normal'):
        """Agregar texto simple"""
        self.elements.append(Paragraph(text, self.styles[style]))
        
    def generate(self):
        """Generar el PDF y devolver el buffer"""
        try:
            self.doc.build(
                self.elements,
                canvasmaker=NumberedCanvas
            )
            self.buffer.seek(0)
            return self.buffer
        except Exception as e:
            logger.error(f"Error generando PDF: {e}")
            raise


# =============================================================================
# Funciones auxiliares para generación de PDFs específicos
# =============================================================================

def generate_cumplimiento_pdf(resultados, estadisticas, fecha_inicio, fecha_fin):
    """
    Generar PDF de reporte de cumplimiento
    
    Args:
        resultados: Lista de diccionarios con datos de cumplimiento
        estadisticas: Diccionario con estadísticas
        fecha_inicio: Fecha de inicio del reporte
        fecha_fin: Fecha fin del reporte
    
    Returns:
        BytesIO buffer con el PDF
    """
    pdf = SACBDPDFGenerator(
        title="Reporte de Cumplimiento de Backups",
        subtitle="Sistema de Administración de Copias de Seguridad - SACSBD",
        orientation='landscape'
    )
    
    # Encabezado
    pdf.add_header()
    
    # Filtros
    pdf.add_filters_info({
        'Fecha Inicio': fecha_inicio,
        'Fecha Fin': fecha_fin
    })
    
    # Estadísticas
    if estadisticas:
        stats = [
            {'label': 'Total Registros', 'value': estadisticas.get('total_registros', 0)},
            {'label': 'Copias Ejecutadas', 'value': estadisticas.get('total_ejecutadas', 0)},
            {'label': 'Copias Programadas', 'value': estadisticas.get('total_programadas', 0)},
            {'label': '% Cumplimiento', 'value': f"{estadisticas.get('promedio_cumplimiento', 0):.2f}%"},
        ]
        pdf.add_statistics_cards(stats)
    
    # Tabla de datos
    pdf.add_section_header("Detalle de Cumplimiento por Base de Datos")
    
    headers = ['Servidor', 'Base de Datos', 'IP Servidor', 'Ejecutadas', 'Programadas', '% Cumplimiento']
    data = []
    for r in resultados:
        data.append([
            r.get('SERVIDOR', ''),
            r.get('DatabaseName', ''),
            r.get('IPSERVER', ''),
            r.get('TOTAL', 0),
            r.get('TOTALPROGRAM', 0),
            f"{r.get('PORCENTAJE', 0):.1f}%"
        ])
    
    # Anchos de columna personalizados
    col_widths = [1.5*inch, 2*inch, 1.2*inch, 1*inch, 1*inch, 1.2*inch]
    
    pdf.add_table(headers, data, col_widths, highlight_column=5)
    
    return pdf.generate()


def generate_jobs_pdf(resultados, stats, fecha_inicio, fecha_fin):
    """
    Generar PDF de reporte de Jobs de Backup
    
    Args:
        resultados: Lista de diccionarios con datos de jobs
        stats: Diccionario con estadísticas
        fecha_inicio: Fecha de inicio
        fecha_fin: Fecha fin
    
    Returns:
        BytesIO buffer con el PDF
    """
    pdf = SACBDPDFGenerator(
        title="Reporte de Jobs de Backup",
        subtitle="Estado y resultados de trabajos de respaldo",
        orientation='landscape'
    )
    
    # Encabezado
    pdf.add_header()
    
    # Filtros
    pdf.add_filters_info({
        'Fecha Inicio': fecha_inicio,
        'Fecha Fin': fecha_fin
    })
    
    # Estadísticas
    if stats:
        stats_cards = [
            {'label': 'Total Jobs', 'value': stats.get('total', 0)},
            {'label': 'Exitosos', 'value': stats.get('exitosos', 0)},
            {'label': 'Fallidos', 'value': stats.get('fallidos', 0)},
            {'label': '% Éxito', 'value': f"{stats.get('porcentaje_exito', 0):.1f}%"},
        ]
        pdf.add_statistics_cards(stats_cards)
    
    # Tabla de datos
    pdf.add_section_header("Detalle de Jobs de Backup")
    
    headers = ['Resultado', 'Servidor', 'IP', 'Fecha', 'Hora', 'Nombre Job', 'Paso', 'Mensaje']
    data = []
    
    # Limitar a 100 registros para no hacer el PDF muy grande
    for r in resultados[:100]:
        mensaje = str(r.get('MENSAJE', ''))[:50]  # Truncar mensaje
        data.append([
            r.get('RESULTADO', ''),
            r.get('SERVIDOR', ''),
            r.get('IPSERVER', ''),
            r.get('FECHA', ''),
            r.get('HORA', ''),
            r.get('NOMBRE_DEL_JOB', ''),
            r.get('PASO', ''),
            mensaje
        ])
    
    col_widths = [0.8*inch, 1*inch, 0.9*inch, 0.8*inch, 0.6*inch, 1.8*inch, 0.5*inch, 2*inch]
    
    pdf.add_table(headers, data, col_widths)
    
    if len(resultados) > 100:
        pdf.add_text(f"Nota: Se muestran los primeros 100 de {len(resultados)} registros.", 'SmallText')
    
    return pdf.generate()


def generate_estados_pdf(resultados, stats):
    """
    Generar PDF de reporte de Estados de Bases de Datos
    
    Args:
        resultados: Lista de diccionarios con estados
        stats: Diccionario con estadísticas
    
    Returns:
        BytesIO buffer con el PDF
    """
    pdf = SACBDPDFGenerator(
        title="Reporte de Estados de Bases de Datos",
        subtitle="Estado actual y configuración de todas las bases de datos",
        orientation='portrait'
    )
    
    # Encabezado
    pdf.add_header()
    
    # Estadísticas
    if stats:
        stats_cards = [
            {'label': 'Total BD', 'value': stats.get('total', 0)},
            {'label': 'Online', 'value': stats.get('online', 0)},
            {'label': 'Otros Estados', 'value': stats.get('otros', 0)},
            {'label': 'Servidores', 'value': stats.get('servidores', 0)},
        ]
        pdf.add_statistics_cards(stats_cards)
    
    # Tabla de datos
    pdf.add_section_header("Detalle de Estados")
    
    headers = ['Servidor', 'Base de Datos', 'IP Servidor', 'Fecha Creación', 'Estado', 'Tipo Estado']
    data = []
    
    for r in resultados:
        fecha = r.get('FECHA_DE_CREACION', '')
        if hasattr(fecha, 'strftime'):
            fecha = fecha.strftime('%d/%m/%Y %H:%M')
        data.append([
            r.get('SERVIDOR', ''),
            r.get('DATABASE_NAME', ''),
            r.get('IPSERVER', 'N/A'),
            str(fecha),
            r.get('ESTADO', ''),
            r.get('TIPO_ESTADO', '')
        ])
    
    col_widths = [1.2*inch, 1.5*inch, 1*inch, 1.2*inch, 0.8*inch, 1*inch]
    
    pdf.add_table(headers, data, col_widths)
    
    return pdf.generate()


def generate_disk_growth_pdf(resultados, estadisticas, fecha_inicio, fecha_fin):
    """
    Generar PDF de reporte de Crecimiento de Discos
    
    Args:
        resultados: Lista de diccionarios con datos de discos
        estadisticas: Diccionario con estadísticas
        fecha_inicio: Fecha inicio
        fecha_fin: Fecha fin
    
    Returns:
        BytesIO buffer con el PDF
    """
    pdf = SACBDPDFGenerator(
        title="Reporte de Crecimiento de Discos",
        subtitle="Análisis del espacio en disco de las bases de datos",
        orientation='landscape'
    )
    
    # Encabezado
    pdf.add_header()
    
    # Filtros
    pdf.add_filters_info({
        'Fecha Inicio': fecha_inicio,
        'Fecha Fin': fecha_fin
    })
    
    # Estadísticas
    if estadisticas:
        stats_cards = [
            {'label': 'Total Logs', 'value': estadisticas.get('total_registros', 0)},
            {'label': 'Espacio Usado (GB)', 'value': estadisticas.get('espacio_usado_gb', 0)},
            {'label': 'Espacio Libre (GB)', 'value': estadisticas.get('espacio_libre_gb', 0)},
            {'label': 'Discos Críticos', 'value': estadisticas.get('discos_criticos', 0)},
        ]
        pdf.add_statistics_cards(stats_cards)
    
    # Tabla de datos
    pdf.add_section_header("Detalle de Espacio en Disco")
    
    headers = ['Fecha/Hora', 'Servidor', 'Base de Datos', 'Archivo', 'Tamaño (MB)', 'Libre (MB)', '% Libre', 'Estado']
    data = []
    
    for r in resultados[:100]:
        fecha = r.get('LogDate', '')
        if hasattr(fecha, 'strftime'):
            fecha = fecha.strftime('%d/%m/%Y %H:%M')
        
        status = 'OK'
        if r.get('status_class') == 'danger':
            status = 'CRÍTICO'
        elif r.get('status_class') == 'warning':
            status = 'ADVERTENCIA'
            
        data.append([
            str(fecha),
            r.get('ServerIP', ''),
            r.get('DatabaseName', ''),
            r.get('FileName', ''),
            f"{r.get('FileSizeMB', 0):,.0f}",
            f"{r.get('DiskFreeMB', 0):,.0f}",
            f"{r.get('PorcentajeLibre', 0):.1f}%",
            status
        ])
    
    col_widths = [1.1*inch, 1*inch, 1.5*inch, 1.2*inch, 0.9*inch, 0.9*inch, 0.7*inch, 0.9*inch]
    
    pdf.add_table(headers, data, col_widths)
    
    if len(resultados) > 100:
        pdf.add_text(f"Nota: Se muestran los primeros 100 de {len(resultados)} registros.", 'SmallText')
    
    return pdf.generate()
