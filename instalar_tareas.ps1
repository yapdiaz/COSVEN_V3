# Ejecutar como Administrador.
# Dashboard: arranca con Windows usando SYSTEM porque solo lee la base SQLite local.
# Actualización: pide credenciales de un usuario que tenga acceso de lectura a \\Paykans\c.

$ErrorActionPreference = "Stop"
$python = "C:\Users\IT\AppData\Local\Programs\Python\Python313\python.exe"
$root = "C:\Paykan\COSVEN"

if (-not (Test-Path $python)) {
    throw "No existe Python en $python"
}

$validation = "C:\Paykan\COSVEN\data\motor_validado_2026-08.ok"
if (-not (Test-Path $validation)) {
    throw "No se instalan tareas: primero debe superar validar_agosto.bat (falta $validation)"
}

if (-not (Test-Path "$root\data\cosven.db")) {
    throw "No se instalan tareas: primero debe finalizar inicializar_2026.bat"
}

# Dashboard al iniciar Windows
$dashAction = New-ScheduledTaskAction `
    -Execute $python `
    -Argument '-m streamlit run "C:\Paykan\COSVEN\app\dashboard_cosven.py" --server.address 0.0.0.0 --server.port 8501 --server.headless true' `
    -WorkingDirectory $root

$dashTrigger = New-ScheduledTaskTrigger -AtStartup
$dashPrincipal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$dashSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask `
    -TaskName "Paykan COSVEN Dashboard" `
    -Action $dashAction `
    -Trigger $dashTrigger `
    -Principal $dashPrincipal `
    -Settings $dashSettings `
    -Description "Publica el dashboard interno Paykan COSVEN en TCP 8501." `
    -Force | Out-Null

# Actualización diaria. Necesita credenciales con acceso UNC a Paykans.
$defaultUser = if ($env:USERDOMAIN) { "$env:USERDOMAIN\$env:USERNAME" } else { $env:USERNAME }
$cred = Get-Credential -UserName $defaultUser -Message "Usuario con acceso de lectura a \\Paykans\c para actualizar COSVEN"

$updAction = New-ScheduledTaskAction `
    -Execute $python `
    -Argument '"C:\Paykan\COSVEN\app\actualizar_mes.py"' `
    -WorkingDirectory $root

$updTrigger = New-ScheduledTaskTrigger -Daily -At 6:00AM
$updSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 4)

Register-ScheduledTask `
    -TaskName "Paykan COSVEN Actualizacion" `
    -Action $updAction `
    -Trigger $updTrigger `
    -Settings $updSettings `
    -User $cred.UserName `
    -Password $cred.GetNetworkCredential().Password `
    -RunLevel Highest `
    -Description "Reconstruye automáticamente el mes que contiene el día anterior y actualiza la base local COSVEN." `
    -Force | Out-Null

Write-Host "Tareas instaladas:" -ForegroundColor Green
Get-ScheduledTask -TaskName "Paykan COSVEN Dashboard", "Paykan COSVEN Actualizacion" |
    Select-Object TaskName, State
