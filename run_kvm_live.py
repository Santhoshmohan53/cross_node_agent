import subprocess
import threading
import time
import paramiko
from pathlib import Path

BASE_DIR = Path(__file__).parent
WIN_BIN = BASE_DIR / "bin" / "deskflow" / "deskflow-1.26.0-win-x64-portable" / "deskflow-core.exe"
KALI_IP = "192.168.137.39"
WIN_IP = "192.168.137.1"

def stream_pipe(pipe, prefix):
    for line in iter(pipe.readline, ''):
        if line:
            print(f"[{prefix}] {line.strip()}")

def run_live():
    print("="*60)
    print("  LIVE BARRIER / DESKFLOW SERVER & CLIENT RESTART")
    print("="*60)

    # 1. Kill any existing instances
    subprocess.run(["taskkill", "/F", "/IM", "deskflow-core.exe"], capture_output=True)
    time.sleep(1)

    # 2. Start Windows Server
    server_proc = subprocess.Popen(
        [str(WIN_BIN), "server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    threading.Thread(target=stream_pipe, args=(server_proc.stdout, "WIN SERVER OUT"), daemon=True).start()
    threading.Thread(target=stream_pipe, args=(server_proc.stderr, "WIN SERVER ERR"), daemon=True).start()
    time.sleep(2)

    # 3. Start Kali Client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(KALI_IP, port=22, username="ghost", password="9233", timeout=5)

    client.exec_command("pkill -9 deskflow-core barrierc 2>/dev/null || true")
    time.sleep(1)

    cmd = f"export DISPLAY=:0; /usr/bin/deskflow-core client {WIN_IP}:24800"
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)

    time.sleep(4)
    lines = []
    while stdout.channel.recv_ready():
        lines.append(stdout.readline().strip())
    
    print("[Kali Client Log]:")
    for l in lines:
        if l:
            print("  |", l)

    client.close()

if __name__ == "__main__":
    run_live()
