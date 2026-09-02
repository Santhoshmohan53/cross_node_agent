import os
import sys
import datetime
import hashlib
import subprocess
import time
from pathlib import Path
import paramiko

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

BASE_DIR = Path(__file__).parent
WIN_PORTABLE_DIR = BASE_DIR / "bin" / "deskflow" / "deskflow-1.26.0-win-x64-portable"
LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", "C:/Users/user/AppData/Local"))

def generate_cert():
    print("[1/5] Generating RSA 2048 TLS Certificate for Deskflow...")
    # Generate private key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Generate self-signed cert
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "Deskflow"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Deskflow"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650)
    ).sign(key, hashes.SHA256())

    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    combined_pem = cert_pem + key_pem

    # Calculate SHA1 and SHA256 fingerprints
    sha1_fp = hashlib.sha1(cert.public_bytes(serialization.Encoding.DER)).hexdigest().upper()
    sha1_formatted = ":".join(sha1_fp[i:i+2] for i in range(0, len(sha1_fp), 2))
    
    sha256_fp = hashlib.sha256(cert.public_bytes(serialization.Encoding.DER)).hexdigest().upper()
    sha256_formatted = ":".join(sha256_fp[i:i+2] for i in range(0, len(sha256_fp), 2))

    print(f"  -> SHA1 Fingerprint  : {sha1_formatted}")
    print(f"  -> SHA256 Fingerprint: {sha256_formatted}")
    
    return combined_pem, sha1_formatted, sha256_formatted

def deploy_windows_cert(combined_pem):
    print("\n[2/5] Deploying TLS Certificate on Windows...")
    paths = [
        WIN_PORTABLE_DIR / "settings" / "tls" / "deskflow.pem",
        WIN_PORTABLE_DIR / "settings" / "SSL" / "Deskflow.pem",
        LOCALAPPDATA / "Deskflow" / "SSL" / "Deskflow.pem",
        LOCALAPPDATA / "Deskflow" / "tls" / "deskflow.pem"
    ]
    for p in paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(combined_pem)
        print(f"  -> Saved {p}")

def deploy_kali_cert(combined_pem, sha1_fp, sha256_fp):
    print("\n[3/5] Deploying TLS Certificate & Trusted Fingerprints to Kali Linux...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("192.168.137.177", port=22, username="ghost", password="9233", timeout=10)

    sftp = client.open_sftp()
    
    # Ensure dirs
    dirs = [
        "/home/ghost/.config/Deskflow/SSL/Fingerprints",
        "/home/ghost/.config/Deskflow/tls",
        "/home/ghost/.local/share/Deskflow/SSL/Fingerprints",
        "/home/ghost/.local/share/Deskflow/tls"
    ]
    for d in dirs:
        client.exec_command(f"mkdir -p {d}")

    # Write pem file
    local_temp_pem = BASE_DIR / "deskflow_temp.pem"
    local_temp_pem.write_bytes(combined_pem)
    
    sftp.put(str(local_temp_pem), "/home/ghost/.config/Deskflow/tls/deskflow.pem")
    sftp.put(str(local_temp_pem), "/home/ghost/.local/share/Deskflow/SSL/Deskflow.pem")
    local_temp_pem.unlink(missing_ok=True)

    # Write TrustedServers.txt
    fingerprint_text = f"{sha256_formatted}\n{sha1_formatted}\n{sha256_fp.lower()}\n{sha1_fp.lower()}\n"
    
    trusted_paths = [
        "/home/ghost/.config/Deskflow/SSL/Fingerprints/TrustedServers.txt",
        "/home/ghost/.local/share/Deskflow/SSL/Fingerprints/TrustedServers.txt"
    ]
    for tp in trusted_paths:
        client.exec_command(f"cat << 'EOF' > {tp}\n{fingerprint_text}\nEOF")

    client.exec_command("chmod -R 700 /home/ghost/.config/Deskflow /home/ghost/.local/share/Deskflow")
    sftp.close()
    client.close()
    print("  -> Certificate & Fingerprints installed on Kali successfully.")

def restart_services():
    print("\n[4/5] Restarting Windows Deskflow Server...")
    # Kill any existing server
    subprocess.run(["taskkill", "/F", "/IM", "deskflow-core.exe"], capture_output=True)
    time.sleep(1)

    bin_path = WIN_PORTABLE_DIR / "deskflow-core.exe"
    server_proc = subprocess.Popen([str(bin_path), "server"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(2)
    print(f"  -> Windows Server running (PID: {server_proc.pid})")

    print("\n[5/5] Restarting Kali Linux Deskflow Client...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("192.168.137.177", port=22, username="ghost", password="9233", timeout=10)

    client.exec_command("pkill -9 deskflow-core barrierc 2>/dev/null || true")
    time.sleep(1)

    client.exec_command("export DISPLAY=:0; nohup /usr/bin/deskflow-core client --new-instance 192.168.137.1:24800 > /tmp/deskflow.log 2>&1 &")
    time.sleep(3)

    stdin, stdout, stderr = client.exec_command("cat /tmp/deskflow.log; echo '--- TCP Link ---'; ss -tan | grep 24800")
    log_out = stdout.read().decode('utf-8')
    print("[Kali Client Log]:\n" + log_out)

    client.close()

if __name__ == "__main__":
    combined_pem, sha1_formatted, sha256_formatted = generate_cert()
    deploy_windows_cert(combined_pem)
    deploy_kali_cert(combined_pem, sha1_formatted, sha256_formatted)
    restart_services()
