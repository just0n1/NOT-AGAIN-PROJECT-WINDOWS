@echo off
title Desinstalar Not Again del Inicio Automatico
echo ==============================================================
echo        DESINSTALANDO NOT AGAIN DEL INICIO DE WINDOWS
echo ==============================================================
echo.
schtasks /delete /tn "NotAgainGuardian" /f
schtasks /delete /tn "NotAgainWatchdog" /f
taskkill /F /IM pythonw.exe /T >nul 2>&1
echo.
echo Tareas eliminadas y guardian detenido. Not Again ya no iniciara solo.
pause