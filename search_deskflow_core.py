import paramiko
import re

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.137.177', port=22, username='ghost', password='9233', timeout=5)

stdin, stdout, stderr = client.exec_command("strings /usr/bin/deskflow-core")
out = stdout.read().decode('latin-1')

matches = [line for line in out.splitlines() if any(k in line.lower() for k in ['trusted', 'fingerprint', 'ssl', '.pem', '.txt', 'deskflow', 'barrier', 'tls'])]
print("Found strings in /usr/bin/deskflow-core:")
for m in sorted(set(matches))[:50]:
    print(" ", m)

client.close()
