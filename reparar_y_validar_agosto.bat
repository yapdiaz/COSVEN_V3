@echo off
setlocal
cd /d C:\Paykan\COSVEN
set PY=C:\Users\IT\AppData\Local\Programs\Python\Python313\python.exe

echo ============================================================
echo PAYKAN COSVEN - REPARACION CACHE HISTORICA + VALIDACION
echo ============================================================
echo.
echo Este proceso NO modifica DBF de Paykan.
echo Solo reconstruye:
echo C:\Paykan\COSVEN\cache\cosven_historico_2026.pkl
echo.

if not exist C:\Paykan\COSVEN\cache\backups mkdir C:\Paykan\COSVEN\cache\backups

if exist C:\Paykan\COSVEN\cache\cosven_historico_2026.pkl (
    for /f "tokens=1-4 delims=/ " %%a in ("%date%") do set FDATE=%%d%%b%%c
    for /f "tokens=1-3 delims=:,. " %%a in ("%time%") do set FTIME=%%a%%b%%c
    copy /y C:\Paykan\COSVEN\cache\cosven_historico_2026.pkl C:\Paykan\COSVEN\cache\backups\cosven_historico_2026_antes_fix.pkl >nul
    echo Backup creado:
    echo C:\Paykan\COSVEN\cache\backups\cosven_historico_2026_antes_fix.pkl
    echo.
)

if exist C:\Paykan\COSVEN\data\motor_validado_2026-08.ok del /q C:\Paykan\COSVEN\data\motor_validado_2026-08.ok

echo [1/3] Reconstruyendo cache agosto con clave ART preservando espacios...
%PY% app\preparar_cache_historica.py --desde 2026-08-01 --hasta 2026-08-31 --reconstruir
if errorlevel 1 goto ERROR

echo.
echo [2/3] Recalculando agosto...
%PY% app\cosven_periodo.py --desde 2026-08-01 --hasta 2026-08-31 --salida-dir C:\Paykan\COSVEN\data\validacion_agosto
if errorlevel 1 goto ERROR

echo.
echo [3/3] Comparando contra la base validada...
%PY% app\validar_agosto.py
if errorlevel 1 goto ERROR

echo.
echo ============================================================
echo VALIDACION SUPERADA
echo ============================================================
echo Si aparece "VALIDACION OK: resultados identicos para agosto 2026",
echo el cache quedo corregido.
pause
exit /b 0

:ERROR
echo.
echo ============================================================
echo VALIDACION NO SUPERADA
echo ============================================================
echo No ejecutar inicializar_2026.bat.
echo Pasar la salida completa para revisar.
pause
exit /b 1
