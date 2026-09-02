@echo off
title Route Windows Internet Through Kali Linux Gateway (192.168.137.177)
cd /d "%~dp0"
echo =======================================================================
echo   Aegis: Switch Windows Internet Gateway to Kali Linux (192.168.137.177)
echo =======================================================================
echo [*] Setting default gateway on Ethernet to Kali Linux (192.168.137.177)...

netsh interface ip set address name="Ethernet" static 192.168.137.1 255.255.255.0 192.168.137.177
netsh interface ip set dns name="Ethernet" static 8.8.8.8
netsh interface ip add dns name="Ethernet" 1.1.1.1 index=2

echo [*] Testing connectivity to Internet...
ping -n 2 8.8.8.8

echo.
echo [+] Configuration complete! Windows is now routing Internet through Kali Linux.
pause
