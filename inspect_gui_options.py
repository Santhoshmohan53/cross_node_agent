import paramiko
import re

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.137.177', port=22, username='ghost', password='9233', timeout=5)

stdin, stdout, stderr = client.exec_command("strings /usr/bin/deskflow")
out = stdout.read().decode('latin-1')

# Extract settings keys
keys = re.findall(r'[a-zA-Z0-9_/]+(?:Tls|tls|Crypto|crypto|Ssl|ssl|Fingerprint|fingerprint|Cert|cert|Security|security)[a-zA-Z0-9_/]*', out)
print("Keys in /usr/bin/deskflow:")
for k in sorted(set(keys))[:50]:
    print(" ", k)

client.close()
