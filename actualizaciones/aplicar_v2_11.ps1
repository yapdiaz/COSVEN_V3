$ErrorActionPreference = "Stop"

$root = "C:\Paykan\COSVEN"
$app  = Join-Path $root "app"
$db   = Join-Path $root "data\cosven.db"
$src  = Join-Path $PSScriptRoot "payload\app"

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = Join-Path $root "versiones\antes_v2_11_$stamp"

New-Item -ItemType Directory -Force -Path (Join-Path $backup "app") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $backup "data") | Out-Null

$archivos = @(
    "dashboard_cosven.py",
    "cosven_periodo.py",
    "cosven_store.py"
)

foreach ($archivo in $archivos) {
    $actual = Join-Path $app $archivo
    if (Test-Path $actual) {
        Copy-Item $actual (Join-Path $backup "app\$archivo") -Force
    }
}

if (Test-Path $db) {
    Copy-Item $db (Join-Path $backup "data\cosven.db") -Force
}

foreach ($archivo in $archivos) {
    Copy-Item (Join-Path $src $archivo) (Join-Path $app $archivo) -Force
}

Copy-Item (Join-Path $src "enriquecer_detalle.py") (Join-Path $app "enriquecer_detalle.py") -Force

Write-Host ""
Write-Host "Archivos v2.11 aplicados." -ForegroundColor Green
Write-Host "Backup:" -ForegroundColor Cyan
Write-Host $backup
Write-Host ""
Write-Host "Ahora se enriquecerá SOLO la base local cosven.db." -ForegroundColor Yellow
Write-Host "Los DBF de Paykan se abren únicamente en modo lectura."
Write-Host ""

$python = "C:\Users\IT\AppData\Local\Programs\Python\Python313\python.exe"

if (-not (Test-Path $python)) {
    throw "No se encontró Python en $python"
}

& $python (Join-Path $app "enriquecer_detalle.py")

if ($LASTEXITCODE -ne 0) {
    throw "Falló el enriquecimiento de la base local. Se conserva el backup."
}

Write-Host ""
Write-Host "v2.11 finalizada correctamente." -ForegroundColor Green
Write-Host "Reinicie el dashboard con:"
Write-Host "C:\Paykan\COSVEN\iniciar_dashboard.bat"
