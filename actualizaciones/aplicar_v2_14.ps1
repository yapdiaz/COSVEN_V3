$ErrorActionPreference = "Stop"

$root = "C:\Paykan\COSVEN"
$app = Join-Path $root "app"
$db = Join-Path $root "data\cosven.db"
$src = Join-Path $PSScriptRoot "payload\app"

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = Join-Path $root "versiones\antes_v2_14_$stamp"

New-Item -ItemType Directory -Force -Path (Join-Path $backup "app") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $backup "data") | Out-Null

foreach ($f in @("dashboard_cosven.py","cosven_periodo.py","cosven_store.py")) {
    $actual = Join-Path $app $f
    if (Test-Path $actual) {
        Copy-Item $actual (Join-Path $backup "app\$f") -Force
    }
}

if (Test-Path $db) {
    Copy-Item $db (Join-Path $backup "data\cosven.db") -Force
}

Copy-Item (Join-Path $src "dashboard_cosven.py") (Join-Path $app "dashboard_cosven.py") -Force
Copy-Item (Join-Path $src "cosven_periodo.py") (Join-Path $app "cosven_periodo.py") -Force
Copy-Item (Join-Path $src "cosven_store.py") (Join-Path $app "cosven_store.py") -Force
Copy-Item (Join-Path $src "backfill_usuario_pedido.py") (Join-Path $app "backfill_usuario_pedido.py") -Force

Write-Host ""
Write-Host "Aplicando usuario de QUIEN HIZO EL PEDIDO..." -ForegroundColor Cyan

$python = "C:\Users\IT\AppData\Local\Programs\Python\Python313\python.exe"
& $python (Join-Path $app "backfill_usuario_pedido.py")

if ($LASTEXITCODE -ne 0) {
    throw "Falló el backfill de usuario de pedido."
}

Write-Host ""
Write-Host "v2.14 aplicada correctamente." -ForegroundColor Green
Write-Host "La última columna del detalle ahora muestra quien hizo/cargó el pedido."
Write-Host "No se usa MOVART.CLAING para este dato."
Write-Host ""
Write-Host "Reinicie:"
Write-Host "C:\Paykan\COSVEN\iniciar_dashboard.bat"
