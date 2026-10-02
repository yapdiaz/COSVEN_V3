Write-Host ""
Write-Host "=== TAREAS COSVEN ===" -ForegroundColor Cyan

Get-ScheduledTask |
Where-Object { $_.TaskName -like "Paykan COSVEN Actualizacion*" } |
ForEach-Object {
    $info = $_ | Get-ScheduledTaskInfo
    [PSCustomObject]@{
        Tarea = $_.TaskName
        Estado = $_.State
        UltimaEjecucion = $info.LastRunTime
        UltimoResultado = $info.LastTaskResult
        ProximaEjecucion = $info.NextRunTime
    }
} | Format-Table -AutoSize

Write-Host ""
Write-Host "=== METADATA LOCAL ===" -ForegroundColor Cyan

@'
import sqlite3

p = r"C:\Paykan\COSVEN\data\cosven.db"
c = sqlite3.connect(p)

for clave, valor in c.execute("""
    SELECT clave, valor
    FROM metadata
    WHERE clave IN (
        'ultima_actualizacion',
        'ultimo_desde',
        'ultimo_hasta',
        'actualizacion_estado',
        'actualizacion_origen',
        'actualizacion_inicio',
        'actualizacion_fin',
        'actualizacion_duracion_seg',
        'datos_hasta',
        'actualizacion_error'
    )
    ORDER BY clave
"""):
    print(f"{clave}: {valor}")

c.close()
'@ | & "C:\Users\IT\AppData\Local\Programs\Python\Python313\python.exe" -
