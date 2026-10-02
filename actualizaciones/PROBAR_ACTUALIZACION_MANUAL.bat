@echo off
cd /d C:\Paykan\COSVEN
C:\Windows\System32\schtasks.exe /Run /TN "Paykan COSVEN Actualizacion Manual"
echo.
echo La tarea fue solicitada. Use VERIFICAR_ACTUALIZACIONES.bat para consultar el estado.
pause
