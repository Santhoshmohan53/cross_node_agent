import paramiko
import time

def update_fingerprints():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('192.168.137.177', port=22, username='ghost', password='9233', timeout=5)

    fps = """1E558F477C526DFCAE658D6235699554327D9E9450B1FC1B13051A0414F8309E
1e558f477c526dfcae658d6235699554327d9e9450b1fc1b13051a0414f8309e
v2:1E558F477C526DFCAE658D6235699554327D9E9450B1FC1B13051A0414F8309E
v2:1e558f477c526dfcae658d6235699554327d9e9450b1fc1b13051a0414f8309e
1E:55:8F:47:7C:52:6D:FC:AE:65:8D:62:35:69:95:54:32:7D:9E:94:50:B1:FC:1B:13:05:1A:04:14:F8:30:9E
33:9D:77:FA:B4:9C:5D:DD:5F:D6:13:66:0B:2C:95:5A:20:F5:84:5F
339D77FAB49C5DDD5FD613660B2C955A20F5845F
"""

    paths = [
        "/home/ghost/.config/Deskflow/SSL/Fingerprints/TrustedServers.txt",
        "/home/ghost/.local/share/Deskflow/SSL/Fingerprints/TrustedServers.txt"
    ]
    for path in paths:
        client.exec_command(f"cat << 'EOF' > {path}\n{fps}\nEOF")

    client.exec_command("pkill -9 deskflow-core barrierc 2>/dev/null || true")
    time.sleep(1)

    print("[*] Launching Deskflow client on Kali...")
    client.exec_command("export DISPLAY=:0; nohup /usr/bin/deskflow-core client --new-instance 192.168.137.1:24800 > /tmp/deskflow.log 2>&1 &")
    time.sleep(3)

    stdin, stdout, stderr = client.exec_command("cat /tmp/deskflow.log; echo '--- TCP Link ---'; ss -tan | grep 24800")
    print(stdout.read().decode('utf-8'))

    client.close()

if __name__ == "__main__":
    update_fingerprints()
