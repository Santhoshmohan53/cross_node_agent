import paramiko
import subprocess
import time

def check_status():
    print("="*60)
    print("  VERIFYING BARRIER / DESKFLOW CONNECTION")
    print("="*60)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("192.168.137.177", port=22, username="ghost", password="9233", timeout=5)

    client.exec_command("pkill -9 deskflow-core barrierc 2>/dev/null || true")
    time.sleep(1)
    client.exec_command("export DISPLAY=:0; nohup /usr/bin/deskflow-core client 192.168.137.1:24800 > /tmp/deskflow.log 2>&1 &")
    time.sleep(3)

    stdin, stdout, stderr = client.exec_command("tail -n 15 /tmp/deskflow.log")
    print("[Kali Client Log]:")
    print(stdout.read().decode('utf-8'))

    stdin, stdout, stderr = client.exec_command("ss -tan | grep 24800")
    print("[Kali Socket Status]:")
    print(stdout.read().decode('utf-8'))

    client.close()

    res = subprocess.run(["cmd", "/c", "netstat -ano | findstr 24800"], capture_output=True, text=True)
    print("[Windows Socket Status]:")
    print(res.stdout)

if __name__ == "__main__":
    check_status()
