import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.137.177', port=22, username='ghost', password='9233', timeout=5)

cmd = "pkill -9 deskflow-core 2>/dev/null; sleep 1; export DISPLAY=:0; timeout 4 /usr/bin/deskflow-core client --new-instance 192.168.137.1:24800 2>&1"
stdin, stdout, stderr = client.exec_command(cmd)
out = stdout.read().decode('utf-8')
print("Full Output:")
print(out)

client.close()
