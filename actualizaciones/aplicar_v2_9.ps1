$ErrorActionPreference = "Stop"
$root = "C:\Paykan\COSVEN"
$dest = Join-Path $root "app\dashboard_cosven.py"
$src  = Join-Path $PSScriptRoot "payload\app\dashboard_cosven.py"

if (-not (Test-Path $src)) { throw "No se encontró el dashboard nuevo dentro del paquete." }

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $root "versiones\antes_v2_9_$stamp\app"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
if (Test-Path $dest) {
    Copy-Item $dest (Join-Path $backupDir "dashboard_cosven.py") -Force
    Write-Host "Backup creado en: $backupDir" -ForegroundColor Cyan
}
Copy-Item $src $dest -Force
Write-Host ""
Write-Host "Dashboard v2.9 aplicado correctamente." -ForegroundColor Green
Write-Host "Cambios: filtro Laboratorio separado de Tipo de producto y popup de detalle compactado para mostrar la grilla completa."
Write-Host "No se modificó cosven.db, históricos, caches ni DBF de Paykan."
Write-Host ""
Write-Host "Reinicie con C:\Paykan\COSVEN\iniciar_dashboard.bat"
