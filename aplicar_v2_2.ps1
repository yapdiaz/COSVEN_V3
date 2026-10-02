$ErrorActionPreference = "Stop"

$root = "C:\Paykan\COSVEN"
$dest = Join-Path $root "app\dashboard_cosven.py"
$src  = Join-Path $PSScriptRoot "payload\app\dashboard_cosven.py"

if (-not (Test-Path $src)) {
    throw "No se encontró el dashboard nuevo dentro del paquete."
}

if (-not (Test-Path (Join-Path $root "app"))) {
    throw "No existe C:\Paykan\COSVEN\app. Verifique la instalación actual."
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $root "versiones\antes_v2_2_$stamp\app"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

if (Test-Path $dest) {
    Copy-Item $dest (Join-Path $backupDir "dashboard_cosven.py") -Force
    Write-Host "Backup creado en:" -ForegroundColor Cyan
    Write-Host $backupDir
}

Copy-Item $src $dest -Force

Write-Host ""
Write-Host "Dashboard v2.2 aplicado correctamente." -ForegroundColor Green
Write-Host "No se modificó la lógica COSVEN, la base cosven.db, los históricos ni los caches."
Write-Host ""
Write-Host "Para cargar la nueva versión:"
Write-Host "1) Si el dashboard está abierto manualmente, cierre la consola de Streamlit."
Write-Host "2) Ejecute C:\Paykan\COSVEN\iniciar_dashboard.bat"
Write-Host ""
Write-Host "Si el dashboard se ejecuta mediante la tarea programada, reinicie únicamente esa tarea."
