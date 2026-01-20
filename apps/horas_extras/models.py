# apps/horas_extras/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import datetime
from django.utils import timezone


class Empleado(models.Model):
    """Modelo para empleados/operadores del centro de cómputo"""
    
    CARGO_CHOICES = [
        ('operador_junior', 'Operador Centro de Cómputo Junior'),
        ('operador_senior', 'Operador Centro de Cómputo Senior'),
        ('coordinador', 'Coordinador de Turno'),
        ('supervisor', 'Supervisor Centro de Cómputo'),
    ]
    
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('vacaciones', 'En Vacaciones'),
        ('incapacidad', 'En Incapacidad'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    numero_empleado = models.CharField(max_length=20, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20, unique=True)
    cargo = models.CharField(max_length=20, choices=CARGO_CHOICES, default='operador_junior')
    salario_base = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    fecha_ingreso = models.DateField()
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='activo')
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    
    # Campos para cálculos
    valor_hora = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    horas_mensuales = models.IntegerField(default=192, validators=[MinValueValidator(1), MaxValueValidator(300)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
        ordering = ['apellidos', 'nombres']
    
    def __str__(self):
        return f"{self.numero_empleado} - {self.nombres} {self.apellidos}"
    
    def calcular_valor_hora(self):
        """Calcula el valor de la hora basado en el salario base"""
        if self.salario_base and self.horas_mensuales:
            self.valor_hora = self.salario_base / self.horas_mensuales
            return self.valor_hora
        return Decimal('0.00')
    
    def save(self, *args, **kwargs):
        # Calcular valor hora automáticamente
        if self.salario_base and self.horas_mensuales:
            self.valor_hora = self.calcular_valor_hora()
        super().save(*args, **kwargs)


class TipoTurno(models.Model):
    """Tipos de turnos según nueva legislación colombiana 2024"""
    
    TURNO_CHOICES = [
        ('manana', 'Turno Mañana'),
        ('tarde', 'Turno Tarde'), 
        ('noche', 'Turno Noche'),
        ('apoyo', 'Turno Apoyo'),
        ('descanso', 'Día Descanso'),
    ]
    
    nombre = models.CharField(max_length=20, choices=TURNO_CHOICES, unique=True)
    descripcion = models.CharField(max_length=100)
    codigo = models.CharField(max_length=5, unique=True, help_text="Código del turno (M, T, N, A, D)")
    
    # === HORARIOS ESPECÍFICOS POR DÍA DE LA SEMANA ===
    # Martes (1), Miércoles (2), Jueves (3), Viernes (4) - 7 horas
    hora_inicio_martes = models.TimeField(null=True, blank=True)
    hora_fin_martes = models.TimeField(null=True, blank=True)
    horas_martes = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('7.00'))
    
    hora_inicio_miercoles = models.TimeField(null=True, blank=True)
    hora_fin_miercoles = models.TimeField(null=True, blank=True)
    horas_miercoles = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('7.00'))
    
    hora_inicio_jueves = models.TimeField(null=True, blank=True)
    hora_fin_jueves = models.TimeField(null=True, blank=True)
    horas_jueves = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('7.00'))
    
    hora_inicio_viernes = models.TimeField(null=True, blank=True)
    hora_fin_viernes = models.TimeField(null=True, blank=True)
    horas_viernes = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('7.00'))
    
    # Sábado (5), Domingo (6), Lunes (0) - 8 horas
    hora_inicio_sabado = models.TimeField(null=True, blank=True)
    hora_fin_sabado = models.TimeField(null=True, blank=True)
    horas_sabado = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('8.00'))
    
    hora_inicio_domingo = models.TimeField(null=True, blank=True)
    hora_fin_domingo = models.TimeField(null=True, blank=True)
    horas_domingo = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('8.00'))
    
    hora_inicio_lunes = models.TimeField(null=True, blank=True)
    hora_fin_lunes = models.TimeField(null=True, blank=True)
    horas_lunes = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('8.00'))
    
    es_nocturno = models.BooleanField(default=False, help_text="Turno que incluye horario nocturno (10 PM - 6 AM)")
    activo = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Tipo de Turno'
        verbose_name_plural = 'Tipos de Turno'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.get_nombre_display()} ({self.codigo})"
    
    def get_horario_por_dia(self, fecha):
        """Retorna el horario y horas según el día de la semana específico"""
        dia_semana = fecha.weekday()  # 0=Lunes, 1=Martes, 2=Miércoles, 3=Jueves, 4=Viernes, 5=Sábado, 6=Domingo
        
        horarios = {
            0: (self.hora_inicio_lunes, self.hora_fin_lunes, self.horas_lunes),        # Lunes - 8 horas
            1: (self.hora_inicio_martes, self.hora_fin_martes, self.horas_martes),     # Martes - 7 horas
            2: (self.hora_inicio_miercoles, self.hora_fin_miercoles, self.horas_miercoles), # Miércoles - 7 horas
            3: (self.hora_inicio_jueves, self.hora_fin_jueves, self.horas_jueves),     # Jueves - 7 horas
            4: (self.hora_inicio_viernes, self.hora_fin_viernes, self.horas_viernes), # Viernes - 7 horas
            5: (self.hora_inicio_sabado, self.hora_fin_sabado, self.horas_sabado),    # Sábado - 8 horas
            6: (self.hora_inicio_domingo, self.hora_fin_domingo, self.horas_domingo), # Domingo - 8 horas
        }
        
        return horarios.get(dia_semana, (None, None, Decimal('0.00')))
    
    def get_nombre_dia(self, dia_semana):
        """Retorna el nombre del día de la semana"""
        nombres_dias = {
            0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 
            4: 'Viernes', 5: 'Sábado', 6: 'Domingo'
        }
        return nombres_dias.get(dia_semana, '')


