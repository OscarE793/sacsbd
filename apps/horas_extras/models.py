# apps/horas_extras/models.py - VERSIÓN SIMPLIFICADA
#
# IMPORTANTE: Este sistema SOLO calcula horas trabajadas
# Los valores en pesos los calcula el departamento de nómina
# Los operadores se gestionan desde el panel de user_management con rol "operador de centro de computo"

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import datetime
from django.utils import timezone


class TipoTurno(models.Model):
    """Tipos de turnos según especificaciones del sistema"""

    TURNO_CHOICES = [
        ('manana', 'Turno Mañana'),
        ('tarde', 'Turno Tarde'),
        ('noche', 'Turno Noche'),
        ('noche_w1', 'Noche Miércoles 1h'),
        ('noche_w2', 'Noche Miércoles 6h'),
        ('apoyo', 'Turno Apoyo'),
        ('descanso', 'Día Descanso'),
    ]

    nombre = models.CharField(max_length=20, choices=TURNO_CHOICES, unique=True)
    descripcion = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True, help_text='Código del turno (ej: Apoyo-A, Turno 1-M, etc.)')

    # Horarios por día de semana
    hora_inicio_lunes = models.TimeField(null=True, blank=True)
    hora_fin_lunes = models.TimeField(null=True, blank=True)
    horas_lunes = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('8.00'))

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

    hora_inicio_sabado = models.TimeField(null=True, blank=True)
    hora_fin_sabado = models.TimeField(null=True, blank=True)
    horas_sabado = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('8.00'))

    hora_inicio_domingo = models.TimeField(null=True, blank=True)
    hora_fin_domingo = models.TimeField(null=True, blank=True)
    horas_domingo = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('8.00'))

    es_nocturno = models.BooleanField(default=False, help_text='Turno que incluye horario nocturno')
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tipo de Turno'
        verbose_name_plural = 'Tipos de Turno'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"

    def get_horario_por_dia(self, fecha):
        """Obtiene el horario específico para un día de la semana"""
        dia_semana = fecha.weekday()  # 0=Lun, 1=Mar, ..., 6=Dom

        horarios = {
            0: (self.hora_inicio_lunes, self.hora_fin_lunes, self.horas_lunes),
            1: (self.hora_inicio_martes, self.hora_fin_martes, self.horas_martes),
            2: (self.hora_inicio_miercoles, self.hora_fin_miercoles, self.horas_miercoles),
            3: (self.hora_inicio_jueves, self.hora_fin_jueves, self.horas_jueves),
            4: (self.hora_inicio_viernes, self.hora_fin_viernes, self.horas_viernes),
            5: (self.hora_inicio_sabado, self.hora_fin_sabado, self.horas_sabado),
            6: (self.hora_inicio_domingo, self.hora_fin_domingo, self.horas_domingo),
        }

        return horarios.get(dia_semana, (None, None, Decimal('0.00')))


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
    """
    Registro de trabajo de operadores en turnos específicos

    IMPORTANTE: Vinculado directamente a User (no a Empleado)
    El operador debe tener el rol "operador de centro de computo" en user_management
    """

    ESTADO_CHOICES = [
        ('programado', 'Programado'),
        ('trabajado', 'Trabajado'),
        ('ausente', 'Ausente'),
        ('reemplazado', 'Reemplazado'),
        ('extra', 'Turno Extra'),
    ]

    # Vinculado directamente a User del sistema unificado
    operador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='turnos',
        verbose_name='Operador',
        help_text='Usuario con rol de operador de centro de computo'
    )
    tipo_turno = models.ForeignKey(TipoTurno, on_delete=models.CASCADE)
    fecha = models.DateField()

    # Horarios reales
    hora_inicio_real = models.TimeField(null=True, blank=True)
    hora_fin_real = models.TimeField(null=True, blank=True)

    horas_programadas = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    horas_trabajadas = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='programado')

    # Campos para clasificación (calculados automáticamente)
    es_lunes = models.BooleanField(default=False)
    es_martes = models.BooleanField(default=False)
    es_miercoles = models.BooleanField(default=False)
    es_jueves = models.BooleanField(default=False)
    es_viernes = models.BooleanField(default=False)
    es_sabado = models.BooleanField(default=False)
    es_domingo = models.BooleanField(default=False)
    es_festivo = models.BooleanField(default=False)
    incluye_nocturno = models.BooleanField(default=False)

    observaciones = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Registro de Turno'
        verbose_name_plural = 'Registros de Turno'
        ordering = ['-fecha', 'operador']
        unique_together = ['operador', 'fecha']

    def __str__(self):
        return f"{self.operador.get_full_name() or self.operador.username} - {self.tipo_turno.codigo} - {self.fecha}"

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

        super().save(*args, **kwargs)


