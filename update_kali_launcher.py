import paramiko

def update_kali_launcher():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("192.168.137.177", port=22, username="ghost", password="9233", timeout=5)

    script = """#!/bin/bash
export DISPLAY=:0
pkill -9 deskflow-core barrierc 2>/dev/null || true
sleep 1
echo "[*] Connecting Deskflow / Barrier KVM Client to Windows (192.168.137.1:24800)..."
nohup /usr/bin/deskflow-core client 192.168.137.1:24800 > /tmp/deskflow.log 2>&1 &
echo "[+] Deskflow client started in background."
"""
    client.exec_command(f"cat << 'EOF' > /home/ghost/aegis/start_barrier.sh\n{script}\nEOF")
    client.exec_command("chmod +x /home/ghost/aegis/start_barrier.sh")
    
    # Launch it now
    client.exec_command("bash /home/ghost/aegis/start_barrier.sh")
    client.close()

if __name__ == "__main__":
    update_kali_launcher()
