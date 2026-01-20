# apps/horas_extras/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count
from decimal import Decimal
import calendar
from .models import (
    Empleado, TipoTurno, DiaFestivo, RegistroTurno, 
    CalculoRecargo, ResumenMensual
)


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = [
        'numero_empleado', 'nombre_completo', 'cedula', 
        'cargo_display', 'valor_hora_formateado', 'estado', 
        'fecha_ingreso'
    ]
    list_filter = ['cargo', 'estado', 'fecha_ingreso']
    search_fields = ['nombres', 'apellidos', 'cedula', 'numero_empleado']
    readonly_fields = ['valor_hora', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Información Personal', {
            'fields': [
                ('numero_empleado', 'cedula'),
                ('nombres', 'apellidos'),
                ('telefono', 'email'),
                'direccion'
            ]
        }),
        ('Información Laboral', {
            'fields': [
                ('cargo', 'estado'),
                'fecha_ingreso',
                ('salario_base', 'horas_mensuales'),
                'valor_hora',
            ]
        }),
        ('Sistema', {
            'fields': ['user', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def nombre_completo(self, obj):
        return f"{obj.nombres} {obj.apellidos}"
    nombre_completo.short_description = 'Nombre Completo'
    
    def cargo_display(self, obj):
        colores = {
            'operador_junior': '#3498db',
            'operador_senior': '#2ecc71', 
            'coordinador': '#f39c12',
            'supervisor': '#e74c3c'
        }
        color = colores.get(obj.cargo, '#95a5a6')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_cargo_display()
        )
    cargo_display.short_description = 'Cargo'
    
    def valor_hora_formateado(self, obj):
        if obj.valor_hora:
            return format_html(
                '<strong>${:,.0f}</strong>',
                obj.valor_hora
            )
        return '-'
    valor_hora_formateado.short_description = 'Valor/Hora'
    
    def save_model(self, request, obj, form, change):
        # Calcular valor hora automáticamente
        obj.calcular_valor_hora()
        super().save_model(request, obj, form, change)


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
    list_filter = ['tipo', 'es_nacional', 'activo', 'fecha__year']
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


class CalculoRecargoInline(admin.StackedInline):
    model = CalculoRecargo
    extra = 0
    readonly_fields = [
        'valor_hora_base', 'total_ordinario', 'total_recargos', 
        'total_horas_extras', 'total_a_pagar', 'fecha_calculo'
    ]
    
    fieldsets = [
        ('Cálculos de Recargos', {
            'fields': [
                ('valor_hora_base', 'horas_ordinarias'),
                ('horas_recargo_nocturno', 'valor_recargo_nocturno'),
                ('horas_recargo_dominical', 'valor_recargo_dominical'),
                ('horas_recargo_festivo', 'valor_recargo_festivo'),
                ('horas_recargo_nocturno_festivo', 'valor_recargo_nocturno_festivo'),
            ]
        }),
        ('Horas Extras', {
            'fields': [
                ('horas_extras_diurnas_ordinarias', 'valor_horas_extras_diurnas_ordinarias'),
                ('horas_extras_nocturnas_ordinarias', 'valor_horas_extras_nocturnas_ordinarias'),
                ('horas_extras_diurnas_festivas', 'valor_horas_extras_diurnas_festivas'),
                ('horas_extras_nocturnas_festivas', 'valor_horas_extras_nocturnas_festivas'),
            ]
        }),
        ('Totales', {
            'fields': [
                ('total_ordinario', 'total_recargos'),
                ('total_horas_extras', 'total_a_pagar'),
                'fecha_calculo'
            ]
        })
    ]


@admin.register(RegistroTurno)
class RegistroTurnoAdmin(admin.ModelAdmin):
    list_display = [
        'empleado', 'fecha', 'tipo_turno_display', 'estado_display',
        'horas_trabajadas', 'horas_extras', 'dia_tipo', 'total_pagar'
    ]
    list_filter = [
        'estado', 'tipo_turno', 'es_domingo', 'es_festivo', 
        'incluye_nocturno', 'fecha__month'
    ]
    search_fields = ['empleado__nombres', 'empleado__apellidos', 'empleado__cedula']
    date_hierarchy = 'fecha'
    readonly_fields = [
        'es_lunes', 'es_martes', 'es_miercoles', 'es_jueves', 
        'es_viernes', 'es_sabado', 'es_domingo', 'es_festivo',
        'incluye_nocturno', 'horas_programadas', 'horas_extras',
        'created_at', 'updated_at'
    ]
    
    inlines = [CalculoRecargoInline]
    
    fieldsets = [
        ('Información del Turno', {
            'fields': [
                ('empleado', 'tipo_turno'),
                ('fecha', 'estado'),
                'observaciones'
            ]
        }),
        ('Horarios', {
            'fields': [
                ('hora_inicio_real', 'hora_fin_real'),
                ('horas_programadas', 'horas_trabajadas', 'horas_extras'),
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
    
    def tipo_turno_display(self, obj):
        colores = {
            'M': '#3498db',  # Mañana - Azul
            'T': '#f39c12',  # Tarde - Naranja  
            'N': '#2c3e50',  # Noche - Gris oscuro
            'A': '#2ecc71',  # Apoyo - Verde
            'D': '#95a5a6'   # Descanso - Gris
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
    
    def total_pagar(self, obj):
        if hasattr(obj, 'calculo'):
            return format_html(
                '<strong>${:,.0f}</strong>',
                obj.calculo.total_a_pagar
            )
        return 'Sin calcular'
    total_pagar.short_description = 'Total a Pagar'
    
    actions = ['calcular_recargos_seleccionados', 'marcar_como_trabajado']
    
    def calcular_recargos_seleccionados(self, request, queryset):
        calculados = 0
        for registro in queryset:
            calculo, created = CalculoRecargo.objects.get_or_create(
                registro_turno=registro,
                defaults={'valor_hora_base': registro.empleado.valor_hora or Decimal('0')}
            )
            calculo.calcular_recargos()
            calculo.save()
            calculados += 1
        
        self.message_user(
            request,
            f'Se calcularon los recargos para {calculados} registros.'
        )
    calcular_recargos_seleccionados.short_description = "Calcular recargos para registros seleccionados"
    
    def marcar_como_trabajado(self, request, queryset):
        updated = queryset.update(estado='trabajado')
        self.message_user(
            request,
            f'{updated} registros marcados como trabajados.'
        )
    marcar_como_trabajado.short_description = "Marcar como trabajado"


@admin.register(CalculoRecargo)
class CalculoRecargoAdmin(admin.ModelAdmin):
    list_display = [
        'empleado_turno', 'fecha_turno', 'valor_hora_base',
        'horas_ordinarias', 'total_recargos_display', 
        'total_horas_extras_display', 'total_a_pagar_display'
    ]
    list_filter = [
        'registro_turno__empleado', 'registro_turno__fecha',
        'registro_turno__es_domingo', 'registro_turno__es_festivo'
    ]
    readonly_fields = [
        'valor_hora_base', 'total_ordinario', 'total_recargos',
        'total_horas_extras', 'total_a_pagar', 'fecha_calculo'
    ]
    
    fieldsets = [
        ('Información Base', {
            'fields': [
                'registro_turno',
                ('valor_hora_base', 'horas_ordinarias')
            ]
        }),
        ('Recargos Aplicados', {
            'fields': [
                ('horas_recargo_nocturno', 'valor_recargo_nocturno'),
                ('horas_recargo_dominical', 'valor_recargo_dominical'),
                ('horas_recargo_festivo', 'valor_recargo_festivo'),
                ('horas_recargo_nocturno_festivo', 'valor_recargo_nocturno_festivo'),
            ]
        }),
        ('Horas Extras', {
            'fields': [
                ('horas_extras_diurnas_ordinarias', 'valor_horas_extras_diurnas_ordinarias'),
                ('horas_extras_nocturnas_ordinarias', 'valor_horas_extras_nocturnas_ordinarias'),
                ('horas_extras_diurnas_festivas', 'valor_horas_extras_diurnas_festivas'),
                ('horas_extras_nocturnas_festivas', 'valor_horas_extras_nocturnas_festivas'),
            ]
        }),
        ('Totales Calculados', {
            'fields': [
                ('total_ordinario', 'total_recargos'),
                ('total_horas_extras', 'total_a_pagar'),
                'fecha_calculo'
            ]
        })
    ]
    
    def empleado_turno(self, obj):
        return f"{obj.registro_turno.empleado.nombres} - {obj.registro_turno.tipo_turno.codigo}"
    empleado_turno.short_description = 'Empleado - Turno'
    
    def fecha_turno(self, obj):
        return obj.registro_turno.fecha
    fecha_turno.short_description = 'Fecha'
    
    def total_recargos_display(self, obj):
        return format_html('<strong>${:,.0f}</strong>', obj.total_recargos)
    total_recargos_display.short_description = 'Total Recargos'
    
    def total_horas_extras_display(self, obj):
        return format_html('<strong>${:,.0f}</strong>', obj.total_horas_extras)
    total_horas_extras_display.short_description = 'Total H. Extras'
    
    def total_a_pagar_display(self, obj):
        return format_html(
            '<strong style="color: #27ae60; font-size: 14px;">${:,.0f}</strong>', 
            obj.total_a_pagar
        )
    total_a_pagar_display.short_description = 'Total a Pagar'


@admin.register(ResumenMensual)
class ResumenMensualAdmin(admin.ModelAdmin):
    list_display = [
        'empleado', 'periodo', 'total_turnos', 'total_horas_trabajadas',
        'total_horas_extras', 'total_a_pagar_display'
    ]
    list_filter = ['ano', 'mes', 'empleado']
    search_fields = ['empleado__nombres', 'empleado__apellidos']
    readonly_fields = [
        'total_horas_trabajadas', 'total_horas_ordinarias', 'total_horas_extras',
        'total_turnos', 'horas_lunes', 'horas_martes', 'horas_miercoles',
        'horas_jueves', 'horas_viernes', 'horas_sabados', 'horas_domingos',
        'horas_festivos', 'total_recargos_nocturnos', 'total_recargos_dominicales',
        'total_recargos_festivos', 'total_recargos_nocturno_festivo',
        'total_valor_ordinario', 'total_valor_recargos', 'total_valor_horas_extras',
        'total_a_pagar', 'fecha_generacion', 'actualizado_en'
    ]
    
    fieldsets = [
        ('Período', {
            'fields': [('empleado', 'mes', 'ano')]
        }),
        ('Resumen de Horas', {
            'fields': [
                ('total_turnos', 'total_horas_trabajadas'),
                ('total_horas_ordinarias', 'total_horas_extras'),
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
        ('Totales de Recargos', {
            'fields': [
                ('total_recargos_nocturnos', 'total_recargos_dominicales'),
                ('total_recargos_festivos', 'total_recargos_nocturno_festivo'),
            ],
            'classes': ['collapse']
        }),
        ('Totales Monetarios', {
            'fields': [
                ('total_valor_ordinario', 'total_valor_recargos'),
                ('total_valor_horas_extras', 'total_a_pagar'),
                ('fecha_generacion', 'actualizado_en')
            ]
        })
    ]
    
    def periodo(self, obj):
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        mes_nombre = meses[obj.mes] if 1 <= obj.mes <= 12 else str(obj.mes)
        return f"{mes_nombre} {obj.ano}"
    periodo.short_description = 'Período'
    
    def total_a_pagar_display(self, obj):
        return format_html(
            '<strong style="color: #27ae60; font-size: 14px;">${:,.0f}</strong>', 
            obj.total_a_pagar
        )
    total_a_pagar_display.short_description = 'Total a Pagar'
    
    actions = ['generar_resumen_seleccionados']
    
    def generar_resumen_seleccionados(self, request, queryset):
        generados = 0
        for resumen in queryset:
            resumen.generar_resumen()
            generados += 1
        
        self.message_user(
            request,
            f'Se regeneraron {generados} resúmenes mensuales.'
        )
    generar_resumen_seleccionados.short_description = "Regenerar resúmenes seleccionados"


# Personalización del título del admin
admin.site.site_header = "Sistema de Horas Extras - Centro de Cómputo"
admin.site.site_title = "Horas Extras Admin"
admin.site.index_title = "Administración de Horas Extras y Recargos"
