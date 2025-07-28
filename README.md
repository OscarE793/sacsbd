# SACSBD - Sistema de Análisis y Control de Seguridad de Base de Datos

## 🎯 Descripción

SACSBD es un sistema web desarrollado en Django para la gestión, monitoreo y análisis de backups de bases de datos SQL Server. Proporciona una interfaz intuitiva para ejecutar procedimientos almacenados, generar reportes y exportar datos en múltiples formatos.

## 🚀 Características Principales

- **Dashboard Interactivo**: Métricas en tiempo real de backups y estado del sistema
- **Reportes Dinámicos**: Ejecución de procedimientos almacenados con filtros avanzados
- **Exportación Múltiple**: Excel, PDF, CSV con formato profesional
- **Consultas Personalizadas**: Editor SQL con autocompletado y validación
- **Historial Completo**: Seguimiento de todas las ejecuciones de reportes
- **Interfaz Moderna**: Diseño responsive con componentes interactivos
- **Seguridad Integrada**: Autenticación, autorización y validación de consultas
- **Tablas Interactivas**: DataTables con filtros, búsqueda y ordenamiento

## 🏗️ Arquitectura del Sistema

```
SACSBD/
├── sacsbd_project/          # Configuración principal del proyecto
│   ├── settings/           # Configuraciones por entorno
│   ├── urls.py            # URLs principales
│   └── wsgi.py            # Configuración WSGI
├── apps/                  # Aplicaciones Django
│   ├── authentication/   # Sistema de autenticación
│   └── reportes/         # Módulo principal de reportes
├── templates/            # Plantillas HTML globales
├── static/              # Archivos estáticos (CSS, JS, imágenes)
├── media/               # Archivos subidos y exportaciones
└── requirements.txt     # Dependencias del proyecto
```

## 📋 Requisitos Previos

### Software Requerido
- **Python 3.9+**
- **SQL Server** (2016 o superior)
- **ODBC Driver 17 for SQL Server**
- **Git** (para clonar el repositorio)

### Base de Datos
El sistema utiliza dos tablas principales:

1. **BACKUPSGENERADOS**: Información detallada de backups
2. **JOBSBACKUPGENERADOS**: Resultados de jobs de backup

### Procedimientos Almacenados Disponibles
- `sp_countTotalBck` - Total de backups
- `sp_genBak` - Backups por fecha específica
- `sp_resultadoJobsBck` - Resultados de jobs entre fechas
- `sp_ultimosbck` - Últimos backups realizados
- `sp_estadosdb` - Estados de bases de datos
- `sp_porcentajeGenBak` - Porcentaje de backups generados
- Y muchos más...

## 🛠️ Instalación

### 1. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/sacsbd.git
cd sacsbd
```

### 2. Crear Entorno Virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
# Instalación mínima
pip install -r requirements-minimal.txt

# O instalación completa (recomendada para desarrollo)
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
Crear archivo `.env` en la raíz del proyecto:

```env
# Configuración de Django
SECRET_KEY=tu-clave-secreta-muy-segura
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Configuración de Base de Datos SQL Server
DB_ENGINE=mssql
DB_NAME=tu_base_datos
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña
DB_HOST=tu_servidor
DB_PORT=1433

# Configuración ODBC
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_TRUST_CERTIFICATE=yes

# Configuración de Email (opcional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_contraseña_app
```

### 5. Configurar Base de Datos

#### Actualizar Configuración en `settings/base.py`:
```python
DATABASES = {
    "default": {
        "ENGINE": "mssql",
        "NAME": os.getenv('DB_NAME', 'sacs_bd'),
        "USER": os.getenv('DB_USER', 'tu_usuario'),
        "PASSWORD": os.getenv('DB_PASSWORD', 'tu_contraseña'),
        "HOST": os.getenv('DB_HOST', 'tu_servidor'),
        "PORT": os.getenv('DB_PORT', ''),
        "OPTIONS": {
            "driver": os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server'),
            "extra_params": f"TrustServerCertificate={os.getenv('DB_TRUST_CERTIFICATE', 'yes')};",
        },
    }
}
```

### 6. Ejecutar Migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Crear Superusuario
```bash
python manage.py createsuperuser
```

### 8. Recopilar Archivos Estáticos
```bash
python manage.py collectstatic
```

### 9. Ejecutar Servidor de Desarrollo
```bash
python manage.py runserver
```

El sistema estará disponible en: `http://localhost:8000`