class DiaFestivo(models.Model):
    """Días festivos en Colombia según la ley"""
    
    TIPO_CHOICES = [
        ('fijo', 'Fecha Fija'),
        ('lunes_siguiente', 'Lunes Siguiente'),
        ('religioso', 'Religioso Variable'),
        ('puente', 'Puente Festivo'),
    ]
    
    nombre = models.CharField(max_length=100)
    fecha = models.DateField(help_text="Fecha del festivo para el año en curso")
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES, default='fijo')
    es_nacional = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Día Festivo'
        verbose_name_plural = 'Días Festivos'
        ordering = ['fecha']
        unique_together = ['fecha', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} - {self.fecha.strftime('%d/%m/%Y')}"
    
    @classmethod
    def es_festivo(cls, fecha):
        """Verifica si una fecha es festivo"""
        return cls.objects.filter(fecha=fecha, activo=True).exists()
    
    @classmethod
    def obtener_festivos_mes(cls, ano, mes):
        """Obtiene todos los festivos de un mes específico"""
        return cls.objects.filter(
            fecha__year=ano, 
            fecha__month=mes, 
            activo=True
        ).order_by('fecha')


class RegistroTurno(models.Model):
    """Registro de trabajo de empleados en turnos específicos"""
    
    ESTADO_CHOICES = [
        ('programado', 'Programado'),
        ('trabajado', 'Trabajado'),
        ('ausente', 'Ausente'),
        ('reemplazado', 'Reemplazado'),
        ('extra', 'Turno Extra'),
    ]
    
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='turnos')
    tipo_turno = models.ForeignKey(TipoTurno, on_delete=models.CASCADE)
    fecha = models.DateField()
    
    # Horarios reales (pueden diferir del tipo de turno)
    hora_inicio_real = models.TimeField(null=True, blank=True)
    hora_fin_real = models.TimeField(null=True, blank=True)
    
    horas_programadas = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    horas_trabajadas = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='programado')
    
    # Campos para cálculos automáticos
    es_lunes = models.BooleanField(default=False)
    es_martes = models.BooleanField(default=False)
    es_miercoles = models.BooleanField(default=False)
    es_jueves = models.BooleanField(default=False)
    es_viernes = models.BooleanField(default=False)
    es_sabado = models.BooleanField(default=False)
    es_domingo = models.BooleanField(default=False)
    es_festivo = models.BooleanField(default=False)
    incluye_nocturno = models.BooleanField(default=False)
    horas_extras = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    
    observaciones = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Registro de Turno'
        verbose_name_plural = 'Registros de Turno'
        ordering = ['-fecha', 'empleado']
        unique_together = ['empleado', 'fecha', 'tipo_turno']
    
    def __str__(self):
        return f"{self.empleado.nombres} - {self.tipo_turno.codigo} - {self.fecha}"
    
    def save(self, *args, **kwargs):
        # Calcular automáticamente campos por día de la semana
        dia_semana = self.fecha.weekday()
        self.es_lunes = dia_semana == 0
        self.es_martes = dia_semana == 1
        self.es_miercoles = dia_semana == 2
        self.es_jueves = dia_semana == 3
        self.es_viernes = dia_semana == 4
        self.es_sabado = dia_semana == 5
        self.es_domingo = dia_semana == 6
        
        self.es_festivo = DiaFestivo.es_festivo(self.fecha)
        self.incluye_nocturno = self.tipo_turno.es_nocturno
        
        # Obtener horas programadas según el día
        if self.tipo_turno:
            _, _, horas_dia = self.tipo_turno.get_horario_por_dia(self.fecha)
            self.horas_programadas = horas_dia
        
        # Calcular horas trabajadas si no están definidas
        if not self.horas_trabajadas and self.hora_inicio_real and self.hora_fin_real:
            inicio = datetime.datetime.combine(self.fecha, self.hora_inicio_real)
            fin = datetime.datetime.combine(self.fecha, self.hora_fin_real)
            
            # Si el turno termina al día siguiente
            if self.hora_fin_real < self.hora_inicio_real:
                fin += datetime.timedelta(days=1)
            
            duracion = fin - inicio
            self.horas_trabajadas = Decimal(str(duracion.total_seconds() / 3600))
        
        # Calcular horas extras (más de las horas programadas)
        if self.horas_trabajadas > self.horas_programadas:
            self.horas_extras = self.horas_trabajadas - self.horas_programadas
        else:
            self.horas_extras = Decimal('0.00')
        
        super().save(*args, **kwargs)


