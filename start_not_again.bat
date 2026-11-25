@echo off
title Not Again - Guardian de Pureza
cd /d "%~dp0"
set PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%

echo ======================================================
echo           NOT AGAIN - GUARDIAN ACTIVO
echo ======================================================
echo Protegiendo navegadores contra pornografia y soft-porn...
echo.
python guardian.py
pause
