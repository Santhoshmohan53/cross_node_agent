import socket
import concurrent.futures
import subprocess
import re
import sys

def ping_host(ip):
    try:
        res = subprocess.run(["ping", "-n", "1", "-w", "400", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return ip, res.returncode == 0
    except Exception:
        return ip, False

def check_port(ip, port, timeout=1.0):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        res = s.connect_ex((ip, port))
        s.close()
        return res == 0
    except Exception:
        return False

def scan_subnet(prefix, start=1, end=254):
    print(f"[*] Scanning {prefix}.{start} - {prefix}.{end}...")
    ips = [f"{prefix}.{i}" for i in range(start, end + 1)]
    live_hosts = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        results = executor.map(ping_host, ips)
        for ip, is_alive in results:
            if is_alive:
                live_hosts.append(ip)
                print(f"  [+] Host is UP: {ip}")
    
    return live_hosts

if __name__ == "__main__":
    subnets = ["192.168.137", "192.168.0", "10.42.0"]
    all_live = []
    
    for sub in subnets:
        live = scan_subnet(sub)
        all_live.extend(live)
    
    print("\n" + "="*50)
    print(f"[*] Discovered {len(all_live)} live hosts. Probing SSH (22) and Daemon (8765)...")
    print("="*50)
    
    for ip in all_live:
        ssh_open = check_port(ip, 22)
        daemon_open = check_port(ip, 8765)
        http_open = check_port(ip, 80)
        print(f" -> IP: {ip:15} | SSH (22): {'OPEN' if ssh_open else 'Closed':6} | Aegis Daemon (8765): {'OPEN' if daemon_open else 'Closed':6} | HTTP (80): {'OPEN' if http_open else 'Closed'}")
