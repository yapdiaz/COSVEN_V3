$ErrorActionPreference = "Stop"

$root = "C:\Paykan\COSVEN"
$dest = Join-Path $root "app\dashboard_cosven.py"
$src  = Join-Path $PSScriptRoot "payload\app\dashboard_cosven.py"

if (-not (Test-Path $src)) {
    throw "No se encontró el dashboard corregido dentro del paquete."
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $root "versiones\antes_v2_5_1_$stamp\app"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

if (Test-Path $dest) {
    Copy-Item $dest (Join-Path $backupDir "dashboard_cosven.py") -Force
}

Copy-Item $src $dest -Force

Write-Host ""
Write-Host "HOTFIX v2.5.1 aplicado correctamente." -ForegroundColor Green
Write-Host "Se corrigió el bloque CSS que provocaba NameError: width."
Write-Host "No se modificó la lógica COSVEN, cosven.db, históricos ni caches."
Write-Host ""
Write-Host "Reinicie el dashboard con:"
Write-Host "C:\Paykan\COSVEN\iniciar_dashboard.bat"