class CalculoRecargo(models.Model):
    """Cálculos de recargos y horas extras según legislación colombiana actualizada"""
    
    registro_turno = models.OneToOneField(RegistroTurno, on_delete=models.CASCADE, related_name='calculo')
    
    # Valores base
    valor_hora_base = models.DecimalField(max_digits=10, decimal_places=2)
    horas_ordinarias = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    
    # === RECARGOS SEGÚN LEGISLACIÓN COLOMBIANA ===
    # RNO - Recargo Nocturno Ordinario (35%)
    horas_recargo_nocturno = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    valor_recargo_nocturno = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # RDF - Recargo Dominical y Festivo (75%)
    horas_recargo_dominical = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    valor_recargo_dominical = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    horas_recargo_festivo = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    valor_recargo_festivo = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # RNF - Recargo Nocturno Festivo (110% = 35% nocturno + 75% festivo)
    horas_recargo_nocturno_festivo = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    valor_recargo_nocturno_festivo = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # === HORAS EXTRAS ===
    # HEDO - Horas Extra Diurnas Ordinarias (25%)
    horas_extras_diurnas_ordinarias = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    valor_horas_extras_diurnas_ordinarias = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # HENO - Horas Extra Nocturnas Ordinarias (75%)
    horas_extras_nocturnas_ordinarias = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    valor_horas_extras_nocturnas_ordinarias = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # HEDF - Horas Extra Diurnas Festivas (100%)
    horas_extras_diurnas_festivas = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    valor_horas_extras_diurnas_festivas = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # HENF - Horas Extra Nocturnas Festivas (150%)
    horas_extras_nocturnas_festivas = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    valor_horas_extras_nocturnas_festivas = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Totales
    total_ordinario = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_recargos = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_horas_extras = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_a_pagar = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    fecha_calculo = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Cálculo de Recargo'
        verbose_name_plural = 'Cálculos de Recargos'
        ordering = ['-fecha_calculo']
    
    def __str__(self):
        return f"Recargo {self.registro_turno.empleado.nombres} - {self.registro_turno.fecha}"
    
    def calcular_recargos(self):
        """Calcula todos los recargos según la nueva legislación colombiana"""
        
        # Obtener valor hora base
        self.valor_hora_base = self.registro_turno.empleado.valor_hora or Decimal('0.00')
        
        # Resetear todos los valores
        self._resetear_valores()
        
        registro = self.registro_turno
        horas_trabajadas = registro.horas_trabajadas
        horas_extras_total = registro.horas_extras
        horas_programadas = registro.horas_programadas
        
        # Determinar tipo de día
        es_domingo = registro.es_domingo
        es_festivo = registro.es_festivo
        incluye_nocturno = registro.incluye_nocturno
        
        # Calcular horas ordinarias (hasta las horas programadas)
        self.horas_ordinarias = min(horas_trabajadas, horas_programadas)
        
        # === APLICAR RECARGOS SEGÚN EL TIPO DE DÍA ===
        if es_festivo:
            if incluye_nocturno:
                # Festivo nocturno: RNF (110%)
                self.horas_recargo_nocturno_festivo = self.horas_ordinarias
                if horas_extras_total > 0:
                    self.horas_extras_nocturnas_festivas = horas_extras_total
            else:
                # Festivo diurno: RDF (75%)
                self.horas_recargo_festivo = self.horas_ordinarias
                if horas_extras_total > 0:
                    self.horas_extras_diurnas_festivas = horas_extras_total
        
        elif es_domingo:
            if incluye_nocturno:
                # Domingo nocturno: RDF (75%) + RNO (35%) 
                self.horas_recargo_dominical = self.horas_ordinarias
                self.horas_recargo_nocturno = self.horas_ordinarias
                if horas_extras_total > 0:
                    self.horas_extras_nocturnas_ordinarias = horas_extras_total
            else:
                # Domingo diurno: RDF (75%)
                self.horas_recargo_dominical = self.horas_ordinarias
                if horas_extras_total > 0:
                    self.horas_extras_diurnas_ordinarias = horas_extras_total
        
        else:
            # Día ordinario (lunes a sábado)
            if incluye_nocturno:
                # Ordinario nocturno: RNO (35%)
                self.horas_recargo_nocturno = self.horas_ordinarias
                if horas_extras_total > 0:
                    self.horas_extras_nocturnas_ordinarias = horas_extras_total
            else:
                # Ordinario diurno: sin recargos base
                if horas_extras_total > 0:
                    self.horas_extras_diurnas_ordinarias = horas_extras_total
        
        # Calcular valores monetarios
        self._calcular_valores_monetarios()
        
        # Calcular totales
        self._calcular_totales()
        
        return self.total_a_pagar
    
    def _resetear_valores(self):
        """Resetea todos los valores de recargos y horas extras"""
        campos_reset = [
            'horas_ordinarias', 'horas_recargo_nocturno', 'valor_recargo_nocturno',
            'horas_recargo_dominical', 'valor_recargo_dominical', 'horas_recargo_festivo',
            'valor_recargo_festivo', 'horas_recargo_nocturno_festivo', 'valor_recargo_nocturno_festivo',
            'horas_extras_diurnas_ordinarias', 'valor_horas_extras_diurnas_ordinarias',
            'horas_extras_nocturnas_ordinarias', 'valor_horas_extras_nocturnas_ordinarias',
            'horas_extras_diurnas_festivas', 'valor_horas_extras_diurnas_festivas',
            'horas_extras_nocturnas_festivas', 'valor_horas_extras_nocturnas_festivas'
        ]
        
        for campo in campos_reset:
            setattr(self, campo, Decimal('0.00'))
    
    def _calcular_valores_monetarios(self):
        """Calcula los valores monetarios de recargos según porcentajes legales actualizados"""
        
        # === RECARGOS BASE ===
        # RNO - Recargo Nocturno Ordinario: 35% adicional
        self.valor_recargo_nocturno = self.horas_recargo_nocturno * self.valor_hora_base * Decimal('0.35')
        
        # RDF - Recargo Dominical y Festivo: 75% adicional
        self.valor_recargo_dominical = self.horas_recargo_dominical * self.valor_hora_base * Decimal('0.75')
        self.valor_recargo_festivo = self.horas_recargo_festivo * self.valor_hora_base * Decimal('0.75')
        
        # RNF - Recargo Nocturno Festivo: 110% adicional (35% + 75%)
        self.valor_recargo_nocturno_festivo = self.horas_recargo_nocturno_festivo * self.valor_hora_base * Decimal('1.10')
        
        # === HORAS EXTRAS ===
        # HEDO - Horas Extra Diurnas Ordinarias: 125% del valor hora (25% adicional)
        self.valor_horas_extras_diurnas_ordinarias = self.horas_extras_diurnas_ordinarias * self.valor_hora_base * Decimal('1.25')
        
        # HENO - Horas Extra Nocturnas Ordinarias: 175% del valor hora (75% adicional)
        self.valor_horas_extras_nocturnas_ordinarias = self.horas_extras_nocturnas_ordinarias * self.valor_hora_base * Decimal('1.75')
        
        # HEDF - Horas Extra Diurnas Festivas: 200% del valor hora (100% adicional)
        self.valor_horas_extras_diurnas_festivas = self.horas_extras_diurnas_festivas * self.valor_hora_base * Decimal('2.00')
        
        # HENF - Horas Extra Nocturnas Festivas: 250% del valor hora (150% adicional)
        self.valor_horas_extras_nocturnas_festivas = self.horas_extras_nocturnas_festivas * self.valor_hora_base * Decimal('2.50')
    
    def _calcular_totales(self):
        """Calcula los valores totales"""
        
        # Total ordinario (horas base sin recargos)
        self.total_ordinario = self.horas_ordinarias * self.valor_hora_base
        
        # Total recargos
        self.total_recargos = (
            self.valor_recargo_nocturno + 
            self.valor_recargo_dominical + 
            self.valor_recargo_festivo +
            self.valor_recargo_nocturno_festivo
        )
        
        # Total horas extras
        self.total_horas_extras = (
            self.valor_horas_extras_diurnas_ordinarias +
            self.valor_horas_extras_nocturnas_ordinarias +
            self.valor_horas_extras_diurnas_festivas +
            self.valor_horas_extras_nocturnas_festivas
        )
        
        # Total a pagar
        self.total_a_pagar = self.total_ordinario + self.total_recargos + self.total_horas_extras


