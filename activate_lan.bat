@echo off
:: Self-elevation check
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Requesting Administrator privileges to enable network hardware...
    powershell -Command "Start-Process cmd -ArgumentList '/c ""%~f0""' -Verb RunAs"
    exit /b
)

title AEGIS: Activate LAN Connection (Intel Ethernet + Kali Linux)
echo =======================================================================
echo          ACTIVATING ETHERNET LAN ADAPTER FOR KALI LINUX
echo =======================================================================
echo.

echo [*] Enabling Intel Ethernet PnP Hardware Device...
pnputil /enable-device "PCI\VEN_8086&DEV_15A0&SUBSYS_2129103C&REV_05\3&11583659&0&C8"

echo [*] Enabling Ethernet Network Interface in Windows...
netsh interface set interface name="Ethernet" admin=ENABLED >nul 2>&1

echo [*] Configuring DHCP and DNS on Ethernet...
netsh interface ip set address name="Ethernet" dhcp >nul 2>&1
netsh interface ip set dns name="Ethernet" dhcp >nul 2>&1

echo [*] Renewing IP configuration...
ipconfig /renew Ethernet

echo.
echo =======================================================================
echo Ethernet Adapter Activated Successfully!
echo =======================================================================
echo.
pause
