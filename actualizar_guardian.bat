@echo off
title Actualizar Guardian Not Again
cd /d "%~dp0"

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ejecuta este archivo como administrador:
    echo Clic derecho - Ejecutar como administrador.
    pause
    exit /b 1
)

echo Deteniendo temporalmente el guardian...
taskkill /F /IM pythonw.exe /T >nul 2>&1
schtasks /end /tn "NotAgainWatchdog" >nul 2>&1
timeout /t 2 /nobreak >nul

echo Aplicando mejoras en guardian.py...
set PY="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
%PY% patch_guardian.py

echo Reiniciando guardian blindado...
schtasks /run /tn "NotAgainWatchdog" >nul 2>&1

echo.
echo ==============================================================
echo   [OK] Guardian actualizado con exito.
echo   - Capturas automaticas en carpeta 'capturas_bloqueo/'.
echo   - Veto inteligente del Modo Sombra (evita falsos positivos en DJ sets/videos).
echo   - blender.exe vigilado por la IA.
echo ==============================================================
timeout /t 5
