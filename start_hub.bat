@echo off
title Aegis Unified Command Center Hub (Port 8080)
cd /d "%~dp0"
echo [*] Starting Aegis Unified Command Center Hub on http://localhost:8080 ...
python hub_server.py
pause
