# 🚀 Guía de Despliegue SACSBD en IIS

## Índice
1. [Prerrequisitos](#prerrequisitos)
2. [Instalación de Python](#instalación-de-python)
3. [Configuración de IIS](#configuración-de-iis)
4. [Despliegue del Proyecto](#despliegue-del-proyecto)
5. [Configuración del Sitio Web](#configuración-del-sitio-web)
6. [Verificación](#verificación)
7. [Solución de Problemas](#solución-de-problemas)

---

## Prerrequisitos

### En el servidor Windows:
- [x] Windows Server 2016/2019/2022
- [x] IIS instalado con CGI habilitado
- [x] SQL Server instalado y configurado
- [x] ODBC Driver 17 for SQL Server
- [x] Acceso de administrador

### Software necesario:
- Python 3.10+ (recomendado 3.13)
- Git (opcional, para clonar repositorio)

---

## 1. Instalación de Python

### Paso 1.1: Descargar Python
1. Ir a https://www.python.org/downloads/
2. Descargar Python 3.13.x (Windows installer 64-bit)

### Paso 1.2: Instalar Python
1. Ejecutar el instalador como **Administrador**
2. **IMPORTANTE**: Marcar ☑️ "Add Python to PATH"
3. Seleccionar "Customize installation"
4. Marcar todas las opciones opcionales
5. En "Advanced Options":
   - ☑️ Install for all users
   - ☑️ Add Python to environment variables
   - Ruta de instalación: `C:\Python313`
6. Hacer clic en "Install"

### Paso 1.3: Verificar instalación
```cmd
python --version
pip --version
```

---

## 2. Configuración de IIS

### Paso 2.1: Instalar características de IIS
Abrir PowerShell como Administrador:
```powershell
# Instalar IIS con CGI
Install-WindowsFeature -Name Web-Server -IncludeManagementTools
Install-WindowsFeature -Name Web-CGI

# Verificar instalación
Get-WindowsFeature -Name Web-*
```

### Paso 2.2: Instalar wfastcgi
```cmd
pip install wfastcgi
wfastcgi-enable
```

**Nota**: Guarda el resultado del comando `wfastcgi-enable`, lo necesitarás después.
Ejemplo de salida:
```
"C:\Python313\python.exe|C:\Python313\Lib\site-packages\wfastcgi.py"
```

### Paso 2.3: Registrar Python en IIS
1. Abrir **IIS Manager**
2. Seleccionar el servidor (raíz)
3. Doble clic en **Handler Mappings**
4. Clic derecho → **Add Module Mapping**
5. Configurar:
   - Request path: `*`
   - Module: `FastCgiModule`
   - Executable: `C:\Python313\python.exe|C:\Python313\Lib\site-packages\wfastcgi.py`
   - Name: `Python FastCGI`

---

## 3. Despliegue del Proyecto

### Paso 3.1: Copiar archivos del proyecto
1. Crear carpeta: `C:\inetpub\wwwroot\sacsbd`
2. Copiar todos los archivos del proyecto a esta carpeta

### Paso 3.2: Crear entorno virtual
```cmd
cd C:\inetpub\wwwroot\sacsbd
python -m venv venv
venv\Scripts\activate
```

### Paso 3.3: Instalar dependencias
```cmd
pip install --upgrade pip
pip install -r requirements.txt
pip install wfastcgi
```

### Paso 3.4: Configurar variables de entorno
1. Editar el archivo `.env.production`:
```ini
SECRET_KEY=tu-clave-secreta-muy-larga-y-segura-de-50-caracteres
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,nombre-servidor,192.168.x.x
DB_NAME=sacs_bd
DB_USER=sa
DB_PASSWORD=tu_password_sql_server
DB_HOST=localhost\SACSBD24
```

### Paso 3.5: Recolectar archivos estáticos
```cmd
python manage.py collectstatic --noinput --settings=sacsbd_project.settings.production
```

### Paso 3.6: Aplicar migraciones
```cmd
python manage.py migrate --settings=sacsbd_project.settings.production
```

### Paso 3.7: Crear superusuario (si es necesario)
```cmd
python manage.py createsuperuser --settings=sacsbd_project.settings.production
```

---

## 4. Configuración del Sitio Web en IIS

### Paso 4.1: Crear Application Pool
1. Abrir **IIS Manager**
2. Clic derecho en **Application Pools** → **Add Application Pool**
3. Configurar:
   - Name: `SACSBD_Pool`
   - .NET CLR version: `No Managed Code`
   - Managed pipeline mode: `Integrated`
4. Clic en **OK**

### Paso 4.2: Configurar Application Pool
1. Seleccionar `SACSBD_Pool`
2. Clic en **Advanced Settings**
3. Configurar:
   - Identity: `LocalSystem` o una cuenta con permisos
   - Start Mode: `AlwaysRunning`
   - Idle Time-out: `0` (deshabilitado)

### Paso 4.3: Crear Sitio Web
1. Clic derecho en **Sites** → **Add Website**
2. Configurar:
   - Site name: `SACSBD`
   - Application pool: `SACSBD_Pool`
   - Physical path: `C:\inetpub\wwwroot\sacsbd`
   - Binding:
     - Type: `http`
     - IP address: `All Unassigned`
     - Port: `80` (o el puerto que desees)
     - Host name: (dejar vacío o tu dominio)

### Paso 4.4: Configurar permisos de carpeta
```cmd
icacls "C:\inetpub\wwwroot\sacsbd" /grant "IIS_IUSRS:(OI)(CI)RX" /T
icacls "C:\inetpub\wwwroot\sacsbd\logs" /grant "IIS_IUSRS:(OI)(CI)F" /T
icacls "C:\inetpub\wwwroot\sacsbd\media" /grant "IIS_IUSRS:(OI)(CI)F" /T
icacls "C:\inetpub\wwwroot\sacsbd\staticfiles" /grant "IIS_IUSRS:(OI)(CI)RX" /T
```

### Paso 4.5: Actualizar web.config
Asegúrate de que el archivo `web.config` tenga las rutas correctas:
```xml
<add key="PYTHONPATH" value="C:\inetpub\wwwroot\sacsbd" />
<add key="WSGI_HANDLER" value="sacsbd_project.wsgi_production.application" />
```

---

## 5. Verificación

### Paso 5.1: Reiniciar IIS
```cmd
iisreset
```

### Paso 5.2: Verificar en navegador
1. Abrir navegador
2. Ir a `http://localhost/` o `http://nombre-servidor/`
3. Debería aparecer la página de login de SACSBD

### Paso 5.3: Verificar logs
```cmd
type C:\inetpub\wwwroot\sacsbd\logs\sacsbd_production.log
```

---

## 6. Solución de Problemas

### Error 500 - Internal Server Error
1. Verificar logs en `C:\inetpub\wwwroot\sacsbd\logs\`
2. Verificar que el Application Pool esté en "Started"
3. Verificar permisos de carpetas

### Error 502.5 - ANCM Out-Of-Process Startup Failure
1. Verificar que wfastcgi esté habilitado: `wfastcgi-enable`
2. Verificar la ruta de Python en web.config

### Error de Base de Datos
1. Verificar conexión a SQL Server
2. Verificar credenciales en `.env.production`
3. Verificar que el driver ODBC esté instalado

### Archivos estáticos no cargan (CSS/JS)
1. Ejecutar: `python manage.py collectstatic --noinput`
2. Verificar permisos en `staticfiles`
3. Verificar configuración de URL Rewrite en web.config

### Comando útil para debug
```cmd
cd C:\inetpub\wwwroot\sacsbd
venv\Scripts\activate
python manage.py check --settings=sacsbd_project.settings.production
```

---

## 7. Estructura de Archivos Final

```
C:\inetpub\wwwroot\sacsbd\
├── apps\
├── logs\
│   ├── sacsbd_production.log
│   └── sacsbd_errors.log
├── media\
├── sacsbd_project\
│   ├── settings\
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py     ← Configuración producción
│   ├── wsgi.py
│   └── wsgi_production.py    ← WSGI para IIS
├── static\
├── staticfiles\              ← Archivos estáticos compilados
├── templates\
├── venv\                     ← Entorno virtual
├── .env.production           ← Variables de entorno
├── manage.py
├── requirements.txt
└── web.config               ← Configuración IIS
```

---

## Contacto y Soporte

Si encuentras problemas durante el despliegue:
1. Revisar los logs en `C:\inetpub\wwwroot\sacsbd\logs\`
2. Verificar el Event Viewer de Windows
3. Consultar la documentación de Django: https://docs.djangoproject.com/

---
**Última actualización**: Diciembre 2025
**Versión SACSBD**: 1.0.0
