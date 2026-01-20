# apps/horas_extras/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, time, datetime
import calendar
from decimal import Decimal

from .models import (
    Empleado, TipoTurno, RegistroTurno, DiaFestivo
)
from .utils import ValidadorTurnos


class DateInput(forms.DateInput):
    input_type = 'date'


class TimeInput(forms.TimeInput):
    input_type = 'time'


class EmpleadoForm(forms.ModelForm):
    """Formulario para crear/editar empleados"""
    
    class Meta:
        model = Empleado
        fields = [
            'numero_empleado', 'nombres', 'apellidos', 'cedula',
            'cargo', 'salario_base', 'fecha_ingreso', 'estado',
            'telefono', 'email', 'direccion', 'horas_mensuales'
        ]
        widgets = {
            'fecha_ingreso': DateInput(),
            'salario_base': forms.NumberInput(attrs={
                'step': '1000',
                'min': '0',
                'class': 'form-control'
            }),
            'horas_mensuales': forms.NumberInput(attrs={
                'min': '1',
                'max': '300',
                'class': 'form-control'
            }),
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_empleado': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'cargo': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if cedula:
            # Verificar unicidad
            existing = Empleado.objects.filter(cedula=cedula)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError('Ya existe un empleado con esta cédula')
        
        return cedula
    
    def clean_numero_empleado(self):
        numero = self.cleaned_data.get('numero_empleado')
        if numero:
            # Verificar unicidad
            existing = Empleado.objects.filter(numero_empleado=numero)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError('Ya existe un empleado con este número')
        
        return numero
    
    def clean_salario_base(self):
        salario = self.cleaned_data.get('salario_base')
        if salario and salario <= 0:
            raise ValidationError('El salario debe ser mayor a cero')
        return salario


class RegistroTurnoForm(forms.ModelForm):
    """Formulario para registrar/editar turnos"""
    
    class Meta:
        model = RegistroTurno
        fields = [
            'empleado', 'tipo_turno', 'fecha', 'estado',
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
            'empleado': forms.Select(attrs={'class': 'form-control'}),
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
        
        # Filtrar empleados activos
        self.fields['empleado'].queryset = Empleado.objects.filter(
            estado='activo'
        ).order_by('apellidos', 'nombres')
        
        # Filtrar tipos de turno activos
        self.fields['tipo_turno'].queryset = TipoTurno.objects.filter(
            activo=True
        ).order_by('nombre')
        
        # Si es edición, deshabilitar algunos campos
        if self.instance.pk:
            self.fields['empleado'].widget.attrs['readonly'] = True
            self.fields['fecha'].widget.attrs['readonly'] = True
    
    def clean(self):
        cleaned_data = super().clean()
        
        empleado = cleaned_data.get('empleado')
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
        if empleado and fecha:
            existing = RegistroTurno.objects.filter(
                empleado=empleado,
                fecha=fecha
            )
            
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(f'Ya existe un turno para {empleado} el {fecha}')
        
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
    
    empleado = forms.ModelChoiceField(
        queryset=Empleado.objects.filter(estado='activo').order_by('apellidos', 'nombres'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Empleado'
    )
    
    mes = forms.ChoiceField(
        choices=[(i, calendar.month_name[i]) for i in range(1, 13)],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Mes'
    )
    
    ano = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(2024, 2030)],
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
    
    def clean(self):
        cleaned_data = super().clean()
        
        mes = int(cleaned_data.get('mes', 0))
        ano = int(cleaned_data.get('ano', 0))
        
        # Validar que no sea un mes pasado (más de 2 meses atrás)
        hoy = date.today()
        fecha_mes = date(ano, mes, 1)
        
        if fecha_mes < date(hoy.year, hoy.month - 2, 1):
            raise ValidationError('No se pueden generar turnos para meses muy anteriores')
        
        return cleaned_data


class FiltroReporteForm(forms.Form):
    """Formulario para filtros de reportes"""
    
    TIPO_REPORTE_CHOICES = [
        ('individual', 'Reporte Individual'),
        ('todos', 'Todos los Empleados'),
        ('resumen', 'Resumen Ejecutivo')
    ]
    
    tipo_reporte = forms.ChoiceField(
        choices=TIPO_REPORTE_CHOICES,
        initial='todos',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Tipo de Reporte'
    )
    
    empleado = forms.ModelChoiceField(
        queryset=Empleado.objects.filter(estado='activo').order_by('apellidos', 'nombres'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Empleado',
        help_text='Requerido solo para reportes individuales'
    )
    
    mes = forms.ChoiceField(
        choices=[(i, calendar.month_name[i]) for i in range(1, 13)],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Mes'
    )
    
    ano = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(2024, 2030)],
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
    
    def clean(self):
        cleaned_data = super().clean()
        
        tipo_reporte = cleaned_data.get('tipo_reporte')
        empleado = cleaned_data.get('empleado')
        
        # Si es reporte individual, el empleado es obligatorio
        if tipo_reporte == 'individual' and not empleado:
            raise ValidationError('Debe seleccionar un empleado para reportes individuales')
        
        return cleaned_data
