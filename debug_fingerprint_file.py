import paramiko
import time

def debug_fingerprint_file():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('192.168.137.177', port=22, username='ghost', password='9233', timeout=5)

    # Let's check what TrustedServers files exist across the whole /home/ghost directory
    stdin, stdout, stderr = client.exec_command("find /home/ghost -name 'TrustedServers.txt' -o -name '*Fingerprint*' -o -name '*.pem'")
    print("All SSL files on Kali:")
    print(stdout.read().decode('utf-8'))

    # Set log level to DEBUG2 in Deskflow.conf
    cfg = """[client]
remoteHost=192.168.137.1

[core]
computerName=ghost
coreMode=1
lastVersion=1.26.0.0
logLevel=DEBUG2

[gui]
enableUpdateCheck=false
logExpanded=true
startCoreWithGui=true
"""
    client.exec_command(f"cat << 'EOF' > /home/ghost/.config/Deskflow/Deskflow.conf\n{cfg}\nEOF")
    client.exec_command("pkill -9 deskflow-core 2>/dev/null || true")
    time.sleep(1)

    client.exec_command("export DISPLAY=:0; timeout 4 /usr/bin/deskflow-core client --new-instance 192.168.137.1:24800 > /tmp/deskflow.log 2>&1")
    time.sleep(3)

    stdin, stdout, stderr = client.exec_command("cat /tmp/deskflow.log")
    print("\n--- Deskflow DEBUG2 Log ---")
    print(stdout.read().decode('utf-8'))

    client.close()

if __name__ == "__main__":
    debug_fingerprint_file()
