$root = "C:\Paykan\COSVEN"
$stamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$dest = Join-Path $root "versiones\$stamp"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
foreach ($name in @("app", "assets", ".streamlit")) {
    $src = Join-Path $root $name
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $dest $name) -Recurse -Force
    }
}
Write-Host "Respaldo creado en $dest" -ForegroundColor Green
