import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.137.177', port=22, username='ghost', password='9233', timeout=5)

cmd = "gdb -batch -ex 'file /usr/bin/deskflow-core' -ex 'disassemble /s' 2>&1"
# Let's search strings in rodata of deskflow-core
stdin, stdout, stderr = client.exec_command("readelf -p .rodata /usr/bin/deskflow-core | grep -C 10 '3394'")
print(stdout.read().decode('utf-8'))

client.close()
