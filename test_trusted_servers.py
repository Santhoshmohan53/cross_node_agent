import paramiko
import time

def test_trusted_servers_file():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('192.168.137.177', port=22, username='ghost', password='9233', timeout=5)

    fp = "1E558F477C526DFCAE658D6235699554327D9E9450B1FC1B13051A0414F8309E"
    
    # Remove file if exists and create directory
    client.exec_command("rm -rf /home/ghost/.config/Deskflow/tls/trusted-servers")
    client.exec_command("mkdir -p /home/ghost/.config/Deskflow/tls/trusted-servers")
    
    # Create fingerprint file inside trusted-servers directory
    client.exec_command(f"touch /home/ghost/.config/Deskflow/tls/trusted-servers/{fp}")
    client.exec_command(f"touch /home/ghost/.config/Deskflow/tls/trusted-servers/{fp.lower()}")
    client.exec_command(f"echo '{fp}' > /home/ghost/.config/Deskflow/tls/trusted-servers/server.txt")
    client.exec_command(f"echo '{fp}' > /home/ghost/.config/Deskflow/tls/trusted-servers/192.168.137.1")
    
    client.exec_command("pkill -9 deskflow-core 2>/dev/null || true")
    time.sleep(1)

    print("[*] Launching deskflow-core client with /home/ghost/.config/Deskflow/tls/trusted-servers file...")
    client.exec_command("export DISPLAY=:0; timeout 4 /usr/bin/deskflow-core client --new-instance 192.168.137.1:24800 > /tmp/deskflow.log 2>&1")
    time.sleep(3)

    stdin, stdout, stderr = client.exec_command("cat /tmp/deskflow.log; echo '--- TCP Link ---'; ss -tan | grep 24800")
    print(stdout.read().decode('utf-8'))

    client.close()

if __name__ == "__main__":
    test_trusted_servers_file()
