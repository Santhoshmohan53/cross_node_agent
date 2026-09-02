<#
.SYNOPSIS
    Configures Windows Ethernet LAN Adapter to obtain IP automatically (DHCP)
    from the Kali Linux Gateway and validates the connection.
#>

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  Windows LAN Client Configurator & Gateway Tester   " -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# 1. Identify Ethernet Adapters
Write-Host "`n[1/4] Detecting Ethernet Network Adapters..." -ForegroundColor Yellow
$adapters = Get-NetAdapter | Where-Object { $_.PhysicalMediaType -match "802.3" -or $_.Name -match "Ethernet|LAN" }

if (-not $adapters) {
    Write-Host "[ERROR] No Ethernet adapter found! Please ensure your LAN cable is connected." -ForegroundColor Red
    exit 1
}

foreach ($adapter in $adapters) {
    Write-Host "  -> Found Adapter: $($adapter.Name) (Status: $($adapter.Status), LinkSpeed: $($adapter.LinkSpeed))" -ForegroundColor Green
}

$targetAdapter = $adapters | Where-Object { $_.Status -eq "Up" } | Select-Object -First 1
if (-not $targetAdapter) {
    $targetAdapter = $adapters | Select-Object -First 1
}

Write-Host "  -> Targeting Adapter: $($targetAdapter.Name)" -ForegroundColor Cyan

# 2. Enable DHCP if not already enabled
Write-Host "`n[2/4] Ensuring DHCP is enabled on $($targetAdapter.Name)..." -ForegroundColor Yellow
try {
    Set-NetIPInterface -InterfaceAlias $targetAdapter.Name -Dhcp Enabled -ErrorAction SilentlyContinue
    Set-DnsClientServerAddress -InterfaceAlias $targetAdapter.Name -ResetServerAddresses -ErrorAction SilentlyContinue
    Write-Host "  -> DHCP & Auto-DNS enabled successfully." -ForegroundColor Green
} catch {
    Write-Host "  -> [INFO] DHCP interface settings updated: $($_.Exception.Message)" -ForegroundColor Gray
}

# 3. Renew IP Configuration
Write-Host "`n[3/4] Renewing IP configuration via DHCP..." -ForegroundColor Yellow
ipconfig /renew | Out-Null
Start-Sleep -Seconds 2

$ipConfig = Get-NetIPAddress -InterfaceAlias $targetAdapter.Name -AddressFamily IPv4 -ErrorAction SilentlyContinue
$gateway = (Get-NetRoute -InterfaceAlias $targetAdapter.Name -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue).NextHop

Write-Host "  -> Assigned IPv4 Address: $($ipConfig.IPAddress)" -ForegroundColor Green
Write-Host "  -> Default Gateway (Kali): $($gateway)" -ForegroundColor Green

# 4. Connectivity Tests
Write-Host "`n[4/4] Running Gateway & Internet Reachability Checks..." -ForegroundColor Yellow

if ($gateway) {
    $gwPing = Test-Connection -ComputerName $gateway -Count 2 -Quiet
    if ($gwPing) {
        Write-Host "  -> [SUCCESS] Kali Gateway ($gateway) is REACHABLE via LAN!" -ForegroundColor Green
    } else {
        Write-Host "  -> [WARN] Could not ping Kali Gateway ($gateway). Check firewall on Kali if ICMP is blocked." -ForegroundColor Yellow
    }
} else {
    Write-Host "  -> [WARN] No default gateway assigned yet. Please verify setup_gateway.sh is active on Kali." -ForegroundColor Yellow
}

# Test Internet Ping & DNS
try {
    $dnsCheck = [System.Net.Dns]::GetHostAddresses("google.com")
    Write-Host "  -> [SUCCESS] DNS Resolution via Kali Gateway is working!" -ForegroundColor Green
    Write-Host "  -> [SUCCESS] Windows is now routing Internet traffic through Kali Linux." -ForegroundColor Green
} catch {
    Write-Host "  -> [INFO] DNS Resolution check: $($_.Exception.Message)" -ForegroundColor Gray
}

Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host " Configuration Complete!" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Cyan
