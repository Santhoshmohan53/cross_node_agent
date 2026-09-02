import paramiko
import re

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.137.177', port=22, username='ghost', password='9233', timeout=5)

stdin, stdout, stderr = client.exec_command("strings /usr/bin/deskflow")
out = stdout.read().decode('latin-1')

# Extract strings of format word/word or CamelCase
keys = set()
for line in out.splitlines():
    line = line.strip()
    if 3 < len(line) < 40 and re.match(r'^[a-zA-Z0-9_]+(/[a-zA-Z0-9_]+)*$', line):
        if any(w in line.lower() for w in ['tls', 'cert', 'crypto', 'sec', 'host', 'mode', 'screen', 'client', 'server']):
            keys.add(line)

print("QSettings candidate keys in Deskflow:")
for k in sorted(keys):
    print(" ", k)

client.close()
