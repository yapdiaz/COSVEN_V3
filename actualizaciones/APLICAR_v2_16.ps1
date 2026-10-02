$ErrorActionPreference = "Stop"

$root = "C:\Paykan\COSVEN"
$dest = Join-Path $root "app\dashboard_cosven.py"
$src  = Join-Path $PSScriptRoot "payload\app\dashboard_cosven.py"

if (-not (Test-Path $src)) {
    throw "No se encontró dashboard_cosven.py dentro del paquete."
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $root "versiones\antes_v2_16_$stamp\app"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

if (Test-Path $dest) {
    Copy-Item $dest (Join-Path $backupDir "dashboard_cosven.py") -Force
}

Copy-Item $src $dest -Force

Write-Host ""
Write-Host "v2.16 aplicada correctamente." -ForegroundColor Green
Write-Host "- Si ayer no tiene datos, abre el último día con movimientos disponible."
Write-Host "- El panel distingue datos procesados y último día con movimientos."
Write-Host "- No cambia cálculos, históricos ni actualizador."
Write-Host ""
Write-Host "Reinicie:"
Write-Host "C:\Paykan\COSVEN\iniciar_dashboard.bat"
