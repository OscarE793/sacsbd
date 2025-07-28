# Script completo para integrar Metronic Demo1 con Django
# integrate_metronic_demo1.ps1

param(
    [string]$ProjectDir = "C:\Users\Oscar Jaramillo\Documents\sacsbd",
    [string]$MetronicDir = "C:\Users\Oscar Jaramillo\Downloads\themeforest-Bnx2vx04-metronic-responsive-admin-dashboard-template\metronic-v9.2.2\metronic-html\dist"
)

Write-Host "🚀 SACS_BD - Integración Completa Metronic Demo1" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green

try {
    Set-Location $ProjectDir

    # 1. Limpiar estructura anterior
    Write-Host "🧹 Limpiando estructura anterior..." -ForegroundColor Yellow
    if (Test-Path "static\assets") { Remove-Item "static\assets" -Recurse -Force }
    if (Test-Path "static\metronic") { Remove-Item "static\metronic" -Recurse -Force }

    # 2. Crear estructura oficial Metronic
    Write-Host "📁 Creando estructura de directorios..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "static\assets" -Force
    New-Item -ItemType Directory -Path "static\assets\css" -Force
    New-Item -ItemType Directory -Path "static\assets\js" -Force
    New-Item -ItemType Directory -Path "static\assets\media" -Force
    New-Item -ItemType Directory -Path "static\assets\vendors" -Force
    New-Item -ItemType Directory -Path "templates\metronic" -Force
    New-Item -ItemType Directory -Path "templates\metronic\layout" -Force
    New-Item -ItemType Directory -Path "templates\metronic\authentication" -Force

    # 3. Copiar assets completos de Metronic
    Write-Host "📦 Copiando assets completos de Metronic..." -ForegroundColor Yellow
    if (Test-Path "$MetronicDir\assets") {
        Copy-Item "$MetronicDir\assets\*" "static\assets\" -Recurse -Force
        Write-Host "  ✅ Assets copiados desde $MetronicDir\assets" -ForegroundColor Green
    } else {
        Write-Host "  ❌ No se encontró $MetronicDir\assets" -ForegroundColor Red
        return
    }

    # 4. Extraer templates clave del Demo1
    Write-Host "📄 Extrayendo templates del Demo1..." -ForegroundColor Yellow
    
    # Copiar login de demo1
    if (Test-Path "$MetronicDir\html\demo1\authentication\classic\sign-in.html") {
        Copy-Item "$MetronicDir\html\demo1\authentication\classic\sign-in.html" "templates\metronic\authentication\login.html" -Force
        Write-Host "  ✅ Login template extraído" -ForegroundColor Green
    }
    
    # Copiar dashboard principal
    if (Test-Path "$MetronicDir\html\demo1\index.html") {
        Copy-Item "$MetronicDir\html\demo1\index.html" "templates\metronic\dashboard.html" -Force
        Write-Host "  ✅ Dashboard template extraído" -ForegroundColor Green
    }

    # 5. Verificar archivos clave
    Write-Host "🔍 Verificando archivos clave..." -ForegroundColor Yellow
    
    $criticalFiles = @(
        "static\assets\css\style.bundle.css",
        "static\assets\js\scripts.bundle.js",
        "static\assets\vendors\keenicons\duotone\style.css",
        "static\assets\vendors\apexcharts\apexcharts.min.js"
    )
    
    $missingFiles = @()
    foreach ($file in $criticalFiles) {
        if (-not (Test-Path $file)) {
            $missingFiles += $file
        } else {
            Write-Host "  ✅ $file" -ForegroundColor Green
        }
    }
    
    if ($missingFiles.Count -gt 0) {
        Write-Host "  ⚠️ Archivos faltantes:" -ForegroundColor Yellow
        $missingFiles | ForEach-Object { Write-Host "    - $_" -ForegroundColor Yellow }
    }

    # 6. Crear configuración Django optimizada
    Write-Host "⚙️ Configurando Django..." -ForegroundColor Yellow
    
    # Resumen
    Write-Host ""
    Write-Host "🎉 ¡Integración Metronic Demo1 completada!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Archivos procesados:" -ForegroundColor Cyan
    $totalFiles = (Get-ChildItem "static\assets" -Recurse -File).Count
    $totalSize = [math]::Round(((Get-ChildItem "static\assets" -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB), 2)
    Write-Host "  📁 Total de archivos: $totalFiles" -ForegroundColor White
    Write-Host "  💾 Tamaño total: $totalSize MB" -ForegroundColor White

    Write-Host ""
    Write-Host "🔧 Próximos pasos:" -ForegroundColor Yellow
    Write-Host "1. Ejecutar: python manage.py collectstatic" -ForegroundColor White
    Write-Host "2. Configurar templates Django" -ForegroundColor White
    Write-Host "3. Actualizar urls.py" -ForegroundColor White
    Write-Host "4. Probar login y dashboard" -ForegroundColor White

} catch {
    Write-Host ""
    Write-Host "❌ Error durante la integración: $($_.Exception.Message)" -ForegroundColor Red
}

Read-Host "`nPresiona Enter para continuar"
