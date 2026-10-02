$ErrorActionPreference = "Stop"

$root = "C:\Paykan\COSVEN"
$dest = Join-Path $root "app\dashboard_cosven.py"
$src  = Join-Path $PSScriptRoot "payload\app\dashboard_cosven.py"

if (-not (Test-Path $src)) {
    throw "No se encontró payload\app\dashboard_cosven.py"
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $root "versiones\antes_v2_18_$stamp\app"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

if (Test-Path $dest) {
    Copy-Item $dest (Join-Path $backupDir "dashboard_cosven.py") -Force
}

Copy-Item $src $dest -Force

Write-Host ""
Write-Host "Paykan COSVEN v2.18 aplicada correctamente." -ForegroundColor Green
Write-Host ""
Write-Host "Cambio funcional:"
Write-Host "- TM=NC permanece visible en el detalle."
Write-Host "- TM=NC queda fuera de Venta, Costo, Utilidad y % Utilidad usados para rentabilidad."
Write-Host "- La misma regla se aplica al resultado principal y a los KPI del popup."
Write-Host "- Fecha inicial: día anterior; si es domingo sin movimientos, abre el sábado."
Write-Host ""
Write-Host "No se modifican DBF, cosven.db, históricos, cálculos de costo ni tareas programadas."
Write-Host ""
Write-Host "Reinicie el dashboard para tomar el cambio:"
Write-Host "C:\Paykan\COSVEN\iniciar_dashboard.bat"
