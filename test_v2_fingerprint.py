import paramiko
import time
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent
WIN_PORTABLE_DIR = BASE_DIR / "bin" / "deskflow" / "deskflow-1.26.0-win-x64-portable"

def restart_and_test():
    print("="*60)
    print("  RESTARTING AND TESTING BARRIER / DESKFLOW KVM")
    print("="*60)

    # 1. Restart Windows Server
    print("[1/3] Restarting Windows Deskflow / Barrier Server...")
    subprocess.run(["taskkill", "/F", "/IM", "deskflow-core.exe"], capture_output=True)
    time.sleep(1)

    bin_path = WIN_PORTABLE_DIR / "deskflow-core.exe"
    server_proc = subprocess.Popen([str(bin_path), "server"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(2)
    print(f"[+] Windows Server running (PID: {server_proc.pid}) listening on 0.0.0.0:24800")

    # 2. Configure exact v2:sha256 fingerprint on Kali
    print("[2/3] Configuring trusted-servers on Kali Linux...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("192.168.137.177", port=22, username="ghost", password="9233", timeout=5)

    fp = "1E558F477C526DFCAE658D6235699554327D9E9450B1FC1B13051A0414F8309E"
    sha1 = "339D77FAB49C5DDD5FD613660B2C955A20F5845F"
    
    # Exact v2 format
    v2_content = f"""v2:sha256:{fp.lower()}
v2:sha256:{fp.upper()}
v2:sha1:{sha1.lower()}
v2:sha1:{sha1.upper()}
"""

    client.exec_command("rm -rf /home/ghost/.config/Deskflow/tls/trusted-servers")
    client.exec_command(f"cat << 'EOF' > /home/ghost/.config/Deskflow/tls/trusted-servers\n{v2_content}\nEOF")
    client.exec_command("chmod 600 /home/ghost/.config/Deskflow/tls/trusted-servers")

    # Also copy to .local/share paths
    client.exec_command("mkdir -p /home/ghost/.local/share/Deskflow/tls")
    client.exec_command(f"cat << 'EOF' > /home/ghost/.local/share/Deskflow/tls/trusted-servers\n{v2_content}\nEOF")

    # 3. Start client on Kali
    print("[3/3] Launching Deskflow client on Kali Linux...")
    client.exec_command("pkill -9 deskflow-core barrierc 2>/dev/null || true")
    time.sleep(1)

    client.exec_command("export DISPLAY=:0; timeout 6 /usr/bin/deskflow-core client --new-instance 192.168.137.1:24800 > /tmp/deskflow.log 2>&1 &")
    time.sleep(4)

    stdin, stdout, stderr = client.exec_command("cat /tmp/deskflow.log; echo '--- TCP Link ---'; ss -tan | grep 24800")
    log_out = stdout.read().decode('utf-8')
    print("[Kali Client Log]:\n" + log_out)

    client.close()

if __name__ == "__main__":
    restart_and_test()
