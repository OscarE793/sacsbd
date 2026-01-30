# apps/horas_extras/admin.py - VERSIÓN SIMPLIFICADA
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import TipoTurno, DiaFestivo, RegistroTurno, ResumenMensual
from .models_normativo import ParametroNormativo, PoliticaEmpresa


@admin.register(TipoTurno)
class TipoTurnoAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 'nombre_display', 'descripcion',
        'es_nocturno_display', 'horarios_resumen', 'activo'
    ]
    list_filter = ['es_nocturno', 'activo']
    search_fields = ['nombre', 'descripcion', 'codigo']

    fieldsets = [
        ('Información General', {
            'fields': [
                ('nombre', 'codigo'),
                'descripcion',
                ('es_nocturno', 'activo')
            ]
        }),
        ('Horarios Martes, Miércoles, Jueves, Viernes (7 horas)', {
            'fields': [
                ('hora_inicio_martes', 'hora_fin_martes', 'horas_martes'),
                ('hora_inicio_miercoles', 'hora_fin_miercoles', 'horas_miercoles'),
                ('hora_inicio_jueves', 'hora_fin_jueves', 'horas_jueves'),
                ('hora_inicio_viernes', 'hora_fin_viernes', 'horas_viernes'),
            ],
            'description': 'Horarios para días de semana con jornada de 7 horas'
        }),
        ('Horarios Sábado, Domingo, Lunes (8 horas)', {
            'fields': [
                ('hora_inicio_sabado', 'hora_fin_sabado', 'horas_sabado'),
                ('hora_inicio_domingo', 'hora_fin_domingo', 'horas_domingo'),
                ('hora_inicio_lunes', 'hora_fin_lunes', 'horas_lunes'),
            ],
            'description': 'Horarios para fines de semana y lunes con jornada de 8 horas'
        })
    ]

    def nombre_display(self, obj):
        return obj.get_nombre_display()
    nombre_display.short_description = 'Turno'

    def es_nocturno_display(self, obj):
        if obj.es_nocturno:
            return format_html('<span style="color: #2c3e50;">🌙 Nocturno</span>')
        return format_html('<span style="color: #f39c12;">☀️ Diurno</span>')
    es_nocturno_display.short_description = 'Tipo'

    def horarios_resumen(self, obj):
        html = []
        dias = [
            ('L', obj.hora_inicio_lunes, obj.hora_fin_lunes, obj.horas_lunes),
            ('M', obj.hora_inicio_martes, obj.hora_fin_martes, obj.horas_martes),
            ('X', obj.hora_inicio_miercoles, obj.hora_fin_miercoles, obj.horas_miercoles),
            ('J', obj.hora_inicio_jueves, obj.hora_fin_jueves, obj.horas_jueves),
            ('V', obj.hora_inicio_viernes, obj.hora_fin_viernes, obj.horas_viernes),
            ('S', obj.hora_inicio_sabado, obj.hora_fin_sabado, obj.horas_sabado),
            ('D', obj.hora_inicio_domingo, obj.hora_fin_domingo, obj.horas_domingo),
        ]

        for dia, inicio, fin, horas in dias:
            if inicio and fin:
                color = '#e74c3c' if horas == 8 else '#3498db'
                html.append(
                    f'<span style="color: {color}; font-size: 11px;">'
                    f'{dia}: {inicio.strftime("%H:%M")}-{fin.strftime("%H:%M")} ({horas}h)</span>'
                )

        return mark_safe('<br>'.join(html)) if html else 'Sin horarios'
    horarios_resumen.short_description = 'Horarios por Día'


@admin.register(DiaFestivo)
class DiaFestivoAdmin(admin.ModelAdmin):
    list_display = [
        'fecha', 'nombre', 'tipo_display', 'es_nacional',
        'activo', 'dia_semana'
    ]
    list_filter = ['tipo', 'es_nacional', 'activo']
    search_fields = ['nombre', 'observaciones']
    date_hierarchy = 'fecha'

    fieldsets = [
        ('Información del Festivo', {
            'fields': [
                'nombre',
                ('fecha', 'tipo'),
                ('es_nacional', 'activo'),
                'observaciones'
            ]
        })
    ]

    def tipo_display(self, obj):
        colores = {
            'fijo': '#2ecc71',
            'lunes_siguiente': '#3498db',
            'religioso': '#9b59b6',
            'puente': '#f39c12'
        }
        color = colores.get(obj.tipo, '#95a5a6')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_tipo_display()
        )
    tipo_display.short_description = 'Tipo'

    def dia_semana(self, obj):
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        return dias[obj.fecha.weekday()]
    dia_semana.short_description = 'Día'


