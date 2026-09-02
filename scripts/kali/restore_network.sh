#!/usr/bin/env bash
# ==============================================================================
# Kali Linux Network Restore / Revert Script
# Reverts Ethernet sharing settings to standard DHCP/Managed mode.
# ==============================================================================

if [ "$EUID" -ne 0 ]; then
  echo "[ERROR] Please run with sudo: sudo ./restore_network.sh"
  exit 1
fi

echo "[*] Restoring network configurations..."

# Remove shared connection profile if created
nmcli connection delete "BridgeToWindows" 2>/dev/null || true

# Flush iptables NAT rules if applied
iptables -t nat -F 2>/dev/null || true
iptables -F FORWARD 2>/dev/null || true

# Reset IP forwarding
sysctl -w net.ipv4.ip_forward=0 > /dev/null
rm -f /etc/sysctl.d/99-ipforward.conf

echo "[+] Network restored to default settings."
