# Script para crear estructura completa de assets
# Ejecutar desde PowerShell en el directorio del proyecto

Write-Host "📁 Creando estructura de directorios para SACS_BD + Metronic..." -ForegroundColor Green

$BaseDir = "C:\Users\Oscar Jaramillo\Documents\sacsbd\static"

# Directorios de Assets (Metronic)
$AssetsDirs = @(
    "assets",
    "assets\css",
    "assets\js", 
    "assets\js\widgets",
    "assets\js\layouts",
    "assets\media",
    "assets\media\icons",
    "assets\media\images", 
    "assets\media\logos",
    "assets\vendors",
    "assets\vendors\keenicons",
    "assets\vendors\ktui",
    "assets\vendors\apexcharts",
    "assets\vendors\@form-validation"
)

# Directorios personalizados SACS_BD
$CustomDirs = @(
    "custom",
    "custom\css",
    "custom\js",
    "custom\img",
    "custom\fonts"
)

# Crear directorios de assets
foreach ($dir in $AssetsDirs) {
    $fullPath = Join-Path $BaseDir $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force
        Write-Host "  ✅ $dir" -ForegroundColor Green
    } else {
        Write-Host "  ⚪ $dir (ya existe)" -ForegroundColor Yellow
    }
}

# Crear directorios personalizados
foreach ($dir in $CustomDirs) {
    $fullPath = Join-Path $BaseDir $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force
        Write-Host "  ✅ $dir" -ForegroundColor Green
    } else {
        Write-Host "  ⚪ $dir (ya existe)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🎉 Estructura de directorios creada exitosamente!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Próximos pasos:" -ForegroundColor Cyan
Write-Host "1. Copiar assets de Metronic a static/assets/" -ForegroundColor White
Write-Host "2. Crear archivos CSS/JS personalizados en static/custom/" -ForegroundColor White
Write-Host "3. Actualizar templates con las nuevas rutas" -ForegroundColor White
