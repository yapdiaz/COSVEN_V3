# Ejecutar como Administrador.
# Crea dos horarios automáticos y una tarea manual bajo un usuario
# con acceso de lectura a \\Paykans\c.

$ErrorActionPreference = "Stop"

$python = "C:\Users\IT\AppData\Local\Programs\Python\Python313\python.exe"
$root = "C:\Paykan\COSVEN"
$script = "C:\Paykan\COSVEN\app\actualizar_mes.py"

if (-not (Test-Path $python)) {
    throw "No existe Python en $python"
}

if (-not (Test-Path $script)) {
    throw "No existe $script. Aplique primero la actualización v2.15."
}

if (-not (Test-Path "$root\data\cosven.db")) {
    throw "No existe $root\data\cosven.db"
}

$defaultUser = if ($env:USERDOMAIN) {
    "$env:USERDOMAIN\$env:USERNAME"
} else {
    $env:USERNAME
}

$cred = Get-Credential `
    -UserName $defaultUser `
    -Message "Usuario Windows con acceso de lectura a \\Paykans\c"

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 3) `
    -MultipleInstances IgnoreNew

# 05:00 - consolida hasta el día anterior.
$action0500 = New-ScheduledTaskAction `
    -Execute $python `
    -Argument '"C:\Paykan\COSVEN\app\actualizar_mes.py" --modo cierre --origen programada-0500' `
    -WorkingDirectory $root

$trigger0500 = New-ScheduledTaskTrigger -Daily -At 5:00AM

Register-ScheduledTask `
    -TaskName "Paykan COSVEN Actualizacion 0500" `
    -Action $action0500 `
    -Trigger $trigger0500 `
    -Settings $settings `
    -User $cred.UserName `
    -Password $cred.GetNetworkCredential().Password `
    -RunLevel Highest `
    -Description "Actualiza el mes abierto COSVEN a las 05:00 y consolida hasta ayer." `
    -Force | Out-Null

# 13:00 - incorpora el día actual de forma intradía.
$action1300 = New-ScheduledTaskAction `
    -Execute $python `
    -Argument '"C:\Paykan\COSVEN\app\actualizar_mes.py" --modo intradia --origen programada-1300' `
    -WorkingDirectory $root

$trigger1300 = New-ScheduledTaskTrigger -Daily -At 1:00PM

Register-ScheduledTask `
    -TaskName "Paykan COSVEN Actualizacion 1300" `
    -Action $action1300 `
    -Trigger $trigger1300 `
    -Settings $settings `
    -User $cred.UserName `
    -Password $cred.GetNetworkCredential().Password `
    -RunLevel Highest `
    -Description "Actualiza el mes abierto COSVEN a las 13:00 incluyendo el día en curso." `
    -Force | Out-Null

# Tarea sin horario: la ejecuta el botón del dashboard.
$actionManual = New-ScheduledTaskAction `
    -Execute $python `
    -Argument '"C:\Paykan\COSVEN\app\actualizar_mes.py" --modo intradia --origen manual' `
    -WorkingDirectory $root

Register-ScheduledTask `
    -TaskName "Paykan COSVEN Actualizacion Manual" `
    -Action $actionManual `
    -Settings $settings `
    -User $cred.UserName `
    -Password $cred.GetNetworkCredential().Password `
    -RunLevel Highest `
    -Description "Actualización COSVEN bajo demanda desde el botón del dashboard." `
    -Force | Out-Null

Write-Host ""
Write-Host "Tareas de actualización instaladas:" -ForegroundColor Green

Get-ScheduledTask `
    -TaskName "Paykan COSVEN Actualizacion 0500",
              "Paykan COSVEN Actualizacion 1300",
              "Paykan COSVEN Actualizacion Manual" |
    Select-Object TaskName, State

Write-Host ""
Write-Host "Horarios:" -ForegroundColor Cyan
Write-Host "05:00 -> mes abierto hasta AYER"
Write-Host "13:00 -> mes abierto incluyendo HOY"
Write-Host "Manual -> botón 'Actualizar datos ahora'"
