from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import UserProfile, Role, UserRole, AuditLog, SystemSettings


class UserProfileInline(admin.StackedInline):
    fk_name = 'user'
    """Inline para el perfil de usuario"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil'
    fieldsets = (
        ('Información Personal', {
            'fields': ('telefono', 'cargo', 'departamento')
        }),
        ('Configuraciones', {
            'fields': ('tema_preferido',)
        }),
        ('Seguridad', {
            'fields': ('intentos_fallidos', 'bloqueado_hasta', 'cambio_password_requerido', 'ultimo_cambio_password'),
            'classes': ('collapse',)
        }),
        ('Restricciones de Acceso', {
            'fields': ('ip_permitidas', 'horario_acceso_inicio', 'horario_acceso_fin'),
            'classes': ('collapse',)
        }),
    )


class UserRoleInline(admin.TabularInline):
    fk_name = 'user'
    """Inline para los roles de usuario"""
    model = UserRole
    extra = 1
    autocomplete_fields = ['role']
    fields = ('role', 'activo', 'fecha_expiracion')
    readonly_fields = ('fecha_asignacion',)


class UserAdmin(BaseUserAdmin):
    """Admin personalizado para usuarios"""
    inlines = (UserProfileInline, UserRoleInline)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 
                   'is_staff', 'get_roles', 'get_last_login')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 
                  'userrole__role', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    def get_roles(self, obj):
        """Muestra los roles del usuario"""
        roles = UserRole.objects.filter(user=obj, activo=True).select_related('role')
        if roles:
            return ', '.join([ur.role.name for ur in roles])
        return '-'
    get_roles.short_description = 'Roles Activos'
    
    def get_last_login(self, obj):
        """Muestra el último login formateado"""
        if obj.last_login:
            return obj.last_login.strftime('%d/%m/%Y %H:%M')
        return 'Nunca'
    get_last_login.short_description = 'Último Login'
    get_last_login.admin_order_field = 'last_login'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin para roles"""
    list_display = ('name', 'get_permissions_badges', 'get_users_count', 'activo', 
                   'fecha_creacion')
    list_filter = ('activo', 'es_administrador', 'puede_gestionar_usuarios', 
                  'puede_ver_reportes', 'puede_gestionar_backups', 
                  'puede_monitorear_servidores')
    search_fields = ('name', 'description')
    filter_horizontal = ('permissions',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion', 'get_users_list')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'description', 'activo')
        }),
        ('Permisos del Sistema', {
            'fields': ('es_administrador', 'puede_gestionar_usuarios', 
                      'puede_ver_reportes', 'puede_gestionar_backups', 
                      'puede_monitorear_servidores')
        }),
        ('Permisos Específicos', {
            'fields': ('permissions',),
            'classes': ('collapse',)
        }),
        ('Información Adicional', {
            'fields': ('fecha_creacion', 'fecha_modificacion', 'get_users_list'),
            'classes': ('collapse',)
        }),
    )
    
    def get_permissions_badges(self, obj):
        """Muestra badges con los permisos del rol"""
        badges = []
        if obj.es_administrador:
            badges.append('<span class="badge bg-danger">Admin</span>')
        if obj.puede_gestionar_usuarios:
            badges.append('<span class="badge bg-primary">Usuarios</span>')
        if obj.puede_ver_reportes:
            badges.append('<span class="badge bg-info">Reportes</span>')
        if obj.puede_gestionar_backups:
            badges.append('<span class="badge bg-success">Backups</span>')
        if obj.puede_monitorear_servidores:
            badges.append('<span class="badge bg-warning">Servidores</span>')
        
        return format_html(' '.join(badges)) if badges else '-'
    get_permissions_badges.short_description = 'Permisos'
    
    def get_users_count(self, obj):
        """Cuenta de usuarios con este rol"""
        count = UserRole.objects.filter(role=obj, activo=True).count()
        return f"{count} usuario(s)"
    get_users_count.short_description = 'Usuarios Asignados'
    
    def get_users_list(self, obj):
        """Lista de usuarios con este rol"""
        user_roles = UserRole.objects.filter(
            role=obj, 
            activo=True
        ).select_related('user')[:10]
        
        if user_roles:
            users_html = []
            for ur in user_roles:
                user_url = reverse('admin:auth_user_change', args=[ur.user.pk])
                users_html.append(
                    f'<a href="{user_url}">{ur.user.username}</a>'
                )
            
            total = UserRole.objects.filter(role=obj, activo=True).count()
            result = ', '.join(users_html)
            
            if total > 10:
                result += f' ... y {total - 10} más'
            
            return mark_safe(result)
        return '-'
    get_users_list.short_description = 'Usuarios con este Rol'


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Admin para asignaciones de roles"""
    list_display = ('user', 'role', 'activo', 'fecha_asignacion', 
                   'fecha_expiracion', 'asignado_por')
    list_filter = ('activo', 'role', 'fecha_asignacion')
    search_fields = ('user__username', 'user__email', 'role__name')
    autocomplete_fields = ['user', 'role']
    date_hierarchy = 'fecha_asignacion'
    
    fieldsets = (
        ('Asignación', {
            'fields': ('user', 'role', 'activo')
        }),
        ('Detalles', {
            'fields': ('asignado_por', 'fecha_asignacion', 'fecha_expiracion')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editando
            return ('user', 'role', 'fecha_asignacion', 'asignado_por')
        return ('fecha_asignacion',)
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creando
            obj.asignado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin para logs de auditoría"""
    list_display = ('timestamp', 'user', 'action', 'get_description_truncated', 
                   'ip_address', 'affected_user')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'description', 'ip_address', 
                    'affected_user__username')
    date_hierarchy = 'timestamp'
    readonly_fields = ('user', 'action', 'description', 'ip_address', 
                      'user_agent', 'timestamp', 'affected_user', 'metadata')
    
    fieldsets = (
        ('Información del Evento', {
            'fields': ('timestamp', 'user', 'action', 'description')
        }),
        ('Detalles Técnicos', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Información Adicional', {
            'fields': ('affected_user', 'metadata'),
            'classes': ('collapse',)
        }),
    )
    
    def get_description_truncated(self, obj):
        """Trunca la descripción para la lista"""
        if len(obj.description) > 50:
            return obj.description[:50] + '...'
        return obj.description
    get_description_truncated.short_description = 'Descripción'
    
    def has_add_permission(self, request):
        """No permitir agregar logs manualmente"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Solo superusuarios pueden eliminar logs"""
        return request.user.is_superuser


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """Admin para configuraciones del sistema"""
    list_display = ('key', 'get_value_truncated', 'description', 
                   'updated_by', 'updated_at')
    search_fields = ('key', 'description', 'value')
    readonly_fields = ('updated_at',)
    
    fieldsets = (
        (None, {
            'fields': ('key', 'value', 'description')
        }),
        ('Información de Actualización', {
            'fields': ('updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_value_truncated(self, obj):
        """Trunca el valor para la lista"""
        if len(obj.value) > 50:
            return obj.value[:50] + '...'
        return obj.value
    get_value_truncated.short_description = 'Valor'
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# Registrar el UserAdmin personalizado solo si el modelo User está registrado
if admin.site.is_registered(User):
    admin.site.unregister(User)
admin.site.register(User, UserAdmin)