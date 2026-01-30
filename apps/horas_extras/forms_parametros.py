# apps/horas_extras/forms_parametros.py
from django import forms
from .models_normativo import ParametroNormativo, PoliticaEmpresa


class ParametroNormativoForm(forms.ModelForm):
    """Formulario para gestionar parámetros normativos desde la interfaz SACSBD"""
    
    class Meta:
        model = ParametroNormativo
        fields = [
            'vigencia_desde', 'vigencia_hasta',
            'hora_inicio_nocturno', 'hora_fin_nocturno',
            'recargo_nocturno', 'recargo_dominical_festivo', 'recargo_nocturno_festivo',
            'recargo_extra_diurno', 'recargo_extra_nocturno',
            'jornada_diaria_max', 'jornada_semanal_max', 'divisor_mensual',
            'tope_extra_dia', 'tope_extra_semana',
            'descripcion'
        ]
        widgets = {
            'vigencia_desde': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'vigencia_hasta': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'hora_inicio_nocturno': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control'
            }),
            'hora_fin_nocturno': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control'
            }),
            'recargo_nocturno': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.35 = 35%'
            }),
            'recargo_dominical_festivo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.75 = 75%'
            }),
            'recargo_nocturno_festivo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '1.10 = 110%'
            }),
            'recargo_extra_diurno': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.25 = 25%'
            }),
            'recargo_extra_nocturno': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.75 = 75%'
            }),
            'jornada_diaria_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '12'
            }),
            'jornada_semanal_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '60'
            }),
            'divisor_mensual': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'tope_extra_dia': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'tope_extra_semana': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ej: Ley 2101 de 2021 - Reducción jornada laboral'
            })
        }
        labels = {
            'vigencia_desde': 'Vigencia Desde',
            'vigencia_hasta': 'Vigencia Hasta (opcional)',
            'hora_inicio_nocturno': 'Hora Inicio Nocturno',
            'hora_fin_nocturno': 'Hora Fin Nocturno',
            'recargo_nocturno': 'Recargo Nocturno (%)',
            'recargo_dominical_festivo': 'Recargo Dominical/Festivo (%)',
            'recargo_nocturno_festivo': 'Recargo Nocturno Festivo (%)',
            'recargo_extra_diurno': 'Hora Extra Diurna (%)',
            'recargo_extra_nocturno': 'Hora Extra Nocturna (%)',
            'jornada_diaria_max': 'Jornada Diaria Máxima (horas)',
            'jornada_semanal_max': 'Jornada Semanal Máxima (horas)',
            'divisor_mensual': 'Divisor Mensual',
            'tope_extra_dia': 'Tope Horas Extra por Día',
            'tope_extra_semana': 'Tope Horas Extra por Semana',
            'descripcion': 'Descripción'
        }
        help_texts = {
            'vigencia_desde': 'Fecha desde la cual aplican estos parámetros',
            'vigencia_hasta': 'Dejar vacío si es vigencia indefinida',
            'recargo_nocturno': 'Usar decimales: 35% = 0.35',
            'recargo_dominical_festivo': 'Usar decimales: 75% = 0.75',
            'descripcion': 'Ej: Ley 2101 - Reforma 2025'
        }
    
    def clean(self):
        cleaned_data = super().clean()
        vigencia_desde = cleaned_data.get('vigencia_desde')
        vigencia_hasta = cleaned_data.get('vigencia_hasta')
        
        # Validar que vigencia_hasta sea posterior a vigencia_desde
        if vigencia_desde and vigencia_hasta:
            if vigencia_hasta <= vigencia_desde:
                raise forms.ValidationError(
                    'La fecha "Vigencia Hasta" debe ser posterior a "Vigencia Desde"'
                )
        
        return cleaned_data


class PoliticaEmpresaForm(forms.ModelForm):
    """Formulario para políticas de empresa"""
    
    class Meta:
        model = PoliticaEmpresa
        fields = [
            'vigencia_desde',
            'pagar_dominical_100',
            'sabado_es_descanso',
            'redondear_minutos',
            'usar_banco_horas',
            'descripcion'
        ]
        widgets = {
            'vigencia_desde': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'redondear_minutos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0 = sin redondeo'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            })
        }
