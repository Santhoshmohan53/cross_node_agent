import paramiko
import time

def setup_sudo_and_tailscale():
    print("="*60)
    print("  CONFIGURING PASSWORDLESS SUDO & TAILSCALE ON KALI LINUX")
    print("="*60)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("192.168.137.177", port=22, username="ghost", password="9233", timeout=10)

    # 1. Configure Passwordless Sudo for ghost
    print("\n[1/3] Setting up NOPASSWD sudoers rule for user 'ghost'...")
    sudo_rule = "ghost ALL=(ALL:ALL) NOPASSWD: ALL\n"
    client.exec_command(f"echo 9233 | sudo -S bash -c 'echo \"{sudo_rule}\" > /etc/sudoers.d/ghost && chmod 0440 /etc/sudoers.d/ghost'")
    time.sleep(1)

    # Test passwordless sudo
    stdin, stdout, stderr = client.exec_command("sudo whoami")
    whoami_out = stdout.read().decode('utf-8').strip()
    print(f"  -> Sudo test (should be root): {whoami_out}")

    # Set root password to 9233 as well so root login is always accessible
    client.exec_command("sudo bash -c 'echo \"root:9233\" | chpasswd'")
    print("  -> Set root password to 9233 as fallback.")

    # 2. Install and configure Tailscale
    print("\n[2/3] Installing Tailscale on Kali Linux...")
    # Add Tailscale Debian repo or official install script
    install_cmd = """sudo apt-get update -y
sudo apt-get install -y curl gpg
curl -fsSL https://pkgs.tailscale.com/stable/debian/bookworm.noarmor.gpg | sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null
curl -fsSL https://pkgs.tailscale.com/stable/debian/bookworm.tailscale-repo.list | sudo tee /etc/apt/sources.list.d/tailscale.list
sudo apt-get update -y
sudo apt-get install -y tailscale
sudo systemctl enable --now tailscaled
"""
    stdin, stdout, stderr = client.exec_command(install_cmd)
    print("  Installing package...")
    out = stdout.read().decode('utf-8')
    # Print tail of output
    print("\n".join(out.splitlines()[-10:]))

    # 3. Check tailscale status
    print("\n[3/3] Verifying Tailscale status...")
    stdin, stdout, stderr = client.exec_command("tailscale version && sudo systemctl status tailscaled | head -n 5")
    print(stdout.read().decode('utf-8'))

    client.close()

if __name__ == "__main__":
    setup_sudo_and_tailscale()