class ResumenMensual(models.Model):
    """Resumen mensual de horas y recargos por empleado"""
    
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='resumenes')
    mes = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    ano = models.IntegerField(validators=[MinValueValidator(2020)])
    
    # Totales de horas
    total_horas_trabajadas = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    total_horas_ordinarias = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    total_horas_extras = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    total_turnos = models.IntegerField(default=0)
    
    # Totales por tipo de día
    horas_lunes = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    horas_martes = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    horas_miercoles = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    horas_jueves = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    horas_viernes = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    horas_sabados = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    horas_domingos = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    horas_festivos = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    
    # Totales de recargos
    total_recargos_nocturnos = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_recargos_dominicales = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_recargos_festivos = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_recargos_nocturno_festivo = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Totales monetarios
    total_valor_ordinario = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_valor_recargos = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_valor_horas_extras = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_a_pagar = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Resumen Mensual'
        verbose_name_plural = 'Resúmenes Mensuales'
        ordering = ['-ano', '-mes', 'empleado']
        unique_together = ['empleado', 'mes', 'ano']
    
    def __str__(self):
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        mes_nombre = meses[self.mes] if 1 <= self.mes <= 12 else str(self.mes)
        return f"{self.empleado.nombres} - {mes_nombre} {self.ano}"
    
    def generar_resumen(self):
        """Genera el resumen mensual basado en los registros de turnos"""
        from django.db.models import Sum, Count
        
        # Obtener todos los registros del mes
        registros = RegistroTurno.objects.filter(
            empleado=self.empleado,
            fecha__year=self.ano,
            fecha__month=self.mes,
            estado='trabajado'
        ).prefetch_related('calculo')
        
        # Resetear valores
        self._resetear_totales()
        
        # Calcular totales
        for registro in registros:
            self.total_turnos += 1
            self.total_horas_trabajadas += registro.horas_trabajadas
            self.total_horas_ordinarias += registro.horas_programadas
            self.total_horas_extras += registro.horas_extras
            
            # Horas por día de la semana
            if registro.es_lunes:
                self.horas_lunes += registro.horas_trabajadas
            elif registro.es_martes:
                self.horas_martes += registro.horas_trabajadas
            elif registro.es_miercoles:
                self.horas_miercoles += registro.horas_trabajadas
            elif registro.es_jueves:
                self.horas_jueves += registro.horas_trabajadas
            elif registro.es_viernes:
                self.horas_viernes += registro.horas_trabajadas
            elif registro.es_sabado:
                self.horas_sabados += registro.horas_trabajadas
            elif registro.es_domingo:
                self.horas_domingos += registro.horas_trabajadas
            
            if registro.es_festivo:
                self.horas_festivos += registro.horas_trabajadas
            
            # Sumar valores monetarios del cálculo
            if hasattr(registro, 'calculo'):
                calculo = registro.calculo
                self.total_valor_ordinario += calculo.total_ordinario
                self.total_valor_recargos += calculo.total_recargos
                self.total_valor_horas_extras += calculo.total_horas_extras
                
                self.total_recargos_nocturnos += calculo.valor_recargo_nocturno
                self.total_recargos_dominicales += calculo.valor_recargo_dominical
                self.total_recargos_festivos += calculo.valor_recargo_festivo
                self.total_recargos_nocturno_festivo += calculo.valor_recargo_nocturno_festivo
        
        # Total a pagar
        self.total_a_pagar = self.total_valor_ordinario + self.total_valor_recargos + self.total_valor_horas_extras
        
        self.save()
        return self
    
    def _resetear_totales(self):
        """Resetea todos los totales antes de recalcular"""
        campos_reset = [
            'total_horas_trabajadas', 'total_horas_ordinarias', 'total_horas_extras', 'total_turnos',
            'horas_lunes', 'horas_martes', 'horas_miercoles', 'horas_jueves', 'horas_viernes',
            'horas_sabados', 'horas_domingos', 'horas_festivos',
            'total_recargos_nocturnos', 'total_recargos_dominicales', 'total_recargos_festivos',
            'total_recargos_nocturno_festivo', 'total_valor_ordinario', 'total_valor_recargos',
            'total_valor_horas_extras', 'total_a_pagar'
        ]
        
        for campo in campos_reset:
            setattr(self, campo, Decimal('0.00') if 'total_turnos' not in campo else 0)
