import paramiko
import re

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.137.177', port=22, username='ghost', password='9233', timeout=5)

cmd = "gdb -batch -ex 'set print asm-demangle on' -ex 'disassemble 0x1286a0, 0x128710' /usr/bin/deskflow-core"
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode('utf-8'))

client.close()
