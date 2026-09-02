import os
import subprocess
import time
from pathlib import Path
import paramiko

BASE_DIR = Path(__file__).parent
WIN_PORTABLE_DIR = BASE_DIR / "bin" / "deskflow" / "deskflow-1.26.0-win-x64-portable"
LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", "C:/Users/user/AppData/Local"))

fp = "1E558F477C526DFCAE658D6235699554327D9E9450B1FC1B13051A0414F8309E"
sha1 = "339D77FAB49C5DDD5FD613660B2C955A20F5845F"

v2_content = f"""v2:sha256:{fp.lower()}
v2:sha256:{fp.upper()}
v2:sha1:{sha1.lower()}
v2:sha1:{sha1.upper()}
{fp}
{fp.lower()}
"""

def deploy_trust():
    print("[1/3] Deploying trusted fingerprints on Windows...")
    win_paths = [
        WIN_PORTABLE_DIR / "settings" / "tls" / "trusted-clients",
        WIN_PORTABLE_DIR / "settings" / "tls" / "trusted-servers",
        WIN_PORTABLE_DIR / "settings" / "SSL" / "Fingerprints" / "TrustedClients.txt",
        WIN_PORTABLE_DIR / "settings" / "SSL" / "Fingerprints" / "TrustedServers.txt",
        LOCALAPPDATA / "Deskflow" / "tls" / "trusted-clients",
        LOCALAPPDATA / "Deskflow" / "tls" / "trusted-servers",
        LOCALAPPDATA / "Deskflow" / "SSL" / "Fingerprints" / "TrustedClients.txt",
        LOCALAPPDATA / "Deskflow" / "SSL" / "Fingerprints" / "TrustedServers.txt",
    ]
    for p in win_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(v2_content, encoding="utf-8")
        print(f"  -> Wrote {p}")

    print("\n[2/3] Deploying trusted fingerprints on Kali Linux...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("192.168.137.177", port=22, username="ghost", password="9233", timeout=5)

    kali_paths = [
        "/home/ghost/.config/Deskflow/tls/trusted-clients",
        "/home/ghost/.config/Deskflow/tls/trusted-servers",
        "/home/ghost/.config/Deskflow/SSL/Fingerprints/TrustedClients.txt",
        "/home/ghost/.config/Deskflow/SSL/Fingerprints/TrustedServers.txt",
        "/home/ghost/.local/share/Deskflow/tls/trusted-clients",
        "/home/ghost/.local/share/Deskflow/tls/trusted-servers",
        "/home/ghost/.local/share/Deskflow/SSL/Fingerprints/TrustedClients.txt",
        "/home/ghost/.local/share/Deskflow/SSL/Fingerprints/TrustedServers.txt",
    ]
    for kp in kali_paths:
        client.exec_command(f"mkdir -p $(dirname {kp}); cat << 'EOF' > {kp}\n{v2_content}\nEOF")
        client.exec_command(f"chmod 600 {kp}")

    print("  -> Kali trust files deployed successfully.")
    client.close()

if __name__ == "__main__":
    deploy_trust()
