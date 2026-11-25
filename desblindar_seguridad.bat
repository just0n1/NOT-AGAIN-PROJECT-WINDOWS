@echo off
title Desblindar Seguridad Not Again
cd /d "%~dp0"

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ejecuta este archivo como administrador:
    echo Clic derecho -> Ejecutar como administrador.
    pause
    exit /b 1
)

echo Removiendo restriccion de borrado...
icacls "%~dp0." /remove:d "%USERNAME%" >nul 2>&1

echo [OK] Restriccion removida para actualizaciones o mantenimiento.
timeout /t 3
