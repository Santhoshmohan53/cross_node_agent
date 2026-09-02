import paramiko
import time

def launch_kali_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("192.168.137.177", port=22, username="ghost", password="9233", timeout=5)

    print("[*] Starting Deskflow / Barrier Client on Kali (connecting to 192.168.137.1:24800)...")
    cmd = "export DISPLAY=:0; nohup /usr/bin/deskflow-core client 192.168.137.1:24800 > /tmp/deskflow.log 2>&1 &"
    client.exec_command(cmd)
    time.sleep(2)

    stdin, stdout, stderr = client.exec_command("cat /tmp/deskflow.log; echo '--- TCP Link ---'; ss -tan | grep 24800")
    print(stdout.read().decode('utf-8'))
    client.close()

if __name__ == "__main__":
    launch_kali_client()
