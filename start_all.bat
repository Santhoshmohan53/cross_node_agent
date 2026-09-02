@echo off
title Aegis Dual-Node Launcher
cd /d "%~dp0"
echo ===================================================
echo   AEGIS: Launching Windows Daemon and Command Hub
echo ===================================================

start "Aegis Windows Daemon" cmd /k "python daemon\windows_daemon.py"
ping -n 3 127.0.0.1 >nul 2>&1
start "Aegis Command Hub" cmd /k "python hub_server.py"

echo [i] Windows Daemon and Command Hub started.
echo [i] Open your browser to http://localhost:8080
ping -n 5 127.0.0.1 >nul 2>&1
