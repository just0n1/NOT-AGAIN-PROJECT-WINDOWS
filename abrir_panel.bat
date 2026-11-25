@echo off
title Not Again — Abrir Panel de Control
cd /d "%~dp0"
set PY="%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe"
start "" %PY% dashboard.py
