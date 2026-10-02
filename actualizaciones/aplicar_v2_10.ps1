$ErrorActionPreference = "Stop"

$root = "C:\Paykan\COSVEN"
$dest = Join-Path $root "app\dashboard_cosven.py"
$src  = Join-Path $PSScriptRoot "payload\app\dashboard_cosven.py"

if (-not (Test-Path $src)) {
    throw "No se encontró el dashboard nuevo dentro del paquete."
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $root "versiones\antes_v2_10_$stamp\app"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

if (Test-Path $dest) {
    Copy-Item $dest (Join-Path $backupDir "dashboard_cosven.py") -Force
    Write-Host "Backup creado en:" -ForegroundColor Cyan
    Write-Host $backupDir
}

Copy-Item $src $dest -Force

Write-Host ""
Write-Host "Dashboard v2.10 aplicado correctamente." -ForegroundColor Green
Write-Host "Cambios:"
Write-Host "- Recuadros de Farmacias, Tipo de pedido y Laboratorios más altos."
Write-Host "- Ayuda final actualizada y simplificada."
Write-Host "- Se mantiene la imagen de ayuda."
Write-Host ""
Write-Host "No se modificó la lógica COSVEN, históricos, caches ni DBF."
Write-Host ""
Write-Host "Reinicie el dashboard con:"
Write-Host "C:\Paykan\COSVEN\iniciar_dashboard.bat"
