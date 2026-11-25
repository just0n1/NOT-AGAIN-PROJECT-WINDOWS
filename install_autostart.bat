@echo off
title Instalar Not Again en Inicio Automatico
cd /d "%~dp0"

echo ==============================================================
echo        INSTALANDO NOT AGAIN EN EL INICIO DE WINDOWS
echo ==============================================================
echo.
echo Configurando el Guardian para que arranque silenciosamente
echo en segundo plano cada vez que inicies tu sesion de Windows...
echo (Sin ventanas de consola abiertas, totalmente invisible).
echo.

set PYTHONW_EXE=%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe
set SCRIPT_PATH=%~dp0guardian.py

if not exist "%PYTHONW_EXE%" (
    echo [ERROR] No se encontro pythonw.exe en %PYTHONW_EXE%
    pause
    exit /b 1
)

:: Crear Tarea Programada en Windows (schtasks) al inicio de sesion
schtasks /create /tn "NotAgainGuardian" /tr "\"%PYTHONW_EXE%\" \"%SCRIPT_PATH%\"" /sc onlogon /f /rl HIGHEST

if %ERRORLEVEL% equ 0 (
    echo.
    echo ==============================================================
    echo [EXITO] Not Again ha sido instalado como Guardian Permanente.
    echo Arrancara de forma automatica cada vez que enciendas el PC.
    echo ==============================================================
) else (
    echo.
    echo [ERROR] No se pudo crear la tarea programada.
)

echo.
pause
