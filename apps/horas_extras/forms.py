# apps/horas_extras/forms.py - VERSIÓN SIMPLIFICADA
# Operadores identificados por rol "operador de centro de computo"

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, time, datetime
import calendar
from decimal import Decimal

from .models import TipoTurno, RegistroTurno, DiaFestivo
from apps.user_management.models import Role, UserRole
from .utils import ValidadorTurnos

# Meses en español para formularios
MESES_ES = [
    ('1', 'Enero'),
    ('2', 'Febrero'),
    ('3', 'Marzo'),
    ('4', 'Abril'),
    ('5', 'Mayo'),
    ('6', 'Junio'),
    ('7', 'Julio'),
    ('8', 'Agosto'),
    ('9', 'Septiembre'),
    ('10', 'Octubre'),
    ('11', 'Noviembre'),
    ('12', 'Diciembre'),
]


class DateInput(forms.DateInput):
    input_type = 'date'


class TimeInput(forms.TimeInput):
    input_type = 'time'


class RegistroTurnoForm(forms.ModelForm):
    """Formulario para registrar/editar turnos"""

    class Meta:
        model = RegistroTurno
        fields = [
            'operador', 'tipo_turno', 'fecha', 'estado',
            'hora_inicio_real', 'hora_fin_real', 'horas_trabajadas',
            'observaciones'
        ]
        widgets = {
            'fecha': DateInput(attrs={'class': 'form-control'}),
            'hora_inicio_real': TimeInput(attrs={'class': 'form-control'}),
            'hora_fin_real': TimeInput(attrs={'class': 'form-control'}),
            'horas_trabajadas': forms.NumberInput(attrs={
                'step': '0.25',
                'min': '0',
                'max': '12',
                'class': 'form-control'
            }),
            'operador': forms.Select(attrs={'class': 'form-control'}),
            'tipo_turno': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones opcionales...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrar solo operadores activos con rol "operador de centro de computo"
        try:
            rol_operador = Role.objects.get(name='operador de centro de computo')
            self.fields['operador'].queryset = User.objects.filter(
                is_active=True,
                userrole__role=rol_operador,
                userrole__activo=True
            ).distinct().order_by('last_name', 'first_name')
        except Role.DoesNotExist:
            self.fields['operador'].queryset = User.objects.none()

        # Filtrar tipos de turno activos
        self.fields['tipo_turno'].queryset = TipoTurno.objects.filter(
            activo=True
        ).order_by('nombre')

        # Si es edición, deshabilitar algunos campos
        if self.instance.pk:
            self.fields['operador'].widget.attrs['readonly'] = True
            self.fields['fecha'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()

        operador = cleaned_data.get('operador')
        fecha = cleaned_data.get('fecha')
        hora_inicio = cleaned_data.get('hora_inicio_real')
        hora_fin = cleaned_data.get('hora_fin_real')
        horas_trabajadas = cleaned_data.get('horas_trabajadas')
        estado = cleaned_data.get('estado')

        # Validar que la fecha no sea futura
        if fecha and fecha > date.today():
            raise ValidationError('No se pueden registrar turnos en fechas futuras')

        # Validar horarios
        if hora_inicio and hora_fin:
            if hora_inicio == hora_fin:
                raise ValidationError('La hora de inicio no puede ser igual a la de fin')

            # Calcular horas automáticamente si no se proporcionaron
            if not horas_trabajadas:
                if fecha:
                    inicio = datetime.combine(fecha, hora_inicio)
                    fin = datetime.combine(fecha, hora_fin)

                    # Si el turno termina al día siguiente
                    if hora_fin < hora_inicio:
                        fin += timezone.timedelta(days=1)

                    duracion = fin - inicio
                    horas_calc = Decimal(str(duracion.total_seconds() / 3600))
                    cleaned_data['horas_trabajadas'] = max(horas_calc, Decimal('0.00'))

        # Validaciones específicas para turnos trabajados
        if estado == 'trabajado':
            if not hora_inicio or not hora_fin:
                raise ValidationError('Los turnos trabajados requieren hora de inicio y fin')

            if not horas_trabajadas or horas_trabajadas <= 0:
                raise ValidationError('Los turnos trabajados requieren horas trabajadas válidas')

        # Validar duplicados
        if operador and fecha:
            existing = RegistroTurno.objects.filter(
                operador=operador,
                fecha=fecha
            )

            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise ValidationError(f'Ya existe un turno para {operador.get_full_name() or operador.username} el {fecha}')

        return cleaned_data

    def clean_horas_trabajadas(self):
        horas = self.cleaned_data.get('horas_trabajadas')

        if horas is not None:
            if horas < 0:
                raise ValidationError('Las horas trabajadas no pueden ser negativas')

            if horas > 12:
                raise ValidationError('No se pueden trabajar más de 12 horas en un día')

        return horas


class GenerarTurnosForm(forms.Form):
    """Formulario para generar turnos automáticos"""

    PATRON_CHOICES = [
        ('M', 'Mañana'),
        ('T', 'Tarde'),
        ('N', 'Noche'),
        ('A', 'Apoyo')
    ]

    operador_id = forms.IntegerField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Operador'
    )

    mes = forms.ChoiceField(
        choices=MESES_ES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Mes'
    )

    ano = forms.ChoiceField(
        choices=[(str(i), str(i)) for i in range(2024, 2030)],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Año'
    )

    patron_inicial = forms.ChoiceField(
        choices=PATRON_CHOICES,
        initial='M',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Patrón Inicial',
        help_text='Tipo de turno con el que iniciará el mes'
    )

    sobrescribir = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Sobrescribir turnos existentes',
        help_text='Marque para eliminar turnos existentes y generar nuevos'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Cargar operadores activos
        try:
            rol_operador = Role.objects.get(name='operador de centro de computo')
            operadores = User.objects.filter(
                is_active=True,
                userrole__role=rol_operador,
                userrole__activo=True
            ).distinct().order_by('last_name', 'first_name')

            choices = [(op.id, f"{op.get_full_name() or op.username}") for op in operadores]
            self.fields['operador_id'].widget.choices = [('', '--- Seleccione ---')] + choices
        except Role.DoesNotExist:
            self.fields['operador_id'].widget.choices = [('', '--- No hay operadores ---')]

    def clean(self):
        cleaned_data = super().clean()

        mes = int(cleaned_data.get('mes', 0))
        ano = int(cleaned_data.get('ano', 0))

        # Validar que no sea un mes pasado (más de 2 meses atrás)
        hoy = date.today()
        fecha_mes = date(ano, mes, 1)

        if fecha_mes < date(hoy.year, max(1, hoy.month - 2), 1):
            raise ValidationError('No se pueden generar turnos para meses muy anteriores')

        return cleaned_data


class FiltroReporteForm(forms.Form):
    """Formulario para filtros de reportes"""

    TIPO_REPORTE_CHOICES = [
        ('individual', 'Reporte Individual'),
        ('todos', 'Todos los Operadores'),
        ('resumen', 'Resumen Ejecutivo')
    ]

    tipo_reporte = forms.ChoiceField(
        choices=TIPO_REPORTE_CHOICES,
        initial='todos',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Tipo de Reporte'
    )

    operador_id = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Operador'
    )

    mes = forms.ChoiceField(
        choices=MESES_ES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Mes'
    )

    ano = forms.ChoiceField(
        choices=[(str(i), str(i)) for i in range(2024, 2030)],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Año'
    )

    incluir_graficos = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Incluir Gráficos',
        help_text='Incluir gráficos estadísticos en el reporte'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Cargar operadores activos
        try:
            rol_operador = Role.objects.get(name='operador de centro de computo')
            operadores = User.objects.filter(
                is_active=True,
                userrole__role=rol_operador,
                userrole__activo=True
            ).distinct().order_by('last_name', 'first_name')

            choices = [(op.id, f"{op.get_full_name() or op.username}") for op in operadores]
            self.fields['operador_id'].widget.choices = [('', '--- Todos ---')] + choices
        except Role.DoesNotExist:
            self.fields['operador_id'].widget.choices = [('', '--- No hay operadores ---')]

    def clean(self):
        cleaned_data = super().clean()

        tipo_reporte = cleaned_data.get('tipo_reporte')
        operador_id = cleaned_data.get('operador_id')

        # Si es reporte individual, el operador es obligatorio
        if tipo_reporte == 'individual' and not operador_id:
            raise ValidationError('Debe seleccionar un operador para reportes individuales')

        return cleaned_data
