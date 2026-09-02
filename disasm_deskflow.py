import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.137.177', port=22, username='ghost', password='9233', timeout=5)

cmd = "gdb -batch -ex 'file /usr/bin/deskflow-core' -ex 'disassemble /m' 2>&1"
stdin, stdout, stderr = client.exec_command("strings -a /usr/bin/deskflow-core | grep -E '\.txt|\.pem|Fingerprints|fingerprints|SSL|tls' | head -n 40")
print(stdout.read().decode('utf-8'))

client.close()
