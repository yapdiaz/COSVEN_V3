$ErrorActionPreference = "Stop"

$root = "C:\Paykan\COSVEN"
$dest = Join-Path $root "app\cosven_periodo.py"
$src  = Join-Path $PSScriptRoot "payload\app\cosven_periodo.py"

if (-not (Test-Path $src)) {
    throw "No se encontró payload\app\cosven_periodo.py"
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $root "versiones\antes_v2_15_1_$stamp\app"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

if (Test-Path $dest) {
    Copy-Item $dest (Join-Path $backupDir "cosven_periodo.py") -Force
}

Copy-Item $src $dest -Force

Write-Host ""
Write-Host "Hotfix v2.15.1 aplicado correctamente." -ForegroundColor Green
Write-Host "Corrige únicamente la exportación del detalle: DTO y USUARIO ahora están incluidos en los encabezados CSV."
Write-Host "No modifica DBF, base histórica, cálculos COSVEN, dashboard ni tareas programadas."
Write-Host ""
