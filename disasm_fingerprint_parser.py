import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.137.177', port=22, username='ghost', password='9233', timeout=5)

# Let's find the address of rodata string "%z1failed to open trusted fingerprints file"
cmd = """gdb -batch /usr/bin/deskflow-core -ex 'find /w 0x0000000000024b40, 0x00000000001343a9, 0x13dbe8' -ex 'disassemble 0x93000, 0x95000' 2>/dev/null | head -n 40"""
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode('utf-8'))

client.close()
