import paramiko
import subprocess

def clean_deskflow_and_check_network():
    # 1. Clean Windows Deskflow
    print("[1/2] Stopping Deskflow on Windows...")
    subprocess.run(["taskkill", "/F", "/IM", "deskflow-core.exe"], capture_output=True)
    subprocess.run(["taskkill", "/F", "/IM", "deskflow.exe"], capture_output=True)

    # 2. Clean Kali Deskflow and inspect Kali network
    print("[2/2] Connecting to Kali Linux...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('192.168.137.177', port=22, username='ghost', password='9233', timeout=5)

    print("--- Stopping and removing Deskflow on Kali ---")
    client.exec_command("echo 9233 | sudo -S pkill -9 deskflow-core deskflow barrierc 2>/dev/null || true")
    client.exec_command("rm -f /home/ghost/Desktop/Barrier_KVM.desktop /home/ghost/.config/autostart/deskflow.desktop /home/ghost/aegis/start_barrier.sh")
    client.exec_command("rm -rf /home/ghost/.config/Deskflow /home/ghost/.local/share/Deskflow /tmp/deskflow*")
    client.exec_command("echo 9233 | sudo -S apt remove -y deskflow >/dev/null 2>&1")
    print("[+] Deskflow removed from Kali Linux.")

    print("\n--- Kali Network Interfaces (ip -br a) ---")
    stdin, stdout, stderr = client.exec_command("ip -br a")
    print(stdout.read().decode('utf-8'))

    print("--- Kali Wireless Interfaces (iw dev) ---")
    stdin, stdout, stderr = client.exec_command("iw dev")
    out = stdout.read().decode('utf-8')
    print(out if out.strip() else "No wireless interface currently detected on Kali.")

    print("--- Kali USB Devices (lsusb) ---")
    stdin, stdout, stderr = client.exec_command("lsusb")
    print(stdout.read().decode('utf-8'))

    client.close()

if __name__ == "__main__":
    clean_deskflow_and_check_network()
