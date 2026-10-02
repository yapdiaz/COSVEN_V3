$ErrorActionPreference = "Stop"

$root = "C:\Paykan\COSVEN"
$app = Join-Path $root "app"
$src = Join-Path $PSScriptRoot "payload\app"

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = Join-Path $root "versiones\antes_v2_15_$stamp\app"
New-Item -ItemType Directory -Force -Path $backup | Out-Null

foreach ($f in @(
    "dashboard_cosven.py",
    "cosven_periodo.py",
    "cosven_store.py",
    "actualizar_mes.py"
)) {
    $actual = Join-Path $app $f
    if (Test-Path $actual) {
        Copy-Item $actual (Join-Path $backup $f) -Force
    }

    Copy-Item (Join-Path $src $f) $actual -Force
}

if (-not (Test-Path (Join-Path $app "preparar_cache_historica.py"))) {
    throw "Falta C:\Paykan\COSVEN\app\preparar_cache_historica.py"
}

Write-Host ""
Write-Host "v2.15 aplicada correctamente." -ForegroundColor Green
Write-Host "Backup:" -ForegroundColor Cyan
Write-Host $backup
Write-Host ""
Write-Host "Siguiente paso:"
Write-Host "Ejecute INSTALAR_TAREAS_ACTUALIZACION.bat como administrador."
