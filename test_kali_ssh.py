import paramiko
import time

def test_ssh(host="192.168.137.177", user="ghost", password="9233"):
    print(f"[*] Attempting SSH connection to {user}@{host}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, port=22, username=user, password=password, timeout=10)
        print(f"[+] SUCCESS! Authenticated to {user}@{host} over SSH.")
        
        commands = [
            ("User identity", "whoami"),
            ("Host & Kernel", "uname -a"),
            ("OS Release", "cat /etc/os-release | grep PRETTY_NAME"),
            ("Network Interfaces", "ip -brief addr"),
            ("Routing Table", "ip route"),
            ("Internet Ping Check", "ping -c 2 8.8.8.8 || ping -c 2 1.1.1.1 || echo 'No Internet via default route'"),
            ("Wireless Interfaces", "iw dev || iwconfig || true"),
            ("Sudo Privileges Check", f"echo '{password}' | sudo -S whoami")
        ]
        
        for label, cmd in commands:
            print(f"\n--- [{label}]: {cmd} ---")
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
            out = stdout.read().decode('utf-8', errors='replace')
            err = stderr.read().decode('utf-8', errors='replace')
            if out:
                print(out.strip())
            if err:
                print(f"[STDERR]: {err.strip()}")
                
        client.close()
        return True
    except Exception as e:
        print(f"[-] SSH connection failed: {e}")
        return False

if __name__ == "__main__":
    test_ssh()
