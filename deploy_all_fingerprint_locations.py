import paramiko
import time

def deploy_all_fingerprint_locations():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('192.168.137.177', port=22, username='ghost', password='9233', timeout=5)

    raw_fp = "1E558F477C526DFCAE658D6235699554327D9E9450B1FC1B13051A0414F8309E"
    colon_fp = "1E:55:8F:47:7C:52:6D:FC:AE:65:8D:62:35:69:95:54:32:7D:9E:94:50:B1:FC:1B:13:05:1A:04:14:F8:30:9E"
    sha1_fp = "33:9D:77:FA:B4:9C:5D:DD:5F:D6:13:66:0B:2C:95:5A:20:F5:84:5F"
    sha1_raw = "339D77FAB49C5DDD5FD613660B2C955A20F5845F"

    content = f"""{raw_fp}
{raw_fp.lower()}
{colon_fp}
{colon_fp.lower()}
v2:{raw_fp}
v2:{raw_fp.lower()}
{sha1_fp}
{sha1_raw}
"""

    paths = [
        "/home/ghost/.config/Deskflow/SSL/Fingerprints/TrustedServers.txt",
        "/home/ghost/.config/Deskflow/Fingerprints/TrustedServers.txt",
        "/home/ghost/.config/Deskflow/tls/TrustedServers.txt",
        "/home/ghost/.config/Deskflow/tls/fingerprints/TrustedServers.txt",
        "/home/ghost/.local/share/Deskflow/SSL/Fingerprints/TrustedServers.txt",
        "/home/ghost/.local/share/Deskflow/Fingerprints/TrustedServers.txt",
        "/home/ghost/.local/share/Deskflow/tls/TrustedServers.txt",
        "/home/ghost/.local/share/Deskflow/tls/fingerprints/TrustedServers.txt",
        "/home/ghost/.local/share/deskflow/SSL/Fingerprints/TrustedServers.txt",
        "/home/ghost/.local/share/deskflow/Fingerprints/TrustedServers.txt",
        "/home/ghost/.local/share/barrier/SSL/Fingerprints/TrustedServers.txt",
        "/home/ghost/.local/share/input-leap/SSL/Fingerprints/TrustedServers.txt",
        "/home/ghost/.barrier/SSL/Fingerprints/TrustedServers.txt",
        "/home/ghost/.deskflow/SSL/Fingerprints/TrustedServers.txt",
        "/home/ghost/.deskflow/Fingerprints/TrustedServers.txt",
        "/home/ghost/.deskflow/tls/TrustedServers.txt",
        "/home/ghost/.deskflow/tls/fingerprints/TrustedServers.txt",
        "/home/ghost/.deskflow/tls/deskflow.pem",
        "/home/ghost/.config/deskflow/SSL/Fingerprints/TrustedServers.txt",
    ]

    for p in paths:
        if p.endswith(".pem"):
            continue
        client.exec_command(f"mkdir -p $(dirname {p}); cat << 'EOF' > {p}\n{content}\nEOF")

    client.exec_command("pkill -9 deskflow-core 2>/dev/null || true")
    time.sleep(1)

    print("[*] Launching deskflow-core client on Kali...")
    client.exec_command("export DISPLAY=:0; timeout 4 /usr/bin/deskflow-core client --new-instance 192.168.137.1:24800 > /tmp/deskflow.log 2>&1")
    time.sleep(3)

    stdin, stdout, stderr = client.exec_command("cat /tmp/deskflow.log")
    print(stdout.read().decode('utf-8'))

    client.close()

if __name__ == "__main__":
    deploy_all_fingerprint_locations()
