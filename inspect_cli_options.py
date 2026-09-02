import paramiko
import re

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.137.177', port=22, username='ghost', password='9233', timeout=5)

stdin, stdout, stderr = client.exec_command("strings /usr/bin/deskflow-core")
out = stdout.read().decode('latin-1')

options = re.findall(r'--[a-zA-Z0-9_-]+', out)
print("All -- options in /usr/bin/deskflow-core:")
for opt in sorted(set(options)):
    print(" ", opt)

client.close()
