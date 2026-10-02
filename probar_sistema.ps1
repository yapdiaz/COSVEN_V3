$root = "C:\Paykan\COSVEN"
Write-Host "=== Paykan COSVEN ==="
Write-Host "Proyecto:" (Test-Path $root)
Write-Host "Base SQLite:" (Test-Path "$root\data\cosven.db")
Write-Host "Dashboard:" (Test-Path "$root\app\dashboard_cosven.py")
Write-Host "Origen Paykan:" (Test-Path "\\Paykans\c\paykann\libres")
Write-Host "Puerto local 8501:"
Test-NetConnection 127.0.0.1 -Port 8501 | Select-Object ComputerName,RemotePort,TcpTestSucceeded
