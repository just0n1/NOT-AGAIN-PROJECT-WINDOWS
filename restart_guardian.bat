@echo off
title Reiniciar Not Again
cd /d "%~dp0"

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ejecuta este archivo como administrador:
    echo clic derecho - Ejecutar como administrador.
    pause
    exit /b 1
)

taskkill /F /IM pythonw.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul
schtasks /run /tn "NotAgainWatchdog" >nul 2>&1

echo [OK] Guardian reiniciado con el codigo actual.
timeout /t 3