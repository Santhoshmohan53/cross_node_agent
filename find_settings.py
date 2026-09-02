from pathlib import Path
import re

bin_path = Path(r"C:\Users\user\.gemini\antigravity-ide\scratch\cross_node_agent\bin\deskflow\deskflow-1.26.0-win-x64-portable\deskflow.exe")
data = bin_path.read_bytes().decode('latin-1')

# In Qt, QSettings keys often appear near setValue or value
for match in re.finditer(r'([a-zA-Z0-9_/]+(?:Tls|Cert|Crypto|Security|Mode|Server|Client|Port|Host)[a-zA-Z0-9_/]*)', data):
    print("Found key:", match.group(1))
