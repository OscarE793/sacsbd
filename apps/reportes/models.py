# apps/reportes/models.py
from django.db import models
from django.utils import timezone
from datetime import datetime

class BackupGenerado(models.Model):
    """Modelo para la tabla BACKUPSGENERADOS"""
    bck_id = models.AutoField(primary_key=True, db_column='BCK_ID')
    servidor = models.CharField(max_length=50, null=True, blank=True, db_column='SERVIDOR')
    database_name = models.CharField(max_length=100, null=True, blank=True, db_column='DatabaseName')
    fecha = models.CharField(max_length=20, null=True, blank=True, db_column='FECHA')
    hora = models.CharField(max_length=20, null=True, blank=True, db_column='HORA')
    type = models.CharField(max_length=20, null=True, blank=True, db_column='TYPE')
    physical_device_name = models.TextField(null=True, blank=True, db_column='physical_device_name')
    ipserver = models.CharField(max_length=50, null=True, blank=True, db_column='IPSERVER')
    
    class Meta:
        db_table = 'BACKUPSGENERADOS'
        managed = False  # Django no administrará esta tabla
        ordering = ['-bck_id']
    
    def __str__(self):
        return f"{self.database_name} - {self.fecha} {self.hora}"
    
    @property
    def fecha_hora_completa(self):
        """Combina fecha y hora en un datetime"""
        try:
            if self.fecha and self.hora:
                # Formato esperado: DD/MM/YYYY HH:MM:SS
                fecha_str = f"{self.fecha} {self.hora}"
                return datetime.strptime(fecha_str, "%d/%m/%Y %H:%M:%S")
        except (ValueError, TypeError):
            pass
        return None
    
    @property
    def tipo_backup_display(self):
        """Descripción amigable del tipo de backup"""
        tipos = {
            'FULL': 'Completo',
            'INCREMENTAL': 'Incremental',
            'DIFF': 'Diferencial',
            'LOG': 'Log de Transacciones'
        }
        return tipos.get(self.type, self.type) if self.type else 'N/A'
    
    @property
    def horas_desde_backup(self):
        """Calcula horas transcurridas desde el backup"""
        fecha_backup = self.fecha_hora_completa
        if fecha_backup:
            delta = timezone.now() - timezone.make_aware(fecha_backup)
            return int(delta.total_seconds() / 3600)
        return None
    
    @property
    def estado_cumplimiento(self):
        """Determina el estado de cumplimiento del backup"""
        horas = self.horas_desde_backup
        if horas is None:
            return 'unknown'
        elif horas <= 24:
            return 'success'
        elif horas <= 48:
            return 'warning'
        else:
            return 'danger'
    
    @property
    def estado_cumplimiento_texto(self):
        """Texto del estado de cumplimiento"""
        estado = self.estado_cumplimiento
        textos = {
            'success': 'En Cumplimiento',
            'warning': 'Advertencia',
            'danger': 'Crítico',
            'unknown': 'Desconocido'
        }
        return textos.get(estado, 'Desconocido')


class JobBackupGenerado(models.Model):
    """Modelo para la tabla JOBSBACKUPGENERADOS"""
    servidor = models.CharField(max_length=100, null=True, blank=True, db_column='SERVIDOR')
    resultado = models.CharField(max_length=50, null=True, blank=True, db_column='RESULTADO')
    fecha_y_hora_inicio = models.DateTimeField(null=True, blank=True, db_column='FECHA_Y_HORA_INICIO')
    nombre_del_job = models.CharField(max_length=100, null=True, blank=True, db_column='NOMBRE_DEL_JOB')
    paso = models.IntegerField(null=True, blank=True, db_column='PASO')
    nombre_del_paso = models.CharField(max_length=100, null=True, blank=True, db_column='NOMBRE_DEL_PASO')
    mensaje = models.TextField(null=True, blank=True, db_column='MENSAJE')
    ipserver = models.CharField(max_length=50, null=True, blank=True, db_column='IPSERVER')
    
    class Meta:
        db_table = 'JOBSBACKUPGENERADOS'
        managed = False  # Django no administrará esta tabla
        ordering = ['-fecha_y_hora_inicio']
    
    def __str__(self):
        return f"{self.nombre_del_job} - {self.resultado}"
    
    @property
    def es_exitoso(self):
        """Determina si el job fue exitoso"""
        if not self.resultado:
            return False
        resultado_lower = self.resultado.lower()
        return 'exitoso' in resultado_lower or 'succeeded' in resultado_lower or 'success' in resultado_lower
    
    @property
    def es_fallido(self):
        """Determina si el job falló"""
        if not self.resultado:
            return False
        resultado_lower = self.resultado.lower()
        return 'fallido' in resultado_lower or 'failed' in resultado_lower or 'error' in resultado_lower
    
    @property
    def css_class(self):
        """Clase CSS según el resultado"""
        if self.es_exitoso:
            return 'success'
        elif self.es_fallido:
            return 'danger'
        else:
            return 'warning'
    
    @property
    def icono(self):
        """Icono según el resultado"""
        if self.es_exitoso:
            return 'ki-check-circle'
        elif self.es_fallido:
            return 'ki-cross-circle'
        else:
            return 'ki-information'
    
    @property
    def resultado_display(self):
        """Resultado formateado para mostrar"""
        if self.es_exitoso:
            return 'Exitoso'
        elif self.es_fallido:
            return 'Fallido'
        else:
            return self.resultado or 'En proceso'


# Modelos para otras tablas mencionadas en los procedimientos
class EstadoDB(models.Model):
    """Modelo para la tabla ESTADODB"""
    class Meta:
        db_table = 'ESTADODB'
        managed = False

class UltimoBCK(models.Model):
    """Modelo para la tabla ULTIMOBCK"""
    class Meta:
        db_table = 'ULTIMOBCK'
        managed = False

class ProgramacionDeBCKS(models.Model):
    """Modelo para la tabla PROGRAMACIONDEBCKS"""
    servidor = models.CharField(max_length=100, db_column='SERVIDOR')
    database_name = models.CharField(max_length=100, db_column='DatabaseName')
    ipserver = models.CharField(max_length=50, db_column='IPSERVER')
    total_programado = models.IntegerField(db_column='TOTALPROGRAM')
    
    class Meta:
        db_table = 'PROGRAMACIONDEBCKS'
        managed = False
