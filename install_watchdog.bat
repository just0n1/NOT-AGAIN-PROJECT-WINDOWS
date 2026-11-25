@echo off
title Instalar vigilante de Not Again
cd /d "%~dp0"

set PYTHONW_EXE=%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe
set SCRIPT_PATH=%~dp0guardian.py

schtasks /create /tn "NotAgainWatchdog" /tr "\"%PYTHONW_EXE%\" \"%SCRIPT_PATH%\"" /sc minute /mo 1 /rl HIGHEST /f

if %ERRORLEVEL% equ 0 (
    echo [EXITO] El guardian se relanzara solo cada minuto si lo cierras.
) else (
    echo [ERROR] Ejecutalo como administrador.
)
pause