class ResumenMensual(models.Model):
    """
    Resumen mensual de horas trabajadas por operador

    IMPORTANTE: Solo calcula HORAS, no valores en pesos
    Los valores monetarios los calcula nómina con sus propias tablas
    """

    operador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumenes_turnos')
    mes = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    ano = models.IntegerField(validators=[MinValueValidator(2020)])

    # Totales de horas (SOLO HORAS, no dinero)
    total_horas_trabajadas = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    total_horas_ordinarias = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    total_turnos = models.IntegerField(default=0)

    # Horas por tipo de día
    horas_lunes = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    horas_martes = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    horas_miercoles = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    horas_jueves = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    horas_viernes = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    horas_sabados = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    horas_domingos = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    horas_festivos = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))

    # Horas por tipo de turno
    horas_nocturnas = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    horas_nocturnas_festivas = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    horas_dominicales = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))

    fecha_calculo = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Resumen Mensual'
        verbose_name_plural = 'Resúmenes Mensuales'
        ordering = ['-ano', '-mes']
        unique_together = ['operador', 'mes', 'ano']

    def __str__(self):
        return f"{self.operador.get_full_name()} - {self.mes}/{self.ano}"

    def calcular_resumen(self):
        """Calcula el resumen de horas del mes"""
        from django.db.models import Sum

        turnos = RegistroTurno.objects.filter(
            operador=self.operador,
            fecha__year=self.ano,
            fecha__month=self.mes,
            estado='trabajado'
        )

        self.total_turnos = turnos.count()
        self.total_horas_trabajadas = turnos.aggregate(Sum('horas_trabajadas'))['horas_trabajadas__sum'] or Decimal('0.00')
        self.total_horas_ordinarias = self.total_horas_trabajadas  # No hay extras en este sistema

        # Por día de semana
        self.horas_lunes = turnos.filter(es_lunes=True).aggregate(Sum('horas_trabajadas'))['horas_trabajadas__sum'] or Decimal('0.00')
        self.horas_martes = turnos.filter(es_martes=True).aggregate(Sum('horas_trabajadas'))['horas_trabajadas__sum'] or Decimal('0.00')
        self.horas_miercoles = turnos.filter(es_miercoles=True).aggregate(Sum('horas_trabajadas'))['horas_trabajadas__sum'] or Decimal('0.00')
        self.horas_jueves = turnos.filter(es_jueves=True).aggregate(Sum('horas_trabajadas'))['horas_trabajadas__sum'] or Decimal('0.00')
        self.horas_viernes = turnos.filter(es_viernes=True).aggregate(Sum('horas_trabajadas'))['horas_trabajadas__sum'] or Decimal('0.00')
        self.horas_sabados = turnos.filter(es_sabado=True).aggregate(Sum('horas_trabajadas'))['horas_trabajadas__sum'] or Decimal('0.00')
        self.horas_domingos = turnos.filter(es_domingo=True).aggregate(Sum('horas_trabajadas'))['horas_trabajadas__sum'] or Decimal('0.00')

        # Por tipo especial
        self.horas_festivos = turnos.filter(es_festivo=True).aggregate(Sum('horas_trabajadas'))['horas_trabajadas__sum'] or Decimal('0.00')
        self.horas_nocturnas = turnos.filter(incluye_nocturno=True).aggregate(Sum('horas_trabajadas'))['horas_trabajadas__sum'] or Decimal('0.00')
        self.horas_nocturnas_festivas = turnos.filter(incluye_nocturno=True, es_festivo=True).aggregate(Sum('horas_trabajadas'))['horas_trabajadas__sum'] or Decimal('0.00')
        self.horas_dominicales = turnos.filter(es_domingo=True).aggregate(Sum('horas_trabajadas'))['horas_trabajadas__sum'] or Decimal('0.00')

        self.save()
        return self


