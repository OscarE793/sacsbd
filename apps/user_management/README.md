# Módulo de Gestión de Usuarios y Permisos

Este módulo proporciona un sistema completo de gestión de usuarios, roles y permisos para SACSBD.

## Características

### 1. Gestión de Usuarios
- **Perfiles extendidos**: Información adicional como teléfono, cargo, departamento
- **Control de acceso**: Restricciones por IP y horario
- **Seguridad mejorada**: Bloqueo por intentos fallidos, cambio de contraseña obligatorio
- **Auditoría completa**: Registro de todas las acciones de usuarios

### 2. Sistema de Roles
- **Roles personalizados**: Crear roles con permisos específicos
- **Permisos granulares**: Control detallado sobre cada funcionalidad
- **Asignación flexible**: Usuarios pueden tener múltiples roles
- **Expiración temporal**: Los roles pueden tener fecha de vencimiento

### 3. Auditoría y Seguridad
- **Logs detallados**: Registro de login, logout, cambios, accesos
- **Tracking de IP**: Registro de direcciones IP en cada acción
- **Intentos fallidos**: Bloqueo automático después de múltiples intentos
- **Headers de seguridad**: CSP, XSS Protection, etc.

## Instalación

1. Asegúrate de que la aplicación esté en `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ...
    'apps.user_management',
    # ...
]
```

2. Agrega los middleware necesarios:
```python
MIDDLEWARE = [
    # ...
    'apps.user_management.middleware.SecurityHeadersMiddleware',
    'apps.user_management.middleware.UserTrackingMiddleware',
    'apps.user_management.middleware.SessionTimeoutMiddleware',
    # ...
]
```

3. Agrega los context processors:
```python
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                # ...
                'apps.user_management.context_processors.user_permissions',
                'apps.user_management.context_processors.system_info',
                # ...
            ],
        },
    },
]
```

4. Ejecuta las migraciones:
```bash
python manage.py makemigrations user_management
python manage.py migrate
```

5. Inicializa los roles por defecto:
```bash
python manage.py init_roles
```

6. Crea un superusuario con perfil completo:
```bash
python manage.py create_admin --username admin --email admin@example.com
```

## Uso

### En las Vistas

#### Usando decoradores de permisos:
```python
from apps.user_management.decorators import require_permission, admin_required

@require_permission('puede_gestionar_usuarios')
def gestionar_usuarios(request):
    # Solo usuarios con permiso pueden acceder
    pass

@admin_required
def configuracion_sistema(request):
    # Solo administradores pueden acceder
    pass
```

#### Verificando permisos manualmente:
```python
from apps.user_management.utils import has_permission

def mi_vista(request):
    if has_permission(request.user, 'puede_ver_reportes'):
        # Mostrar reportes
        pass
```

### En los Templates

#### Usando template tags:
```django
{% load user_tags %}

{% if user|has_perm:"puede_gestionar_backups" %}
    <a href="{% url 'backup:list' %}">Gestionar Backups</a>
{% endif %}

<!-- Mostrar nombre del usuario -->
{{ user|user_display_name }}

<!-- Mostrar badges de permisos -->
{% permission_badges user %}
```

### Logging de Acciones

El sistema registra automáticamente:
- Inicios de sesión exitosos y fallidos
- Cierres de sesión
- Cambios en usuarios y roles
- Accesos a secciones protegidas

Para registrar acciones personalizadas:
```python
from apps.user_management.utils import log_user_action

log_user_action(
    request.user,
    'custom_action',
    'Descripción de la acción',
    request,
    affected_user=otro_usuario  # Opcional
)
```

## Configuración

### Settings disponibles:

```python
# Timeout de sesión en segundos (default: 1800 = 30 minutos)
SESSION_TIMEOUT = 1800

# Nombre del sistema
SYSTEM_NAME = 'SACSBD'

# Versión del sistema
SYSTEM_VERSION = '1.0.0'
```

## Roles por Defecto

El comando `init_roles` crea los siguientes roles:

1. **Administrador**: Acceso total al sistema
2. **Operador de Reportes**: Puede ver y generar reportes
3. **Operador de Backups**: Puede gestionar copias de seguridad
4. **Monitor de Servidores**: Puede ver estado de servidores
5. **Usuario Básico**: Solo lectura de reportes

## Modelos

### UserProfile
Extiende el modelo User de Django con:
- Información personal (teléfono, cargo, departamento)
- Configuraciones (tema preferido)
- Seguridad (intentos fallidos, bloqueos)
- Restricciones (IPs permitidas, horarios)

### Role
Define roles personalizados con:
- Permisos del sistema (booleanos)
- Permisos específicos de Django
- Metadatos (activo, fechas)

### UserRole
Relación muchos a muchos entre usuarios y roles:
- Asignación con fecha
- Posibilidad de expiración
- Registro de quién asignó el rol

### AuditLog
Registro completo de actividades:
- Usuario, acción, descripción
- IP, user agent
- Usuario afectado (si aplica)
- Metadatos adicionales en JSON

## Comandos de Gestión

### init_roles
```bash
python manage.py init_roles [--force]
```
Crea los roles por defecto. Con `--force` desactiva roles existentes.

### create_admin
```bash
python manage.py create_admin --username USUARIO --email EMAIL [opciones]
```
Crea un superusuario con perfil completo y rol de administrador.

## Middleware

### UserTrackingMiddleware
- Verifica restricciones de acceso (IP, horario)
- Registra accesos a secciones protegidas
- Maneja cambios de contraseña obligatorios

### SecurityHeadersMiddleware
- Agrega headers de seguridad HTTP
- Configura Content Security Policy
- Protección XSS y clickjacking

### SessionTimeoutMiddleware
- Cierra sesiones inactivas automáticamente
- Configurable via SESSION_TIMEOUT

## API de Utilidades

### has_permission(user, permission_name)
Verifica si un usuario tiene un permiso específico.

### get_user_roles(user)
Obtiene los roles activos de un usuario.

### log_user_action(user, action, description, request)
Registra una acción en el log de auditoría.

### check_user_access_restrictions(user, request)
Verifica todas las restricciones de acceso del usuario.

## Seguridad

- **Contraseñas**: Validación de fortaleza, cambio obligatorio
- **Bloqueo de cuentas**: Automático después de intentos fallidos
- **Restricción por IP**: Lista blanca de IPs permitidas
- **Restricción horaria**: Acceso solo en horarios específicos
- **Auditoría completa**: Todo queda registrado
- **Headers de seguridad**: Protección contra ataques comunes

## Contribuir

Para agregar nuevas funcionalidades:

1. Crea los modelos necesarios en `models.py`
2. Agrega vistas en `views.py`
3. Crea formularios en `forms.py`
4. Agrega utilidades en `utils.py`
5. Documenta todo cambio importante