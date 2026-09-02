import paramiko

def prepare_kali_gateway_script():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('192.168.137.177', port=22, username='ghost', password='9233', timeout=5)

    script = """#!/bin/bash
# Aegis Kali Linux NAT Gateway & Monitor Mode Setup Script
set -e

echo "======================================================="
echo "  Aegis Kali Linux: NAT Gateway & Routing Enabler"
echo "======================================================="

# 1. Enable IPv4 Kernel Forwarding
echo "[1/4] Enabling IPv4 packet forwarding..."
echo 1 > /proc/sys/net/ipv4/ip_forward
sysctl -w net.ipv4.ip_forward=1 >/dev/null

# 2. Check for wireless interface
echo "[2/4] Detecting wireless adapter..."
WLAN_IF=$(iw dev | grep Interface | awk '{print $2}' | head -n 1)

if [ -z "$WLAN_IF" ]; then
    echo "[!] No wireless interface detected yet. Please plug in the USB WiFi adapter."
else
    echo "[+] Detected wireless interface: $WLAN_IF"
    
    # 3. Configure NAT / iptables Masquerading
    echo "[3/4] Configuring iptables NAT Masquerade ($WLAN_IF -> eth0)..."
    iptables -t nat -F
    iptables -F FORWARD
    iptables -t nat -A POSTROUTING -o "$WLAN_IF" -j MASQUERADE
    iptables -A FORWARD -i eth0 -o "$WLAN_IF" -j ACCEPT
    iptables -A FORWARD -i "$WLAN_IF" -o eth0 -m state --state RELATED,ESTABLISHED -j ACCEPT
    echo "[+] NAT forwarding is active."
fi

# 4. Save rules
echo "[4/4] Gateway configuration ready."
"""
    client.exec_command(f"cat << 'EOF' > /home/ghost/aegis/setup_kali_gateway.sh\n{script}\nEOF")
    client.exec_command("chmod +x /home/ghost/aegis/setup_kali_gateway.sh")
    print("[+] Created /home/ghost/aegis/setup_kali_gateway.sh on Kali Linux.")
    client.close()

if __name__ == "__main__":
    prepare_kali_gateway_script()