class PatronOperador(models.Model):
    """
    Almacena los "seeds" (puntos de inicio) del patrón de turnos por operador.
    
    REGLA CLAVE:
    - Un operador puede tener MÚLTIPLES seeds (uno por cada cambio de patrón)
    - Vacaciones, reubicaciones, rotaciones manuales crean nuevos seeds
    - Para una fecha dada, se usa el seed más reciente con fecha_inicio <= fecha
    
    El patrón es GLOBAL (T=7, N=8, D=6, M=7 = 28 días),
    pero cada operador puede tener múltiples puntos de referencia.
    """
    
    TURNO_CHOICES = [
        ('T', 'Tarde'),
        ('N', 'Noche'),
        ('D', 'Descanso'),
        ('M', 'Mañana'),
        ('A', 'Apoyo'),
    ]
    
    operador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='patrones_turno',
        help_text='Operador al que pertenece este patrón'
    )
    
    fecha_inicio_patron = models.DateField(
        help_text='Fecha donde comienza a aplicarse este patrón'
    )
    
    turno_inicial_patron = models.CharField(
        max_length=1,
        choices=TURNO_CHOICES,
        help_text='Turno que el operador tiene en fecha_inicio_patron'
    )
    
    es_solo_referencia = models.BooleanField(
        default=True,
        help_text="Este patrón solo se usa como referencia visual, NO genera turnos automáticamente"
    )

    motivo = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text='Motivo del cambio (vacaciones, reubicación, etc.)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Patrón de Operador'
        verbose_name_plural = 'Patrones de Operadores'
        ordering = ['-fecha_inicio_patron']  # Más reciente primero
        unique_together = ['operador', 'fecha_inicio_patron']
    
    def __str__(self):
        return f"{self.operador.get_full_name()} - {self.turno_inicial_patron} desde {self.fecha_inicio_patron}"
    
    @classmethod
    def obtener_seed_vigente(cls, operador, fecha):
        """
        Obtiene el seed vigente para un operador en una fecha específica.
        
        Busca el PatronOperador más reciente del operador
        con fecha_inicio_patron <= fecha
        
        Returns: PatronOperador o None si no existe
        """
        return cls.objects.filter(
            operador=operador,
            fecha_inicio_patron__lte=fecha
        ).order_by('-fecha_inicio_patron').first()
    
    @classmethod
    def calcular_turno_para_fecha(cls, operador, fecha):
        """
        Calcula el turno de un operador para una fecha específica.
        Usa el seed vigente para esa fecha.
        
        Returns: código de turno ('T', 'N', 'D', 'M') o None si no hay seed
        """
        seed = cls.obtener_seed_vigente(operador, fecha)
        if not seed:
            return None
        return seed.calcular_turno_fecha(fecha)
    
    def calcular_turno_fecha(self, fecha):
        """
        Calcula el turno que corresponde a una fecha específica
        usando ESTE seed como referencia.
        
        TURNOS FIJOS (no rotan):
        - A (Apoyo): se mantiene fijo hasta que haya otro seed
        
        TURNOS CÍCLICOS:
        - Usa el patrón global: T(7) + N(8) + D(6) + M(7) = 28 días
        """
        from datetime import timedelta
        
        # Turno A (Apoyo) es FIJO - no rota
        if self.turno_inicial_patron == 'A':
            return 'A'
        
        ciclos_config = [
            ('T', 7),   # días 0-6
            ('N', 8),   # días 7-14
            ('D', 6),   # días 15-20
            ('M', 7),   # días 21-27
        ]
        ciclo_total = 28
        
        # Calcular offset inicial basado en turno_inicial_patron
        offset_inicial = 0
        for codigo, duracion in ciclos_config:
            if codigo == self.turno_inicial_patron:
                break
            offset_inicial += duracion
        
        # Calcular posición en ciclo de 28 días
        dias_desde_inicio = (fecha - self.fecha_inicio_patron).days
        pos_en_ciclo = (dias_desde_inicio + offset_inicial) % ciclo_total
        
        # Determinar turno
        pos_acumulada = 0
        for codigo, duracion in ciclos_config:
            if pos_en_ciclo < pos_acumulada + duracion:
                return codigo
            pos_acumulada += duracion
        
        return 'D'  # fallback


