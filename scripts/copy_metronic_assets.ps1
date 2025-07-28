# Script para copiar assets de Metronic a estructura Django
# Ejecutar desde PowerShell como administrador

param(
    [string]$SourcePath = "C:\Users\Oscar Jaramillo\Downloads\themeforest-Bnx2vx04-metronic-responsive-admin-dashboard-template\metronic-v9.2.2\metronic-html\dist\assets",
    [string]$DestPath = "C:\Users\Oscar Jaramillo\Documents\sacsbd\static\assets"
)

Write-Host "🚀 Copiando assets de Metronic v9.2.2 a Django..." -ForegroundColor Green
Write-Host "📂 Origen: $SourcePath" -ForegroundColor Cyan
Write-Host "📂 Destino: $DestPath" -ForegroundColor Cyan
Write-Host ""

# Verificar directorios
if (-not (Test-Path $SourcePath)) {
    Write-Host "❌ Directorio fuente no encontrado: $SourcePath" -ForegroundColor Red
    Write-Host "🔍 Verifica que Metronic esté descomprimido en la ubicación correcta" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

if (-not (Test-Path $DestPath)) {
    Write-Host "📁 Creando directorio destino: $DestPath" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $DestPath -Force -ErrorAction Stop
}

try {
    Write-Host "📋 Iniciando copia de archivos..." -ForegroundColor Yellow
    
    # CSS Principal
    Write-Host "  📄 Copiando CSS principal..." -ForegroundColor Cyan
    if (Test-Path "$SourcePath\css\styles.css") {
        Copy-Item "$SourcePath\css\styles.css" "$DestPath\css\" -Force
        Write-Host "    ✅ styles.css copiado" -ForegroundColor Green
    } else {
        Write-Host "    ❌ styles.css no encontrado" -ForegroundColor Red
    }
    
    # JavaScript Principal
    Write-Host "  📄 Copiando JavaScript principal..." -ForegroundColor Cyan
    if (Test-Path "$SourcePath\js\core.bundle.js") {
        Copy-Item "$SourcePath\js\core.bundle.js" "$DestPath\js\" -Force
        Write-Host "    ✅ core.bundle.js copiado" -ForegroundColor Green
    } else {
        Write-Host "    ❌ core.bundle.js no encontrado" -ForegroundColor Red
    }
    
    # JavaScript de Widgets (importante para dashboard)
    Write-Host "  📄 Copiando widgets JavaScript..." -ForegroundColor Cyan
    if (Test-Path "$SourcePath\js\widgets") {
        New-Item -ItemType Directory -Path "$DestPath\js\widgets" -Force -ErrorAction SilentlyContinue
        Copy-Item "$SourcePath\js\widgets\*" "$DestPath\js\widgets\" -Recurse -Force
        $widgetFiles = (Get-ChildItem "$DestPath\js\widgets" -Recurse -File).Count
        Write-Host "    ✅ $widgetFiles archivos de widgets copiados" -ForegroundColor Green
    }
    
    # JavaScript de Layouts
    Write-Host "  📄 Copiando layouts JavaScript..." -ForegroundColor Cyan
    if (Test-Path "$SourcePath\js\layouts") {
        New-Item -ItemType Directory -Path "$DestPath\js\layouts" -Force -ErrorAction SilentlyContinue
        Copy-Item "$SourcePath\js\layouts\*" "$DestPath\js\layouts\" -Recurse -Force
        $layoutFiles = (Get-ChildItem "$DestPath\js\layouts" -Recurse -File).Count
        Write-Host "    ✅ $layoutFiles archivos de layouts copiados" -ForegroundColor Green
    }
    
    # Vendors críticos para SACS_BD
    Write-Host "  📦 Copiando vendors críticos..." -ForegroundColor Cyan
    $CriticalVendors = @('keenicons', 'ktui', 'apexcharts', '@form-validation', 'clipboard')
    
    foreach ($vendor in $CriticalVendors) {
        if (Test-Path "$SourcePath\vendors\$vendor") {
            Write-Host "    📦 Copiando $vendor..." -ForegroundColor Yellow
            New-Item -ItemType Directory -Path "$DestPath\vendors\$vendor" -Force -ErrorAction SilentlyContinue
            Copy-Item "$SourcePath\vendors\$vendor\*" "$DestPath\vendors\$vendor\" -Recurse -Force
            Write-Host "    ✅ $vendor copiado" -ForegroundColor Green
        } else {
            Write-Host "    ⚠️ $vendor no encontrado" -ForegroundColor Yellow
        }
    }
    
    # Media files (logos, iconos, imágenes)
    Write-Host "  🖼️ Copiando archivos media..." -ForegroundColor Cyan
    if (Test-Path "$SourcePath\media") {
        Copy-Item "$SourcePath\media\*" "$DestPath\media\" -Recurse -Force
        $mediaFiles = (Get-ChildItem "$DestPath\media" -Recurse -File).Count
        Write-Host "    ✅ $mediaFiles archivos media copiados" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "🎉 ¡Assets de Metronic copiados exitosamente!" -ForegroundColor Green
    
    # Mostrar resumen
    Write-Host ""
    Write-Host "📊 Resumen de archivos copiados:" -ForegroundColor Cyan
    $TotalFiles = (Get-ChildItem $DestPath -Recurse -File).Count
    $TotalSize = [math]::Round(((Get-ChildItem $DestPath -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB), 2)
    
    Write-Host "  📁 Total de archivos: $TotalFiles" -ForegroundColor White
    Write-Host "  💾 Tamaño total: $TotalSize MB" -ForegroundColor White
    
    Write-Host ""
    Write-Host "🔧 Próximos pasos:" -ForegroundColor Yellow
    Write-Host "1. Ejecutar: python manage.py collectstatic" -ForegroundColor White
    Write-Host "2. Actualizar templates con rutas {% static 'assets/...' %}" -ForegroundColor White
    Write-Host "3. Crear template de prueba para verificar integración" -ForegroundColor White
    Write-Host "4. Personalizar CSS en static/custom/css/sacs-theme.css" -ForegroundColor White
    
    Write-Host ""
    Write-Host "✅ Migración completada. ¡Listo para desarrollar con Metronic!" -ForegroundColor Green

} catch {
    Write-Host ""
    Write-Host "❌ Error durante la copia: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "🔍 Verifica permisos y rutas" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host ""
Read-Host "Presiona Enter para continuar"
