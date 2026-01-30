@echo off
chcp 65001 >nul
echo ====================================
echo MIGRACIÓN DEL SISTEMA DE TURNOS
echo ====================================
echo.

cd /d "C:\Users\Oscar Jaramillo\Documents\sacsbd"

echo [INFO] Directorio actual: %CD%
echo.

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] No se encontró el entorno virtual
    pause
    exit /b 1
)

echo [1/6] Generando migración...
echo Comando: python manage.py makemigrations horas_extras
echo.

venv\Scripts\python.exe manage.py makemigrations horas_extras

if errorlevel 1 (
    echo.
    echo [ERROR] Falló la generación de la migración
    pause
    exit /b 1
)

echo.
echo [INFO] Migración generada exitosamente
echo.

echo [2/6] Mostrando plan de migración...
venv\Scripts\python.exe manage.py showmigrations horas_extras

echo.
echo ====================================
echo REVISIÓN ANTES DE APLICAR
echo ====================================
echo.
echo La migración debe realizar:
echo.
echo   [ELIMINAR]
echo     - Tabla horas_extras_empleado
echo     - Tabla horas_extras_calculorecargo
echo.
echo   [MODIFICAR]
echo     - horas_extras_registroturno:
echo       * Eliminar columna 'empleado_id'
echo       * Agregar columna 'operador_id' (FK a auth_user)
echo.
echo   [CREAR]
echo     - Tabla horas_extras_resumenmensual
echo.
echo ====================================
echo.

set /p confirmar="¿Deseas aplicar la migración? (escribe SI en mayúsculas): "

if not "%confirmar%"=="SI" (
    echo.
    echo [CANCELADO] Migración cancelada por el usuario
    echo.
    pause
    exit /b 0
)

echo.
echo [4/6] Aplicando migración...
echo Comando: python manage.py migrate horas_extras
echo.

venv\Scripts\python.exe manage.py migrate horas_extras

if errorlevel 1 (
    echo.
    echo [ERROR] Falló la aplicación de la migración
    echo.
    echo IMPORTANTE: Revisa los errores arriba.
    pause
    exit /b 1
)

echo.
echo [5/6] Verificando estructura de base de datos...
echo.

venv\Scripts\python.exe manage.py shell -c "from apps.horas_extras.models import TipoTurno, DiaFestivo, RegistroTurno, ResumenMensual; from django.contrib.auth.models import User; print('=' * 50); print('VERIFICACIÓN DE MODELOS'); print('=' * 50); print(f'TipoTurno: {TipoTurno.objects.count()} registros'); print(f'DiaFestivo: {DiaFestivo.objects.count()} registros'); print(f'RegistroTurno: {RegistroTurno.objects.count()} registros'); print(f'ResumenMensual: {ResumenMensual.objects.count()} registros'); print(''); turno = RegistroTurno.objects.first(); print(f'Campo operador existe: {hasattr(turno, \"operador\") if turno else \"N/A\"}'); print('=' * 50)"

echo.
echo [6/6] Verificando rol de operador...
echo.

venv\Scripts\python.exe manage.py shell -c "from apps.user_management.models import Role, UserRole; from django.contrib.auth.models import User; print('Verificando rol de operador...'); rol = Role.objects.filter(name='operador de centro de computo').first(); print(f'Rol existe: {\"SI\" if rol else \"NO\"}'); print(f'Usuarios con rol: {UserRole.objects.filter(role=rol, activo=True).count() if rol else 0}')"

echo.
echo ====================================
echo ✓ MIGRACIÓN COMPLETADA
echo ====================================
echo.
echo PRÓXIMOS PASOS:
echo.
echo 1. Verificar rol 'operador de centro de computo':
echo    Ir a: http://localhost:8000/usuarios/roles/
echo.
echo 2. Asignar el rol a los usuarios operadores
echo.
echo 3. Probar el sistema:
echo    python manage.py runserver
echo.
echo 4. Verificar dashboard sin errores:
echo    http://localhost:8000/horas-extras/
echo.
pause
