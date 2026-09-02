@echo off
title Spacedesk Virtual Display Driver Installer
cd /d "%~dp0"
echo =========================================================
echo   Spacedesk Virtual Display Driver Installer
echo =========================================================
echo [*] Downloading latest official Spacedesk 64-bit driver MSI...

powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $url = 'https://www.spacedesk.net/download/spacedesk_driver_Win_10_64_v2229_BETA.msi'; $dest = Join-Path $env:TEMP 'spacedesk_driver.msi'; Write-Host 'Downloading to' $dest; Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing; Write-Host 'Launching installer with Admin prompt...'; Start-Process msiexec.exe -ArgumentList \"/i `\"$dest`\"\" -Verb RunAs"

echo.
echo [i] Follow the on-screen prompts to complete installation.
echo [i] Once installed, Windows will extend displays and Kali can connect via http://192.168.137.1:17882
pause
