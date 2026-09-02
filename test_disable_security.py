import paramiko
import time

def test_disable_group_security():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('192.168.137.177', port=22, username='ghost', password='9233', timeout=5)

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

[security]
groupSecurity=false
enabled=false
tls=false

[internalConfig]
groupSecurity=false
clipboardSharing=true
defaultLockToScreenState=false
disableLockToScreen=false
hasHeartbeat=true
heartbeat=5000
hotkeys\\size=0
protocol=1
relativeMouseMoves=false
win32KeepForeground=false
"""

    client.exec_command(f"cat << 'EOF' > /home/ghost/.config/Deskflow/Deskflow.conf\n{cfg}\nEOF")
    client.exec_command("pkill -9 deskflow-core 2>/dev/null || true")
    time.sleep(1)

    print("[*] Launching deskflow-core client...")
    client.exec_command("export DISPLAY=:0; timeout 4 /usr/bin/deskflow-core client --new-instance 192.168.137.1:24800 > /tmp/deskflow.log 2>&1")
    time.sleep(3)

    stdin, stdout, stderr = client.exec_command("cat /tmp/deskflow.log")
    print(stdout.read().decode('utf-8'))

    client.close()

if __name__ == "__main__":
    test_disable_group_security()
