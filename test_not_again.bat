@echo off
title Not Again - Modo Prueba (Dry Run)
cd /d "%~dp0"
set PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%

echo ======================================================
echo           NOT AGAIN - MODO PRUEBA / CALIBRACION
echo ======================================================
echo En este modo se mediran los niveles NSFW en tiempo real
echo pero NO se cerrara el navegador.
echo.
python guardian.py --dry-run
pause