## 🔧 Configuración Adicional

### Configuración de Procedimientos Almacenados

En `apps/reportes/utils.py`, puedes agregar nuevos procedimientos al diccionario `PROCEDIMIENTOS_DISPONIBLES`:

```python
PROCEDIMIENTOS_DISPONIBLES = {
    'tu_nuevo_sp': {
        'nombre': 'Nombre Descriptivo',
        'descripcion': 'Descripción del procedimiento',
        'parametros': [
            {'nombre': 'fecha', 'tipo': 'date', 'formato': 'DD/MM/YYYY'}
        ],
        'categoria': 'tu_categoria'
    }
}
```

### Configuración de Conexión SQL Server

Para actualizar la cadena de conexión en `apps/reportes/utils.py`:

```python
def _get_connection_string(self) -> str:
    return (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={tu_servidor};"
        f"DATABASE={tu_base_datos};"
        f"UID={tu_usuario};"
        f"PWD={tu_contraseña};"
        "TrustServerCertificate=yes;"
    )
```

## 📖 Uso del Sistema

### 1. Acceso al Sistema
- Accede a `http://localhost:8000`
- Usa las credenciales de superusuario creadas

### 2. Dashboard Principal
- **Métricas**: Visualiza estadísticas principales
- **Gráficos**: Tendencias y distribución de backups
- **Accesos Rápidos**: Ejecuta reportes comunes
- **Historial**: Últimas ejecuciones

### 3. Generación de Reportes
- Selecciona un procedimiento almacenado
- Configura parámetros necesarios
- Aplica filtros adicionales
- Ejecuta y visualiza resultados
- Exporta en formato deseado

### 4. Consultas Personalizadas
- Editor SQL con autocompletado
- Validación de seguridad automática
- Ejecución de SELECT personalizados
- Exportación de resultados

### 5. Historial de Ejecuciones
- Visualiza todas las ejecuciones pasadas
- Re-ejecuta reportes exitosos
- Analiza errores y tiempos de ejecución
- Exporta historial completo

## 📊 Ejemplos de Uso

### Reporte de Backups por Fecha
```sql
-- Procedimiento: sp_genBak
-- Parámetro: 15/07/2024
-- Resultado: Lista de todos los backups del 15 de julio de 2024
```

### Análisis de Jobs Fallidos
```sql
-- Procedimiento: sp_resultadoJobsBck  
-- Parámetros: 2024-07-01 a 2024-07-31
-- Resultado: Jobs ejecutados en julio con su estado
```

### Consulta Personalizada
```sql
SELECT 
    SERVIDOR,
    COUNT(DISTINCT DatabaseName) as BasesDatos,
    COUNT(*) as TotalBackups,
    MAX(FECHA) as UltimoBackup
FROM BACKUPSGENERADOS 
GROUP BY SERVIDOR 
ORDER BY TotalBackups DESC;
```

## 🔒 Seguridad

### Validaciones Implementadas
- **Consultas SQL**: Solo SELECT permitido
- **Parámetros**: Validación de tipos y formatos
- **Autenticación**: Login obligatorio
- **Sesiones**: Timeout configurable
- **CSRF**: Protección automática

### Palabras Prohibidas
El sistema bloquea automáticamente:
- DROP, DELETE, UPDATE, INSERT
- ALTER, CREATE, TRUNCATE
- Operaciones destructivas

## 📁 Estructura de Archivos

### Aplicación de Reportes
```
apps/reportes/
├── models.py              # Modelos de datos
├── views.py               # Lógica de vistas
├── forms.py               # Formularios
├── utils.py               # Utilidades y conexión DB
├── urls.py                # Configuración de URLs
├── admin.py               # Administración Django
├── templatetags/          # Tags personalizados
│   └── reportes_tags.py
├── templates/reportes/    # Plantillas HTML
│   ├── base.html
│   ├── dashboard.html
│   ├── reportes.html
│   ├── consulta_personalizada.html
│   ├── historial.html
│   └── widgets/
└── migrations/            # Migraciones de BD
```

