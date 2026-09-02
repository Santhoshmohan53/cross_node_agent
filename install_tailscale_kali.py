import paramiko
import time

def install_tailscale():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("192.168.137.177", port=22, username="ghost", password="9233", timeout=10)

    print("[*] Running official Tailscale installer on Kali Linux...")
    cmd = "curl -fsSL https://tailscale.com/install.sh | sudo sh"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    # Stream output
    for line in iter(stdout.readline, ""):
        print("  ", line.strip())

    print("\n[*] Enabling tailscaled service...")
    client.exec_command("sudo systemctl enable --now tailscaled")
    time.sleep(2)

    stdin, stdout, stderr = client.exec_command("tailscale version; sudo systemctl is-active tailscaled")
    print(stdout.read().decode('utf-8'))

    client.close()

if __name__ == "__main__":
    install_tailscale()