@admin.register(RegistroTurno)
class RegistroTurnoAdmin(admin.ModelAdmin):
    list_display = [
        'operador_nombre', 'fecha', 'tipo_turno_display', 'estado_display',
        'horas_trabajadas', 'dia_tipo'
    ]
    list_filter = [
        'estado', 'tipo_turno', 'es_domingo', 'es_festivo',
        'incluye_nocturno'
    ]
    search_fields = ['operador__username', 'operador__first_name', 'operador__last_name']
    date_hierarchy = 'fecha'
    readonly_fields = [
        'es_lunes', 'es_martes', 'es_miercoles', 'es_jueves',
        'es_viernes', 'es_sabado', 'es_domingo', 'es_festivo',
        'incluye_nocturno', 'horas_programadas',
        'created_at', 'updated_at'
    ]

    fieldsets = [
        ('Información del Turno', {
            'fields': [
                ('operador', 'tipo_turno'),
                ('fecha', 'estado'),
                'observaciones'
            ]
        }),
        ('Horarios', {
            'fields': [
                ('hora_inicio_real', 'hora_fin_real'),
                ('horas_programadas', 'horas_trabajadas'),
            ]
        }),
        ('Clasificación Automática', {
            'fields': [
                ('es_lunes', 'es_martes', 'es_miercoles', 'es_jueves'),
                ('es_viernes', 'es_sabado', 'es_domingo'),
                ('es_festivo', 'incluye_nocturno'),
                ('created_at', 'updated_at')
            ],
            'classes': ['collapse']
        })
    ]

    def operador_nombre(self, obj):
        return obj.operador.get_full_name() or obj.operador.username
    operador_nombre.short_description = 'Operador'

    def tipo_turno_display(self, obj):
        colores = {
            'Apoyo-A': '#2ecc71',        # Apoyo - Verde
            'Turno 1-M': '#3498db',      # Mañana - Azul
            'Turno 2-T': '#f39c12',      # Tarde - Naranja
            'Turno 3-N': '#2c3e50',      # Noche - Gris oscuro
            'Des o Permi-D': '#95a5a6'   # Descanso - Gris
        }
        color = colores.get(obj.tipo_turno.codigo, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.tipo_turno.codigo
        )
    tipo_turno_display.short_description = 'Turno'

    def estado_display(self, obj):
        colores = {
            'programado': '#3498db',
            'trabajado': '#2ecc71',
            'ausente': '#e74c3c',
            'reemplazado': '#f39c12',
            'extra': '#9b59b6'
        }
        color = colores.get(obj.estado, '#95a5a6')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_display.short_description = 'Estado'

    def dia_tipo(self, obj):
        iconos = []
        if obj.es_domingo:
            iconos.append('🔴 Dom')
        if obj.es_festivo:
            iconos.append('🎉 Fest')
        if obj.incluye_nocturno:
            iconos.append('🌙 Noct')
        if obj.es_sabado:
            iconos.append('🟠 Sáb')

        return ' '.join(iconos) if iconos else '⚪ Regular'
    dia_tipo.short_description = 'Tipo de Día'

    actions = ['marcar_como_trabajado']

    def marcar_como_trabajado(self, request, queryset):
        updated = queryset.update(estado='trabajado')
        self.message_user(
            request,
            f'{updated} registros marcados como trabajados.'
        )
    marcar_como_trabajado.short_description = "Marcar como trabajado"


@admin.register(ResumenMensual)
class ResumenMensualAdmin(admin.ModelAdmin):
    list_display = [
        'operador_nombre', 'periodo', 'total_turnos', 'total_horas_trabajadas',
        'horas_nocturnas', 'horas_dominicales'
    ]
    list_filter = ['ano', 'mes']
    search_fields = ['operador__username', 'operador__first_name', 'operador__last_name']
    readonly_fields = [
        'total_horas_trabajadas', 'total_horas_ordinarias',
        'total_turnos', 'horas_lunes', 'horas_martes', 'horas_miercoles',
        'horas_jueves', 'horas_viernes', 'horas_sabados', 'horas_domingos',
        'horas_festivos', 'horas_nocturnas', 'horas_nocturnas_festivas',
        'horas_dominicales', 'fecha_calculo'
    ]

    fieldsets = [
        ('Período', {
            'fields': [('operador', 'mes', 'ano')]
        }),
        ('Resumen de Horas', {
            'fields': [
                ('total_turnos', 'total_horas_trabajadas'),
                'total_horas_ordinarias',
            ]
        }),
        ('Horas por Día de la Semana', {
            'fields': [
                ('horas_lunes', 'horas_martes', 'horas_miercoles'),
                ('horas_jueves', 'horas_viernes'),
                ('horas_sabados', 'horas_domingos', 'horas_festivos'),
            ],
            'classes': ['collapse']
        }),
        ('Horas por Tipo de Turno', {
            'fields': [
                ('horas_nocturnas', 'horas_dominicales'),
                'horas_nocturnas_festivas',
            ],
            'classes': ['collapse']
        }),
        ('Sistema', {
            'fields': ['fecha_calculo']
        })
    ]

    def operador_nombre(self, obj):
        return obj.operador.get_full_name() or obj.operador.username
    operador_nombre.short_description = 'Operador'

    def periodo(self, obj):
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        mes_nombre = meses[obj.mes] if 1 <= obj.mes <= 12 else str(obj.mes)
        return f"{mes_nombre} {obj.ano}"
    periodo.short_description = 'Período'

    actions = ['generar_resumen_seleccionados']

    def generar_resumen_seleccionados(self, request, queryset):
        generados = 0
        for resumen in queryset:
            resumen.calcular_resumen()
            generados += 1

        self.message_user(
            request,
            f'Se regeneraron {generados} resúmenes mensuales.'
        )
    generar_resumen_seleccionados.short_description = "Regenerar resúmenes seleccionados"


