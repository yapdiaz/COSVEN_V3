$ErrorActionPreference = "Stop"

$root = "C:\Paykan\COSVEN"
$app  = Join-Path $root "app"
$src  = Join-Path $PSScriptRoot "payload\app\backfill_usuario_pedido_rapido.py"
$dest = Join-Path $app "backfill_usuario_pedido_rapido.py"

if (-not (Test-Path $src)) {
    throw "No se encontró el script rápido."
}

Copy-Item $src $dest -Force

$python = "C:\Users\IT\AppData\Local\Programs\Python\Python313\python.exe"
if (-not (Test-Path $python)) {
    throw "No se encontró Python en $python"
}

Write-Host ""
Write-Host "Iniciando backfill rápido..." -ForegroundColor Cyan
Write-Host "Primero copia PEDIDOS.DBF y USUARIOS.DBF a cache local."
Write-Host "Luego procesa localmente y muestra progreso."
Write-Host ""

& $python $dest

if ($LASTEXITCODE -ne 0) {
    throw "Falló el backfill rápido."
}

Write-Host ""
Write-Host "Proceso finalizado correctamente." -ForegroundColor Green
Write-Host "Reinicie el dashboard:"
Write-Host "C:\Paykan\COSVEN\iniciar_dashboard.bat"
