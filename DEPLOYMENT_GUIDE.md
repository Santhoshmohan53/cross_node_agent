# AEGIS: Dual-Node Kali Linux & Windows Agent Correlation System
## Complete Deployment & Configuration Manual

This document explains step-by-step how to set up the network transition (Kali as Internet Gateway), deploy the daemons on both Kali Linux and Windows, and launch the Unified Command Center.

---

### Phase 1: Kali Linux Gateway & Wi-Fi Setup

1. **Connect Wi-Fi on Kali Linux**:
   - Plug your Wi-Fi router / adapter into the Kali Mini PC.
   - Connect to your wireless network using either GUI or `nmcli dev wifi connect <SSID> password <PASS>`.
   - Verify Wi-Fi is online: `ping -c 2 8.8.8.8`.

2. **Run Gateway & Ethernet Sharing Configurator**:
   - Copy the `cross_node_agent` folder to your Kali Mini PC (e.g. via USB or SCP).
   - In terminal on Kali, run:
     ```bash
     cd cross_node_agent/scripts/kali
     chmod +x setup_gateway.sh restore_network.sh
     sudo ./setup_gateway.sh
     ```
   - This script:
     - Enables IPv4 kernel forwarding (`net.ipv4.ip_forward=1`).
     - Sets the Ethernet connection to `ipv4.method shared` (NetworkManager handles DHCP/DNS & NAT Masquerading automatically).
     - Assigns Kali Ethernet IP to `10.42.0.1`.
     - Confirms your Wi-Fi adapter is monitor mode ready.

3. **Launch the Kali Agent Daemon**:
   ```bash
   cd cross_node_agent
   pip3 install -r requirements.txt
   python3 daemon/kali_daemon.py
   ```
   *Daemon starts listening on `http://0.0.0.0:8765`.*

---

### Phase 2: Windows PC LAN Configuration

1. **Ensure Ethernet is Connected**:
   - Plug the Ethernet LAN cable directly between the Kali Mini PC and your Windows PC.
2. **Run Windows DHCP Configurator**:
   - Open PowerShell as Administrator and run:
     ```powershell
     cd C:\Users\user\.gemini\antigravity-ide\scratch\cross_node_agent\scripts\windows
     .\configure_lan_dhcp.ps1
     ```
   - This script ensures DHCP is active on your Ethernet NIC, renews the IP, verifies reachability to the Kali gateway (`10.42.0.1`), and confirms DNS resolution.

3. **Launch the Windows Agent Daemon**:
   - In PowerShell or CMD:
     ```powershell
     cd C:\Users\user\.gemini\antigravity-ide\scratch\cross_node_agent
     python daemon/windows_daemon.py
     ```
   *Daemon starts listening on `http://127.0.0.1:8766`.*

---

### Phase 3: Launch Unified Command Center (Hub & Web UI)

1. **Start the Hub Server on Windows (or Kali)**:
   ```powershell
   cd C:\Users\user\.gemini\antigravity-ide\scratch\cross_node_agent
   python hub_server.py
   ```
2. **Open the Dashboard in Any Web Browser**:
   - On Windows: Navigate to `http://localhost:8080`
   - On Kali (connected to monitor): Open browser to `http://10.42.0.1:8080` or `http://localhost:8080` if hub is run there.

---

### Features Available in the Unified Dashboard

- **Live Topology & Health**: Real-time visual representation of Kali Gateway, Wi-Fi link, Monitor mode toggle, and Windows client link with CPU/RAM metrics.
- **Dual-Split Live Terminal**: Side-by-side execution on Kali (Bash) and Windows (PowerShell) with real-time output.
- **Cross-Node Workflows**: Run automated multi-stage playbooks (e.g. Nmap scan on Kali -> Windows validates reachability).
- **AI Agent Copilot**: Natural language dispatcher that splits high-level objectives into correlated Kali + Windows tasks.
- **File Sync Hub**: Transfer files, packet captures, and logs between machines with one click.