# ============================================================
# MOTOR NORMATIVO PARAMETRIZABLE
# ============================================================

@admin.register(ParametroNormativo)
class ParametroNormativoAdmin(admin.ModelAdmin):
    """
    Admin para gestionar parámetros normativos por fecha de vigencia.
    Cambio de ley = nuevo registro con nueva vigencia_desde.
    """
    list_display = [
        'vigencia_desde', 'hora_inicio_nocturno_display', 'recargos_display',
        'jornada_semanal_max', 'descripcion_corta'
    ]
    list_filter = ['vigencia_desde']
    ordering = ['-vigencia_desde']
    
    fieldsets = [
        ('Vigencia', {
            'fields': [('vigencia_desde', 'vigencia_hasta')],
            'description': 'Fecha desde la cual aplican estos parámetros. Cambio de ley = nuevo registro.'
        }),
        ('Jornada Nocturna (Art. 160 CST)', {
            'fields': [('hora_inicio_nocturno', 'hora_fin_nocturno')],
            'description': 'El horario nocturno varía según la reforma legal (21:00 → 19:00 desde Ley 2101).'
        }),
        ('Recargos (%)', {
            'fields': [
                ('recargo_nocturno', 'recargo_dominical_festivo'),
                ('recargo_nocturno_festivo',),
                ('recargo_extra_diurno', 'recargo_extra_nocturno'),
            ],
            'description': 'Porcentajes como decimales: 35% = 0.35, 75% = 0.75'
        }),
        ('Jornada Legal', {
            'fields': [
                ('jornada_diaria_max', 'jornada_semanal_max'),
                'divisor_mensual',
            ]
        }),
        ('Topes Horas Extra', {
            'fields': [('tope_extra_dia', 'tope_extra_semana')],
            'classes': ['collapse']
        }),
        ('Metadata', {
            'fields': ['descripcion', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    def hora_inicio_nocturno_display(self, obj):
        return obj.hora_inicio_nocturno.strftime('%H:%M')
    hora_inicio_nocturno_display.short_description = 'Inicio Nocturno'
    
    def recargos_display(self, obj):
        return format_html(
            '<span title="RNO: {rno}%, RDF: {rdf}%, RNF: {rnf}%">RNO {rno}% | RDF {rdf}%</span>',
            rno=int(obj.recargo_nocturno * 100),
            rdf=int(obj.recargo_dominical_festivo * 100),
            rnf=int(obj.recargo_nocturno_festivo * 100)
        )
    recargos_display.short_description = 'Recargos'
    
    def descripcion_corta(self, obj):
        return obj.descripcion[:40] + '...' if len(obj.descripcion) > 40 else obj.descripcion
    descripcion_corta.short_description = 'Descripción'


@admin.register(PoliticaEmpresa)
class PoliticaEmpresaAdmin(admin.ModelAdmin):
    """Admin para políticas de empresa (reglas más favorables que la ley)."""
    list_display = [
        'vigencia_desde', 'pagar_dominical_100', 'sabado_es_descanso',
        'redondear_minutos', 'usar_banco_horas'
    ]
    list_filter = ['pagar_dominical_100', 'sabado_es_descanso', 'usar_banco_horas']
    ordering = ['-vigencia_desde']
    
    fieldsets = [
        ('Vigencia', {
            'fields': ['vigencia_desde']
        }),
        ('Políticas Extralegales', {
            'fields': [
                'pagar_dominical_100',
                'sabado_es_descanso',
                'redondear_minutos',
                'usar_banco_horas',
            ],
            'description': 'Estas políticas pueden ser más favorables que el mínimo legal.'
        }),
        ('Metadata', {
            'fields': ['descripcion', 'created_at'],
            'classes': ['collapse']
        }),
    ]
    
    readonly_fields = ['created_at']


# Personalización del título del admin
admin.site.site_header = "Sistema de Gestión de Turnos - Centro de Cómputo"
admin.site.site_title = "Turnos Admin"
admin.site.index_title = "Administración de Turnos y Horas Trabajadas"
