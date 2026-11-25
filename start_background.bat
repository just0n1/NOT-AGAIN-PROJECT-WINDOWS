@echo off
title Not Again - Iniciar en Segundo Plano
cd /d "%~dp0"
set PYTHONW_EXE=%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe

start "" "%PYTHONW_EXE%" "%~dp0guardian.py"
echo ==============================================================
echo [EXITO] Not Again esta corriendo silenciosamente en segundo plano.
echo Protegiendo tus navegadores sin ventanas abiertas.
echo Puedes verificar los eventos en guardian.log
echo ==============================================================
timeout /t 3
exit
