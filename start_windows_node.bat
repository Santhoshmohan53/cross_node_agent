@echo off
title Aegis Windows Agent Daemon (Port 8766)
cd /d "%~dp0"
echo [*] Starting Aegis Windows Agent Daemon...
python daemon\windows_daemon.py
pause
