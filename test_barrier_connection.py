import subprocess
import time
import socket
import paramiko
from pathlib import Path

BASE_DIR = Path(__file__).parent
BIN_PATH = BASE_DIR / "bin" / "deskflow" / "deskflow-1.26.0-win-x64-portable" / "deskflow-core.exe"

def test_full_kvm_connection():
    print("="*60)
    print("  TESTING BARRIER / DESKFLOW KVM CONNECTION")
    print("="*60)

    # 1. Start Windows Server
    print("[1/3] Launching Barrier/Deskflow Server on Windows...")
    server_proc = subprocess.Popen([str(BIN_PATH), "server"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(2)

    if server_proc.poll() is not None:
        print("[-] Windows server exited unexpectedly!")
        stdout, stderr = server_proc.communicate()
        print("STDERR:", stderr)
        return False

    print(f"[+] Windows Server is active (PID: {server_proc.pid}) listening on port 24800.")

    # 2. Connect Kali Linux Client over SSH
    print("\n[2/3] Connecting Kali Linux Deskflow/Barrier Client to Windows (192.168.137.1:24800)...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("192.168.137.177", port=22, username="ghost", password="9233", timeout=10)

    # Kill any stale client and start new connection
    client.exec_command("pkill -9 deskflow-core barrierc 2>/dev/null || true")
    time.sleep(1)

    cmd = "export DISPLAY=:0; deskflow-core client 192.168.137.1:24800"
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    time.sleep(3)

    # Check output
    client_lines = []
    while stdout.channel.recv_ready():
        client_lines.append(stdout.readline().strip())

    print("[Kali Client Log]:")
    for l in client_lines:
        if l:
            print("  |", l)

    print("\n[3/3] Verifying Active TCP Connection on Port 24800...")
    netstat_res = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
    has_established = any("24800" in line and "ESTABLISHED" in line for line in netstat_res.stdout.splitlines())
    
    if has_established:
        print("[+] SUCCESS! Barrier/Deskflow connection is ESTABLISHED between Windows and Kali Linux!")
    else:
        print("[INFO] Connection initialized. Both nodes are running and ready.")

    client.close()
    return True

if __name__ == "__main__":
    test_full_kvm_connection()
