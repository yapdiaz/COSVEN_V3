$ErrorActionPreference = "Stop"

$root = "C:\Paykan\COSVEN"
$dest = Join-Path $root "app\dashboard_cosven.py"
$src  = Join-Path $PSScriptRoot "payload\app\dashboard_cosven.py"

if (-not (Test-Path $src)) {
    throw "No se encontró payload\app\dashboard_cosven.py"
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $root "versiones\antes_v2_19_$stamp\app"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

if (Test-Path $dest) {
    Copy-Item $dest (Join-Path $backupDir "dashboard_cosven.py") -Force
}

Copy-Item $src $dest -Force

Write-Host ""
Write-Host "Paykan COSVEN v2.19 aplicada correctamente." -ForegroundColor Green
Write-Host ""
Write-Host "Cambio funcional:"
Write-Host "- TM=NC vuelve a participar en Venta, Costo y Utilidad con su signo real."
Write-Host "- Se elimina la exclusión completa de la familia 121."
Write-Host "- Se excluye únicamente el artículo 121-0012 (ENCOMIENDAS), igual que Power BI."
Write-Host "- La misma regla se aplica al resultado principal y a los KPI del popup."
Write-Host "- Se conserva la regla de fecha v2.18: domingo sin movimientos abre sábado."
Write-Host ""
Write-Host "No se modifican DBF, cosven.db, históricos, cálculos de costo ni tareas programadas."
Write-Host ""
Write-Host "Reinicie el dashboard para tomar el cambio:"
Write-Host "C:\Paykan\COSVEN\iniciar_dashboard.bat"
