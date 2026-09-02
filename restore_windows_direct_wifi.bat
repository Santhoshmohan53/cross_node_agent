@echo off
title Restore Windows Direct Wi-Fi Connection
cd /d "%~dp0"
echo =======================================================================
echo   Aegis: Restore Windows Host Direct Wi-Fi Connection
echo =======================================================================
echo [*] Resetting Ethernet adapter to Host ICS mode (192.168.137.1 no gateway)...

netsh interface ip set address name="Ethernet" static 192.168.137.1 255.255.255.0 none
netsh interface ip set dns name="Ethernet" none

echo [+] Ethernet set to Host ICS mode.
pause