### Plantillas y Estáticas
```
templates/reportes/
├── base.html              # Plantilla base
├── dashboard.html         # Dashboard principal
├── reportes.html          # Generación de reportes
├── consulta_personalizada.html  # Editor SQL
├── historial.html         # Historial de ejecuciones
└── widgets/               # Componentes reutilizables

static/
├── assets/css/           # Hojas de estilo
├── assets/js/            # JavaScript
├── assets/images/        # Imágenes
└── assets/vendors/       # Librerías terceros
```

## 🚀 Despliegue en Producción

### 1. Configurar Entorno de Producción
```env
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com,tu-ip
SECRET_KEY=clave-super-secreta-production

# Base de datos de producción
DB_HOST=servidor-produccion
DB_NAME=sacsbd_production
```

### 2. Usar Gunicorn
```bash
pip install gunicorn
gunicorn sacsbd_project.wsgi:application --bind 0.0.0.0:8000
```

### 3. Configurar Nginx (Recomendado)
```nginx
server {
    listen 80;
    server_name tu-dominio.com;
    
    location /static/ {
        alias /path/to/sacsbd/staticfiles/;
    }
    
    location /media/ {
        alias /path/to/sacsbd/media/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. Configurar Supervisord
```ini
[program:sacsbd]
command=/path/to/venv/bin/gunicorn sacsbd_project.wsgi:application --bind 127.0.0.1:8000
directory=/path/to/sacsbd
user=sacsbd
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/sacsbd.log
```

## 🛠️ Desarrollo

### Comandos Útiles
```bash
# Ejecutar tests
python manage.py test

# Crear migración
python manage.py makemigrations reportes

# Aplicar migraciones
python manage.py migrate

# Shell de Django
python manage.py shell

# Crear comando personalizado
python manage.py startcommand nombre_comando
```

### Estructura de Tests
```python
# apps/reportes/tests.py
class ReportesViewsTest(TestCase):
    def test_dashboard_view(self):
        # Implementar tests
        pass
```

### Extensiones Recomendadas

#### Agregar Nuevo Procedimiento
1. Actualizar `PROCEDIMIENTOS_DISPONIBLES` en `utils.py`
2. Agregar validaciones en `forms.py` si es necesario
3. Actualizar plantillas si requiere campos especiales

#### Agregar Nueva Exportación
1. Crear función en `views.py` (ej: `generar_xml`)
2. Agregar opción en formularios
3. Actualizar botones en plantillas

## 🐛 Troubleshooting

### Error de Conexión a SQL Server
```bash
# Verificar driver ODBC
odbcinst -q -d

# Instalar driver en Ubuntu/Debian
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17
```

### Error de Dependencias Python
```bash
# Actualizar pip
python -m pip install --upgrade pip

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### Error de Permisos en Base de Datos
- Verificar que el usuario tenga permisos EXECUTE en los SPs
- Verificar conexión con SQL Server Management Studio
- Revisar firewall y puertos abiertos

### Problemas de Rendimiento
- Verificar índices en tablas principales
- Optimizar consultas pesadas
- Implementar cache para reportes frecuentes
- Configurar pool de conexiones

## 📞 Soporte

### Logs del Sistema
```bash
# Ver logs de Django
tail -f logs/sacsbd.log

# Ver logs de errores
tail -f logs/django_errors.log
```

### Información del Sistema
```python
# En Django shell
python manage.py shell

from apps.reportes.utils import DatabaseManager
db = DatabaseManager()
# Probar conexión
datos, error = db.ejecutar_consulta_personalizada("SELECT GETDATE()")
```

## 📝 Licencia

Este proyecto está desarrollado para uso interno de la organización. Todos los derechos reservados.

## 👥 Contribuciones

Para contribuir al proyecto:

1. Fork del repositorio
2. Crear rama para nueva feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📚 Documentación Adicional

- [Django Documentation](https://docs.djangoproject.com/)
- [SQL Server Documentation](https://docs.microsoft.com/en-us/sql/)
- [DataTables Documentation](https://datatables.net/)
- [Bootstrap Documentation](https://getbootstrap.com/)

---

**SACSBD v1.0.0** - Sistema de Análisis y Control de Seguridad de Base de Datos

Desarrollado con ❤️ usando Django y tecnologías modernas.
