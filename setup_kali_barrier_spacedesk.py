#!/usr/bin/env python3
"""
Sets up Barrier KVM Client and Spacedesk Extended Display Launchers on Kali Linux.
"""

import paramiko
import time

KALI_IP = "192.168.137.177"
KALI_USER = "ghost"
KALI_PASS = "9233"
WIN_IP = "192.168.137.1"

def run_remote(client, cmd, sudo=False):
    if sudo:
        exec_cmd = f"echo '{KALI_PASS}' | sudo -S bash -c \"{cmd}\""
    else:
        exec_cmd = cmd

    print(f"\n[EXEC ({'sudo' if sudo else 'user'})] {cmd}")
    stdin, stdout, stderr = client.exec_command(exec_cmd, get_pty=True)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print(out.strip())
    if err and not "password for ghost" in err:
        print(f"[STDERR]: {err.strip()}")
    return stdout.channel.recv_exit_status(), out

def main():
    print("="*60)
    print("  KALI LINUX BARRIER & SPACEDESK CLIENT SETUP")
    print("="*60)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(KALI_IP, port=22, username=KALI_USER, password=KALI_PASS, timeout=15)
    print("[+] Connected to Kali Linux over SSH.\n")
    
    # 1. Install Barrier and Chromium on Kali
    print("[1/4] Installing Barrier KVM and Chromium Browser on Kali...")
    run_remote(client, "DEBIAN_FRONTEND=noninteractive apt-get install -y barrier chromium x11-xserver-utils xdotool", sudo=True)

    # 2. Configure Barrier Client Service & Scripts
    print("\n[2/4] Configuring Barrier Client on Kali...")
    run_remote(client, "mkdir -p /home/ghost/Desktop /home/ghost/.config/autostart")

    barrier_script = f"""#!/bin/bash
# Barrier Client Launcher for Kali Linux
# Connects to Windows Barrier Server on {WIN_IP}
pkill -9 barrierc 2>/dev/null || true
sleep 1
barrierc -f --no-tray --restart --name ghost {WIN_IP}:24800
"""
    run_remote(client, f"cat << 'EOF' > /home/ghost/aegis/start_barrier.sh\n{barrier_script}\nEOF")
    run_remote(client, "chmod +x /home/ghost/aegis/start_barrier.sh")

    barrier_desktop = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Barrier KVM (Windows Mouse & Keyboard)
Comment=Connect mouse and keyboard to Windows PC
Exec=/home/ghost/aegis/start_barrier.sh
Icon=input-mouse
Terminal=true
Categories=Utility;
"""
    run_remote(client, f"cat << 'EOF' > /home/ghost/Desktop/Barrier_KVM.desktop\n{barrier_desktop}\nEOF")
    run_remote(client, "chmod +x /home/ghost/Desktop/Barrier_KVM.desktop")

    # 3. Configure Spacedesk Extended Display Launcher
    print("\n[3/4] Creating Spacedesk Extended Display Launcher on Kali...")
    spacedesk_script = f"""#!/bin/bash
# Spacedesk Extended Display Kiosk Launcher for Kali Linux
# Connects to Windows Spacedesk Virtual Display on {WIN_IP}:17882
export DISPLAY=:0
echo "[*] Launching Spacedesk Extended Display from Windows ({WIN_IP})..."
echo "[*] Press F11 or Alt+Tab or Ctrl+Alt+Right to switch back to Kali Desktop."

chromium --app="http://{WIN_IP}:17882" --start-fullscreen --no-default-browser-check --no-first-run 2>/dev/null || \
firefox -kiosk "http://{WIN_IP}:17882" 2>/dev/null
"""
    run_remote(client, f"cat << 'EOF' > /home/ghost/aegis/launch_spacedesk.sh\n{spacedesk_script}\nEOF")
    run_remote(client, "chmod +x /home/ghost/aegis/launch_spacedesk.sh")

    spacedesk_desktop = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Spacedesk Extended Display (Windows Screen)
Comment=Use this monitor as Windows Second Screen
Exec=/home/ghost/aegis/launch_spacedesk.sh
Icon=video-display
Terminal=false
Categories=Utility;
"""
    run_remote(client, f"cat << 'EOF' > /home/ghost/Desktop/Spacedesk_Extended_Display.desktop\n{spacedesk_desktop}\nEOF")
    run_remote(client, "chmod +x /home/ghost/Desktop/Spacedesk_Extended_Display.desktop")

    # 4. Create Workspace Switch Helper
    print("\n[4/4] Creating Quick Display Switcher on Kali...")
    toggle_script = """#!/bin/bash
# Switches between Workspace 1 (Extended Windows Screen) and Workspace 2 (Kali Linux Desktop)
CURRENT_WS=$(wmctrl -d | grep '*' | cut -d ' ' -f 1)
if [ "$CURRENT_WS" = "0" ]; then
    wmctrl -s 1
else
    wmctrl -s 0
fi
"""
    run_remote(client, f"cat << 'EOF' > /home/ghost/aegis/toggle_screen.sh\n{toggle_script}\nEOF")
    run_remote(client, "chmod +x /home/ghost/aegis/toggle_screen.sh")

    print("\n" + "="*60)
    print("  KALI LINUX BARRIER & SPACEDESK SETUP COMPLETE!")
    print("="*60)
    client.close()

if __name__ == "__main__":
    main()
