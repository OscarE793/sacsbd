# apps/horas_extras/models_normativo.py
"""
Motor Normativo Parametrizable para SACSBD
==========================================

Modelos que almacenan parámetros legales versionados por fecha.
Cambio de ley = nuevo registro, NO modificar código.

Arquitectura:
- ParametroNormativo: Parámetros de la norma laboral colombiana
- PoliticaEmpresa: Reglas internas que pueden ser más favorables que la ley
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import time


class ParametroNormativo(models.Model):
    """
    Parámetros legales versionados por fecha de vigencia.
    
    REGLA CLAVE: Cambio de ley = nuevo registro con nueva vigencia_desde
    El sistema automáticamente aplica los parámetros correctos según la fecha.
    
    Referencia legal:
    - Ley 2101 de 2021: Reducción jornada laboral
    - Art. 160 CST: Jornada nocturna
    - Art. 179 CST: Recargos dominicales y festivos
    """
    
    vigencia_desde = models.DateField(
        unique=True,
        help_text='Fecha desde la cual aplican estos parámetros'
    )
    vigencia_hasta = models.DateField(
        null=True, 
        blank=True,
        help_text='Fecha hasta la cual aplican (null = vigente indefinidamente)'
    )
    
    # === JORNADA NOCTURNA ===
    hora_inicio_nocturno = models.TimeField(
        default=time(21, 0),
        help_text='Hora inicio jornada nocturna (Art. 160 CST)'
    )
    hora_fin_nocturno = models.TimeField(
        default=time(6, 0),
        help_text='Hora fin jornada nocturna'
    )
    
    # === RECARGOS (porcentajes como decimales) ===
    recargo_nocturno = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        default=Decimal('0.35'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Recargo nocturno ordinario (35% = 0.35)'
    )
    recargo_dominical_festivo = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        default=Decimal('0.75'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Recargo dominical/festivo diurno (75% = 0.75)'
    )
    recargo_nocturno_festivo = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        default=Decimal('1.10'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Recargo nocturno en festivo (35% + 75% = 1.10)'
    )
    recargo_extra_diurno = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        default=Decimal('0.25'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Hora extra diurna (25%)'
    )
    recargo_extra_nocturno = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        default=Decimal('0.75'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Hora extra nocturna (75%)'
    )
    
    # === JORNADA LEGAL ===
    jornada_diaria_max = models.IntegerField(
        default=8,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text='Máximo de horas ordinarias por día'
    )
    jornada_semanal_max = models.IntegerField(
        default=44,
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        help_text='Máximo de horas ordinarias por semana (2025: 44h)'
    )
    divisor_mensual = models.IntegerField(
        default=220,
        help_text='Divisor para cálculo de valor hora (2025: 220)'
    )
    
    # === TOPES HORAS EXTRA ===
    tope_extra_dia = models.IntegerField(
        default=2,
        help_text='Máximo de horas extra autorizadas por día'
    )
    tope_extra_semana = models.IntegerField(
        default=12,
        help_text='Máximo de horas extra autorizadas por semana'
    )

    # === CONFIGURACIÓN FLEXIBLE DE TURNOS (JSON) ===
    configuracion_turnos = models.TextField(
        default="{}",
        blank=True,
        help_text="JSON para sobrescribir horarios. Ej: {'M': {'semana': ['06:00', '13:00']}}"
    )
    
    # === METADATA ===
    descripcion = models.TextField(
        blank=True,
        help_text='Descripción de esta versión de parámetros (ej: "Ley 2101 - Reforma 2025")'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Parámetro Normativo'
        verbose_name_plural = 'Parámetros Normativos'
        ordering = ['-vigencia_desde']
    
    def __str__(self):
        return f"Norma desde {self.vigencia_desde} - {self.descripcion[:50] if self.descripcion else 'Sin descripción'}"
    
    @classmethod
    def obtener_vigente(cls, fecha):
        """
        Obtiene los parámetros vigentes para una fecha específica.
        
        Busca el registro con vigencia_desde <= fecha más reciente.
        
        Args:
            fecha: datetime.date para consultar
            
        Returns:
            ParametroNormativo o None si no hay parámetros definidos
        """
        return cls.objects.filter(
            vigencia_desde__lte=fecha
        ).order_by('-vigencia_desde').first()
    
    def es_hora_nocturna(self, hora):
        """
        Determina si una hora específica cae en jornada nocturna.
        
        Args:
            hora: int (0-23) o datetime.time
            
        Returns:
            bool: True si es nocturna
        """
        if hasattr(hora, 'hour'):
            hora = hora.hour
        
        inicio = self.hora_inicio_nocturno.hour
        fin = self.hora_fin_nocturno.hour
        
        # Jornada nocturna cruza medianoche (ej: 21:00 a 06:00)
        if inicio > fin:
            return hora >= inicio or hora < fin
        else:
            return inicio <= hora < fin

    def save(self, *args, **kwargs):
        """
        Sobrescribe save para garantizar la consistencia legal:
        RNF = RNO + RDF (Siempre)
        """
        # Calcular RNF automáticamente
        self.recargo_nocturno_festivo = self.recargo_nocturno + self.recargo_dominical_festivo
        
        super().save(*args, **kwargs)


class PoliticaEmpresa(models.Model):
    """
    Políticas internas que pueden ser más favorables que la ley mínima.
    
    Ejemplo: Pagar dominicales al 100% en lugar del 75% legal.
    """
    
    vigencia_desde = models.DateField(
        unique=True,
        help_text='Fecha desde la cual aplica esta política'
    )
    
    # === POLÍTICAS EXTRALEGALES ===
    pagar_dominical_100 = models.BooleanField(
        default=False,
        help_text='Si True, paga dominicales al 100% en lugar del 75% legal'
    )
    sabado_es_descanso = models.BooleanField(
        default=False,
        help_text='Si True, sábado se considera día de descanso (recargo adicional)'
    )
    redondear_minutos = models.IntegerField(
        default=0,
        help_text='Redondear minutos al múltiplo indicado (0 = no redondear)'
    )
    
    # === BANCO DE HORAS ===
    usar_banco_horas = models.BooleanField(
        default=False,
        help_text='Si True, habilita compensación de tiempo en lugar de pago'
    )
    
    # === METADATA ===
    descripcion = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Política de Empresa'
        verbose_name_plural = 'Políticas de Empresa'
        ordering = ['-vigencia_desde']
    
    def __str__(self):
        return f"Política desde {self.vigencia_desde}"
    
    @classmethod
    def obtener_vigente(cls, fecha):
        """Obtiene la política vigente para una fecha."""
        return cls.objects.filter(
            vigencia_desde__lte=fecha
        ).order_by('-vigencia_desde').first()
