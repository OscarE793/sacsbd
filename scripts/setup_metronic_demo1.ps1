# Script para configurar Metronic demo1 siguiendo documentación oficial
# setup_metronic_demo1.ps1

Write-Host "🚀 SACS_BD - Configuración Metronic Demo1 (Oficial)" -ForegroundColor Green
Write-Host "Siguiendo: https://keenthemes.com/metronic/tailwind/docs/getting-started/integration/django" -ForegroundColor Cyan

$ProjectDir = "C:\Users\Oscar Jaramillo\Documents\sacsbd"
$MetronicSource = "C:\Users\Oscar Jaramillo\Downloads\themeforest-Bnx2vx04-metronic-responsive-admin-dashboard-template\metronic-v9.2.2"

Set-Location $ProjectDir

try {
    # 1. Crear estructura según documentación oficial
    Write-Host "📁 Creando estructura oficial..." -ForegroundColor Yellow
    
    $Dirs = @(
        "static\demo1\assets\css",
        "static\demo1\assets\js",
        "static\demo1\assets\media",
        "static\demo1\assets\vendors",
        "static\demo1\plugins",
        "templates\layouts",
        "templates\pages",
        "templates\partials"
    )
    
    foreach ($dir in $Dirs) {
        $fullPath = Join-Path $ProjectDir $dir
        if (-not (Test-Path $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
            Write-Host "  ✅ $dir" -ForegroundColor Green
        }
    }
    
    # 2. Copiar assets de demo1 específicamente
    Write-Host "📦 Copiando assets de demo1..." -ForegroundColor Yellow
    
    if (Test-Path "$MetronicSource\html\demo1\assets") {
        # Demo1 específico
        Copy-Item "$MetronicSource\html\demo1\assets\*" "$ProjectDir\static\demo1\assets\" -Recurse -Force
        Write-Host "  ✅ Assets demo1 copiados" -ForegroundColor Green
    } elseif (Test-Path "$MetronicSource\dist\assets") {
        # Fallback a dist
        Copy-Item "$MetronicSource\dist\assets\*" "$ProjectDir\static\demo1\assets\" -Recurse -Force
        Write-Host "  ✅ Assets dist copiados" -ForegroundColor Green
    } else {
        Write-Host "  ❌ No se encontraron assets de Metronic" -ForegroundColor Red
        Write-Host "  📍 Verifica la ruta: $MetronicSource" -ForegroundColor Yellow
    }
    
    # 3. Copiar plugins
    if (Test-Path "$MetronicSource\html\demo1\plugins") {
        Copy-Item "$MetronicSource\html\demo1\plugins\*" "$ProjectDir\static\demo1\plugins\" -Recurse -Force
        Write-Host "  ✅ Plugins copiados" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "🎉 Configuración completada!" -ForegroundColor Green
    Write-Host "📋 Próximo paso: Actualizar settings.py y templates" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

Read-Host "Presiona Enter para continuar"
