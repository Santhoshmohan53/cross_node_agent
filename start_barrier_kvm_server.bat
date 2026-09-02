@echo off
title Aegis Barrier / Deskflow KVM Server (Port 24800)
cd /d "%~dp0"
echo =========================================================
echo   Aegis Barrier / Deskflow KVM Server (Windows Host)
echo =========================================================
echo [*] Server IP: 192.168.137.1:24800
echo [*] Screen 1 (Primary): DESKTOP-74DM2T1
echo [*] Screen 2 (Right): ghost (Kali Linux Mini PC)
echo [*] Keystrokes: Ctrl+Alt+K (Switch to Kali), Ctrl+Alt+W (Switch to Windows)
echo =========================================================

bin\deskflow\deskflow-1.26.0-win-x64-portable\deskflow-core.exe server
pause
