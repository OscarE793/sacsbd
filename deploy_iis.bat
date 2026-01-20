@echo off
REM =============================================================================
REM SACSBD - Script de Despliegue para IIS
REM =============================================================================
REM INSTRUCCIONES:
REM 1. Ejecutar como Administrador
REM 2. Modificar las rutas según tu servidor
REM =============================================================================

echo.
echo =============================================================================
echo SACSBD - Despliegue en IIS
echo =============================================================================
echo.

REM Configurar rutas (MODIFICAR SEGÚN TU SERVIDOR)
SET PYTHON_PATH=C:\Python313
SET PROJECT_PATH=C:\inetpub\wwwroot\sacsbd
SET VENV_PATH=%PROJECT_PATH%\venv

echo [1/8] Verificando Python...
%PYTHON_PATH%\python.exe --version
if errorlevel 1 (
    echo ERROR: Python no encontrado en %PYTHON_PATH%
    pause
    exit /b 1
)

echo.
echo [2/8] Creando entorno virtual...
if not exist "%VENV_PATH%" (
    %PYTHON_PATH%\python.exe -m venv %VENV_PATH%
    echo Entorno virtual creado.
) else (
    echo Entorno virtual ya existe.
)

echo.
echo [3/8] Activando entorno virtual...
call %VENV_PATH%\Scripts\activate.bat

echo.
echo [4/8] Instalando dependencias...
pip install --upgrade pip
pip install -r %PROJECT_PATH%\requirements.txt
pip install wfastcgi

echo.
echo [5/8] Configurando wfastcgi...
wfastcgi-enable

echo.
echo [6/8] Recolectando archivos estaticos...
cd %PROJECT_PATH%
python manage.py collectstatic --noinput --settings=sacsbd_project.settings.production

echo.
echo [7/8] Aplicando migraciones...
python manage.py migrate --settings=sacsbd_project.settings.production

echo.
echo [8/8] Verificando configuracion...
python manage.py check --settings=sacsbd_project.settings.production

echo.
echo =============================================================================
echo DESPLIEGUE COMPLETADO
echo =============================================================================
echo.
echo PASOS SIGUIENTES:
echo 1. Abrir IIS Manager
echo 2. Crear un nuevo sitio web apuntando a: %PROJECT_PATH%
echo 3. Configurar el Application Pool para usar "No Managed Code"
echo 4. Asegurar permisos de lectura/escritura en las carpetas:
echo    - %PROJECT_PATH%\logs
echo    - %PROJECT_PATH%\media
echo    - %PROJECT_PATH%\staticfiles
echo 5. Reiniciar IIS: iisreset
echo.
pause
