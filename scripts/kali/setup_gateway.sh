#!/usr/bin/env bash
# ==============================================================================
# Kali Linux Gateway & Network Sharing Setup Script
# Configures Kali Mini PC as the primary Wi-Fi Router/Gateway and shares
# Internet to the connected Windows PC via Ethernet LAN.
# ==============================================================================

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}=====================================================${NC}"
echo -e "${CYAN}    Kali Linux Gateway & LAN Bridge Configurator    ${NC}"
echo -e "${CYAN}=====================================================${NC}"

if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[ERROR] Please run this script with sudo: sudo ./setup_gateway.sh${NC}"
  exit 1
fi

# 1. Detect Network Interfaces
echo -e "\n${YELLOW}[1/5] Detecting Network Interfaces...${NC}"

# Find Wi-Fi interface (wlan*, wlp*, etc.)
WIFI_IFACE=$(ip link | grep -oE '(wlan[0-9]+|wlp[0-9]+s[0-9]+|wlx[0-9a-fA-F]+)' | head -n 1)
if [ -z "$WIFI_IFACE" ]; then
    # Fallback search via iw
    WIFI_IFACE=$(iw dev 2>/dev/null | awk '$1=="Interface"{print $2}' | head -n 1)
fi

# Find Ethernet interface (eth*, enp*, etc.)
ETH_IFACE=$(ip link | grep -oE '(eth[0-9]+|enp[0-9]+s[0-9]+|eno[0-9]+|enx[0-9a-fA-F]+)' | head -n 1)

echo -e "  -> Detected Wi-Fi Interface   : ${GREEN}${WIFI_IFACE:-'None found'}${NC}"
echo -e "  -> Detected Ethernet Interface: ${GREEN}${ETH_IFACE:-'None found'}${NC}"

if [ -z "$ETH_IFACE" ]; then
    echo -e "${RED}[ERROR] No Ethernet interface found! Ensure the LAN cable is plugged in.${NC}"
    exit 1
fi

if [ -z "$WIFI_IFACE" ]; then
    echo -e "${YELLOW}[WARN] No Wi-Fi interface detected automatically. Ensure your Wi-Fi adapter is connected.${NC}"
fi

# 2. Enable Kernel IP Forwarding
echo -e "\n${YELLOW}[2/5] Enabling Kernel IPv4 Forwarding...${NC}"
sysctl -w net.ipv4.ip_forward=1 > /dev/null
echo "net.ipv4.ip_forward = 1" > /etc/sysctl.d/99-ipforward.conf
sysctl --system > /dev/null
echo -e "  -> ${GREEN}net.ipv4.ip_forward enabled permanently.${NC}"

# 3. Configure Ethernet Connection Sharing via NetworkManager
echo -e "\n${YELLOW}[3/5] Configuring NetworkManager Connection Sharing on ${ETH_IFACE}...${NC}"

# Check if NetworkManager is active
if systemctl is-active --quiet NetworkManager; then
    NM_CON_NAME="BridgeToWindows"

    # Delete existing connection with this name if exists
    nmcli connection delete "$NM_CON_NAME" 2>/dev/null || true

    # Create new shared connection on the Ethernet interface
    echo -e "  -> Creating shared connection profile '${NM_CON_NAME}' on ${ETH_IFACE}..."
    nmcli connection add type ethernet ifname "$ETH_IFACE" con-name "$NM_CON_NAME" \
        ipv4.method shared \
        ipv6.method ignore

    # Bring up the connection
    echo -e "  -> Activating shared connection..."
    nmcli connection up "$NM_CON_NAME"

    echo -e "  -> ${GREEN}NetworkManager shared connection active!${NC}"
    echo -e "     Kali Ethernet IP is automatically set to ${CYAN}10.42.0.1${NC}."
    echo -e "     DHCP & DNS are running for the Windows client."
else
    # Fallback to iptables + dnsmasq if NetworkManager is disabled
    echo -e "  -> ${YELLOW}NetworkManager not active, configuring via iptables fallback...${NC}"
    
    ip addr flush dev "$ETH_IFACE"
    ip addr add 192.168.100.1/24 dev "$ETH_IFACE"
    ip link set "$ETH_IFACE" up

    # iptables NAT Masquerade
    iptables -F
    iptables -t nat -F
    if [ -n "$WIFI_IFACE" ]; then
        iptables -t nat -A POSTROUTING -o "$WIFI_IFACE" -j MASQUERADE
        iptables -A FORWARD -i "$ETH_IFACE" -o "$WIFI_IFACE" -j ACCEPT
        iptables -A FORWARD -i "$WIFI_IFACE" -o "$ETH_IFACE" -m state --state RELATED,ESTABLISHED -j ACCEPT
    fi
    echo -e "  -> ${GREEN}iptables NAT configured.${NC}"
fi

# 4. Check Wi-Fi Monitor Mode Capability
echo -e "\n${YELLOW}[4/5] Checking Wi-Fi Monitor Mode Capabilities...${NC}"
if [ -n "$WIFI_IFACE" ]; then
    MODES=$(iw phy 2>/dev/null | grep -A 10 "Supported interface modes" | grep "monitor" || true)
    if [ -n "$MODES" ]; then
        echo -e "  -> ${GREEN}Wi-Fi adapter supports MONITOR MODE!${NC}"
    else
        echo -e "  -> ${YELLOW}Wi-Fi adapter monitor mode support unconfirmed.${NC}"
    fi
fi

# 5. Status Summary
echo -e "\n${CYAN}=====================================================${NC}"
echo -e "${GREEN} Gateway Setup Complete!${NC}"
echo -e "${CYAN}=====================================================${NC}"
echo -e "1. ${CYAN}Kali Gateway IP${NC}   : 10.42.0.1 (or 192.168.100.1)"
echo -e "2. ${CYAN}Windows Client${NC}    : Set Windows LAN adapter to DHCP (auto obtain IP)"
echo -e "3. ${CYAN}Aegis Daemon${NC}      : Launch 'python3 daemon/kali_daemon.py'"
echo -e "4. ${CYAN}Testing${NC}           : Windows will be able to ping 10.42.0.1 and access Internet"
echo -e "${CYAN}=====================================================${NC}\n"
