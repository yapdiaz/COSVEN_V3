@echo off
cd /d C:\Paykan\COSVEN
set PY=C:\Users\IT\AppData\Local\Programs\Python\Python313\python.exe
%PY% app\preparar_cache_historica.py --desde 2026-08-01 --hasta 2026-08-31
if errorlevel 1 goto ERROR
%PY% app\cosven_periodo.py --desde 2026-08-01 --hasta 2026-08-31 --salida-dir C:\Paykan\COSVEN\data\validacion_agosto
if errorlevel 1 goto ERROR
%PY% app\validar_agosto.py
if errorlevel 1 goto ERROR
pause
exit /b 0
:ERROR
echo.
echo VALIDACION NO SUPERADA. No instalar automatizacion hasta revisar el log/salida.
pause
exit /b 1
