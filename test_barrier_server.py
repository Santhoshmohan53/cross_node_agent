import subprocess
import socket
import time
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
BIN_PATH = BASE_DIR / "bin" / "deskflow" / "deskflow-1.26.0-win-x64-portable" / "deskflow-core.exe"
CONFIG_PATH = BASE_DIR / "config" / "deskflow_server.conf"

def check_port(ip="192.168.137.1", port=24800, timeout=1.0):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        res = s.connect_ex((ip, port))
        s.close()
        return res == 0
    except Exception:
        return False

def start_server():
    print(f"[*] Starting Barrier/Deskflow Server on 192.168.137.1:24800...")
    cmd = [
        str(BIN_PATH),
        "server"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(2)
    
    if proc.poll() is not None:
        stdout, stderr = proc.communicate()
        print(f"[-] Server failed to start! Exit code: {proc.returncode}")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        return None
    
    print(f"[+] Server started successfully with PID: {proc.pid}")
    is_open = check_port()
    print(f"[+] Port 24800 is {'LISTENING' if is_open else 'NOT LISTENING'}")
    return proc

if __name__ == "__main__":
    p = start_server()
    if p:
        time.sleep(3)
        p.terminate()
