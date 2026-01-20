from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.core.validators import RegexValidator
import os

class UserProfile(models.Model):
    """Perfil extendido de usuario"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Información personal
    telefono = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="El teléfono debe tener entre 9 y 15 dígitos."
        )]
    )
    cargo = models.CharField(max_length=100, blank=True, null=True)
    departamento = models.CharField(max_length=100, blank=True, null=True)
    
    # Configuraciones de sistema
    tema_preferido = models.CharField(
        max_length=20,
        choices=[
            ('light', 'Claro'),
            ('dark', 'Oscuro'),
            ('auto', 'Automático'),
        ],
        default='light'
    )
    
    # Metadatos de seguimiento
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='perfiles_creados'
    )
    
    # Configuraciones de seguridad
    intentos_fallidos = models.IntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)
    cambio_password_requerido = models.BooleanField(default=False)
    ultimo_cambio_password = models.DateTimeField(null=True, blank=True)
    
    # Configuraciones de acceso
    ip_permitidas = models.TextField(
        blank=True, 
        null=True,
        help_text="Lista de IPs permitidas separadas por comas"
    )
    horario_acceso_inicio = models.TimeField(null=True, blank=True)
    horario_acceso_fin = models.TimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"
        
    def __str__(self):
        return f"Perfil de {self.user.username}"
    
    def get_full_name(self):
        """Obtiene el nombre completo del usuario"""
        return self.user.get_full_name() or self.user.username
    
    def is_blocked(self):
        """Verifica si el usuario está bloqueado"""
        if self.bloqueado_hasta:
            return timezone.now() < self.bloqueado_hasta
        return False
    
    def reset_failed_attempts(self):
        """Resetea los intentos fallidos"""
        self.intentos_fallidos = 0
        self.bloqueado_hasta = None
        self.save()
    
    def increment_failed_attempts(self):
        """Incrementa los intentos fallidos y bloquea si es necesario"""
        self.intentos_fallidos += 1
        if self.intentos_fallidos >= 5:  # Bloquear después de 5 intentos
            self.bloqueado_hasta = timezone.now() + timezone.timedelta(minutes=30)
        self.save()
    
    def can_access_from_ip(self, ip_address):
        """Verifica si puede acceder desde una IP específica"""
        if not self.ip_permitidas:
            return True
        allowed_ips = [ip.strip() for ip in self.ip_permitidas.split(',')]
        return ip_address in allowed_ips
    
    def can_access_at_time(self, current_time=None):
        """Verifica si puede acceder en el horario actual"""
        if not self.horario_acceso_inicio or not self.horario_acceso_fin:
            return True
        
        if current_time is None:
            current_time = timezone.now().time()
        
        return self.horario_acceso_inicio <= current_time <= self.horario_acceso_fin


class Role(models.Model):
    """Roles personalizados del sistema"""
    name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True, null=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    
    # Configuraciones del rol
    es_administrador = models.BooleanField(default=False)
    puede_gestionar_usuarios = models.BooleanField(default=False)
    puede_ver_reportes = models.BooleanField(default=True)
    puede_gestionar_backups = models.BooleanField(default=False)
    puede_monitorear_servidores = models.BooleanField(default=False)
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        
    def __str__(self):
        return self.name
    
    def get_users_count(self):
        """Obtiene el número de usuarios con este rol"""
        return self.user_set.count()


class UserRole(models.Model):
    """Relación entre usuarios y roles"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    asignado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='roles_asignados'
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Asignación de Rol"
        verbose_name_plural = "Asignaciones de Roles"
        unique_together = ('user', 'role')
        
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"
    
    def is_expired(self):
        """Verifica si la asignación ha expirado"""
        if self.fecha_expiracion:
            return timezone.now() > self.fecha_expiracion
        return False


class AuditLog(models.Model):
    """Log de auditoría para acciones de usuarios"""
    ACTIONS = [
        ('login', 'Inicio de sesión'),
        ('logout', 'Cierre de sesión'),
        ('create_user', 'Crear usuario'),
        ('update_user', 'Actualizar usuario'),
        ('delete_user', 'Eliminar usuario'),
        ('change_password', 'Cambiar contraseña'),
        ('assign_role', 'Asignar rol'),
        ('remove_role', 'Remover rol'),
        ('view_report', 'Ver reporte'),
        ('export_data', 'Exportar datos'),
        ('system_access', 'Acceso al sistema'),
        ('failed_login', 'Intento de login fallido'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50, choices=ACTIONS)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Información adicional
    affected_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs_affected'
    )
    metadata = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Log de Auditoría"
        verbose_name_plural = "Logs de Auditoría"
        ordering = ['-timestamp']
        
    def __str__(self):
        user_name = self.user.username if self.user else "Usuario desconocido"
        return f"{user_name} - {self.get_action_display()} - {self.timestamp}"


class SystemSettings(models.Model):
    """Configuraciones del sistema de usuarios"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.CharField(max_length=255, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"
        
    def __str__(self):
        return f"{self.key}: {self.value[:50]}"


# Función para crear perfil automáticamente
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crea automáticamente un perfil cuando se crea un usuario"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Guarda el perfil cuando se guarda el usuario"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
