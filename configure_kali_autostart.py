import paramiko

def configure_kali_autostart():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("192.168.137.177", port=22, username="ghost", password="9233", timeout=10)

    # 1. Update start_barrier.sh
    barrier_script = """#!/bin/bash
export DISPLAY=:0
pkill -9 deskflow-core barrierc 2>/dev/null || true
sleep 1
echo "[*] Connecting Deskflow / Barrier Client to Windows (192.168.137.1:24800)..."
deskflow-core client 192.168.137.1:24800
"""
    client.exec_command(f"cat << 'EOF' > /home/ghost/aegis/start_barrier.sh\n{barrier_script}\nEOF")
    client.exec_command("chmod +x /home/ghost/aegis/start_barrier.sh")

    # 2. Add Autostart entry on Kali desktop
    autostart_entry = """[Desktop Entry]
Type=Application
Exec=/home/ghost/aegis/start_barrier.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Deskflow Barrier KVM Client
Comment=Auto-connect mouse and keyboard to Windows
"""
    client.exec_command("mkdir -p /home/ghost/.config/autostart")
    client.exec_command(f"cat << 'EOF' > /home/ghost/.config/autostart/deskflow.desktop\n{autostart_entry}\nEOF")

    # 3. Create desktop shortcuts with proper permissions
    client.exec_command("chmod +x /home/ghost/Desktop/*.desktop /home/ghost/.config/autostart/*.desktop 2>/dev/null || true")

    print("[+] Configured start_barrier.sh, autostart, and desktop shortcuts on Kali Linux.")
    client.close()

if __name__ == "__main__":
    configure_kali_autostart()
