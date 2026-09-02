import paramiko
import re

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.137.177', port=22, username='ghost', password='9233', timeout=5)

stdin, stdout, stderr = client.exec_command('strings /usr/bin/deskflow | grep -E "tls[A-Z]|crypto[A-Z]|security[A-Z]|enableTls|tlsEnabled"')
out = stdout.read().decode('utf-8')
print("Keys in Deskflow GUI:")
for line in sorted(set(out.splitlines())):
    print(" ", line)

client.close()
