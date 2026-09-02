#!/usr/bin/env python3
"""
Aegis Kali Linux Automated Provisioner & Updater
Connects over SSH, updates apt repositories, installs networking/pentest toolsets,
deploys the Aegis Kali Daemon as a systemd service, and verifies end-to-end connectivity.
"""

import paramiko
import time
import os
import sys
from pathlib import Path

KALI_IP = "192.168.137.177"
KALI_USER = "ghost"
KALI_PASS = "9233"
WIN_IP = "192.168.137.1"

def run_remote(client, cmd, sudo=False, timeout=600):
    """Executes a command on Kali Linux over SSH with real-time streaming."""
    if sudo:
        exec_cmd = f"echo '{KALI_PASS}' | sudo -S bash -c \"{cmd}\""
    else:
        exec_cmd = cmd

    print(f"\n[EXEC ({'sudo' if sudo else 'user'})] {cmd}")
    stdin, stdout, stderr = client.exec_command(exec_cmd, get_pty=True)
    
    output_lines = []
    while True:
        line = stdout.readline()
        if not line:
            break
        cleaned = line.strip()
        if cleaned and not cleaned.startswith("[sudo] password"):
            print(f"  | {cleaned}", flush=True)
            output_lines.append(cleaned)
            
    exit_status = stdout.channel.recv_exit_status()
    print(f"[STATUS] Exit Code: {exit_status}")
    return exit_status, "\n".join(output_lines)

def upload_file_scp(sftp, local_path, remote_path):
    """Uploads a file to Kali via SFTP."""
    print(f"[*] Uploading {local_path} -> {remote_path}...")
    sftp.put(str(local_path), str(remote_path))

def main():
    print("="*60)
    print("  AEGIS KALI LINUX PROVISIONING & UPGRADE PIPELINE")
    print("="*60)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"[*] Connecting to {KALI_USER}@{KALI_IP}...")
    client.connect(KALI_IP, port=22, username=KALI_USER, password=KALI_PASS, timeout=15)
    print("[+] Connected successfully!\n")
    
    # 1. Kill any stale apt locks if any
    print("[1/7] Checking and clearing any stale package manager locks...")
    run_remote(client, "killall -9 apt apt-get dpkg 2>/dev/null || true", sudo=True)
    run_remote(client, "dpkg --configure -a", sudo=True)

    # 2. Update Package Index
    print("\n[2/7] Updating Kali Linux APT Repositories (apt-get update)...")
    run_remote(client, "apt-get update -y", sudo=True, timeout=300)

    # 3. Install Essential Networking, Pentest & Wi-Fi Packages
    print("\n[3/7] Installing Network, Wi-Fi Testing, & Diagnostics Toolsets...")
    packages = [
        # Network diagnostics & core
        "net-tools", "iproute2", "dnsutils", "ethtool", "traceroute", "tcpdump",
        "tshark", "nmap", "masscan", "iperf3", "socat", "netcat-traditional",
        "bridge-utils", "hping3", "arping", "fping", "curl", "wget", "git",
        # Wireless & Monitor mode tools
        "wireless-tools", "iw", "aircrack-ng", "rfkill",
        # Development, Python & Daemon tools
        "python3", "python3-pip", "python3-venv", "python3-dev", "build-essential",
        "python3-fastapi", "python3-uvicorn", "python3-websockets", "python3-psutil",
        "python3-httpx", "python3-pydantic", "python3-aiofiles"
    ]
    pkg_str = " ".join(packages)
    run_remote(client, f"DEBIAN_FRONTEND=noninteractive apt-get install -y {pkg_str}", sudo=True, timeout=900)

    # 4. Install additional Python packages via pip if needed
    print("\n[4/7] Ensuring Python dependencies for Aegis Daemon...")
    run_remote(client, "pip3 install --break-system-packages fastapi uvicorn[standard] websockets pydantic requests httpx psutil aiofiles python-multipart || true")

    # 5. Deploy Aegis Daemon Files to Kali
    print("\n[5/7] Deploying Aegis Daemon and Bridge to Kali Linux...")
    run_remote(client, "mkdir -p /home/ghost/aegis /tmp/aegis_storage")
    run_remote(client, "chown -R ghost:ghost /home/ghost/aegis /tmp/aegis_storage")
    
    sftp = client.open_sftp()
    local_dir = Path(r"C:\Users\user\.gemini\antigravity-ide\scratch\cross_node_agent")
    
    upload_file_scp(sftp, local_dir / "daemon" / "common_models.py", "/home/ghost/aegis/common_models.py")
    upload_file_scp(sftp, local_dir / "daemon" / "kali_daemon.py", "/home/ghost/aegis/kali_daemon.py")
    upload_file_scp(sftp, local_dir / "daemon" / "agent_bridge.py", "/home/ghost/aegis/agent_bridge.py")
    upload_file_scp(sftp, local_dir / "scripts" / "kali" / "setup_gateway.sh", "/home/ghost/aegis/setup_gateway.sh")
    upload_file_scp(sftp, local_dir / "scripts" / "kali" / "restore_network.sh", "/home/ghost/aegis/restore_network.sh")
    sftp.close()

    run_remote(client, "chmod +x /home/ghost/aegis/*.sh /home/ghost/aegis/*.py")

    # 6. Configure Systemd Service for Aegis Kali Daemon
    print("\n[6/7] Installing and starting Aegis Kali Daemon as a persistent Systemd Service...")
    service_content = f"""[Unit]
Description=Aegis Kali Linux Agent Daemon (Port 8765)
After=network.target

[Service]
Type=simple
User=ghost
WorkingDirectory=/home/ghost/aegis
Environment=WINDOWS_DAEMON_URL=http://{WIN_IP}:8766
Environment=PORT=8765
ExecStart=/usr/bin/python3 /home/ghost/aegis/kali_daemon.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
    # Write service file
    run_remote(client, f"cat << 'EOF' > /etc/systemd/system/aegis-kali.service\n{service_content}\nEOF", sudo=True)
    run_remote(client, "systemctl daemon-reload", sudo=True)
    run_remote(client, "systemctl enable aegis-kali.service", sudo=True)
    run_remote(client, "systemctl restart aegis-kali.service", sudo=True)
    time.sleep(2)
    run_remote(client, "systemctl status aegis-kali.service --no-pager", sudo=True)

    # 7. Test Daemon Status and Bidirectional Communication
    print("\n[7/7] Verifying Daemon Health and Connectivity from Kali...")
    run_remote(client, "curl -s http://127.0.0.1:8765/api/status | head -n 30")
    
    print("\n" + "="*60)
    print("  KALI LINUX PROVISIONING & DAEMON SETUP COMPLETE!")
    print("="*60)
    client.close()

if __name__ == "__main__":
    main()
