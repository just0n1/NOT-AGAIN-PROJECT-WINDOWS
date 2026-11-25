@echo off
title Blindaje de Seguridad Not Again (Anti-Borrado)
cd /d "%~dp0"

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ejecuta este archivo como administrador:
    echo Clic derecho -> Ejecutar como administrador.
    pause
    exit /b 1
)

echo Aplicando denegacion de borrado NTFS a la carpeta y archivos...
icacls "%~dp0." /deny "%USERNAME%:(OI)(CI)(DE,DC)" >nul 2>&1

echo [OK] Carpeta blindada. El usuario no podra borrar ni la carpeta ni los archivos.
timeout /t 3
