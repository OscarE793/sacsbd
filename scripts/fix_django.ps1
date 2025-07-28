# Script para limpiar y configurar Django correctamente
# fix_django.ps1

Write-Host "🔧 SACS_BD - Limpieza y Configuración Django" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

$ProjectDir = "C:\Users\Oscar Jaramillo\Documents\sacsbd"
Set-Location $ProjectDir

try {
    # 1. Activar entorno virtual
    Write-Host "🐍 Activando entorno virtual..." -ForegroundColor Yellow
    & "$ProjectDir\sacsvenv\Scripts\Activate.ps1"
    
    # 2. Desinstalar backends SQL Server conflictivos
    Write-Host "🗑️ Desinstalando backends SQL Server conflictivos..." -ForegroundColor Yellow
    pip uninstall mssql-django django-mssql-backend pyodbc -y 2>$null
    
    # 3. Limpiar cache Python y Django
    Write-Host "🧹 Limpiando cache y archivos temporales..." -ForegroundColor Yellow
    python clean_django.py
    
    # 4. Reinstalar dependencias limpias
    Write-Host "📦 Instalando dependencias limpias..." -ForegroundColor Yellow
    pip install -r requirements.txt
    
    # 5. Verificar configuración Django
    Write-Host "🔍 Verificando configuración Django..." -ForegroundColor Yellow
    python manage.py check --settings=sacsbd_project.settings.development
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Django check pasado!" -ForegroundColor Green
        
        # 6. Crear migraciones
        Write-Host "📋 Creando migraciones..." -ForegroundColor Yellow
        python manage.py makemigrations --settings=sacsbd_project.settings.development
        
        # 7. Aplicar migraciones
        Write-Host "📋 Aplicando migraciones..." -ForegroundColor Yellow
        python manage.py migrate --settings=sacsbd_project.settings.development
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Migraciones aplicadas correctamente!" -ForegroundColor Green
            
            # 8. Collectstatic
            Write-Host "📁 Recopilando archivos estáticos..." -ForegroundColor Yellow
            python manage.py collectstatic --noinput --settings=sacsbd_project.settings.development
            
            Write-Host ""
            Write-Host "🎉 ¡Django configurado correctamente!" -ForegroundColor Green
            Write-Host "🚀 Ahora puedes ejecutar: python manage.py runserver" -ForegroundColor Cyan
            Write-Host "🔗 URL de prueba: http://127.0.0.1:8000/test/" -ForegroundColor Cyan
            
        } else {
            Write-Host "❌ Error en migraciones" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ Django check falló" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Read-Host "Presiona Enter para continuar"
