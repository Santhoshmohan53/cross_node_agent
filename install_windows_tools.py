import os
import sys
import subprocess
import urllib.request
from pathlib import Path

TEMP_DIR = Path(os.environ.get("TEMP", "C:/Temp"))

def install_barrier():
    print("[1/2] Installing Barrier on Windows...")
    # Check if already installed
    prog_files = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Barrier"
    prog_files_x86 = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Barrier"
    if (prog_files / "barriers.exe").exists() or (prog_files_x86 / "barriers.exe").exists():
        print("  -> Barrier is already installed.")
        return True

    installer_url = "https://github.com/debauchee/barrier/releases/download/v2.4.0/BarrierSetup-2.4.0-release.exe"
    installer_path = TEMP_DIR / "BarrierSetup-2.4.0.exe"
    
    if not installer_path.exists():
        print(f"  -> Downloading Barrier installer from {installer_url}...")
        urllib.request.urlretrieve(installer_url, installer_path)
        print("  -> Download complete.")

    print("  -> Executing silent installation...")
    try:
        res = subprocess.run([str(installer_path), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-"], capture_output=True, timeout=120)
        print(f"  -> Installer exit code: {res.returncode}")
        return res.returncode == 0
    except Exception as e:
        print(f"  -> Failed to install Barrier: {e}")
        return False

def install_spacedesk():
    print("\n[2/2] Installing Spacedesk Driver on Windows...")
    # Check if spacedesk service exists
    try:
        srv_check = subprocess.run(["sc", "query", "spacedeskHookKmode"], capture_output=True, text=True)
        if "RUNNING" in srv_check.stdout or "STOPPED" in srv_check.stdout:
            print("  -> Spacedesk service is already installed.")
            return True
    except Exception:
        pass

    print("  -> Attempting install via winget...")
    try:
        res = subprocess.run(
            ["winget", "install", "--id", "Datronicsoft.SpacedeskDriver.Server", "--accept-source-agreements", "--accept-package-agreements", "--silent"],
            capture_output=True,
            text=True,
            timeout=180
        )
        print(f"  -> Winget output:\n{res.stdout}")
        if res.returncode == 0:
            return True
    except Exception as e:
        print(f"  -> Winget install error: {e}")

    # Fallback to direct MSI download if winget fails
    msi_url = "https://www.spacedesk.net/download/spacedesk_driver_Win_10_64_v2229_BETA.msi"
    msi_path = TEMP_DIR / "spacedesk_driver_64.msi"
    try:
        print(f"  -> Downloading Spacedesk MSI from {msi_url}...")
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(msi_url, headers=headers)
        with urllib.request.urlopen(req) as response, open(msi_path, 'wb') as out_file:
            out_file.write(response.read())
        print("  -> Download complete. Installing MSI...")
        res = subprocess.run(["msiexec", "/i", str(msi_path), "/qn", "/norestart"], capture_output=True, timeout=180)
        print(f"  -> MSI exit code: {res.returncode}")
        return res.returncode == 0
    except Exception as e:
        print(f"  -> MSI install error: {e}")
        return False

if __name__ == "__main__":
    b_ok = install_barrier()
    s_ok = install_spacedesk()
    print("\n" + "="*50)
    print(f"Barrier Installed: {b_ok}")
    print(f"Spacedesk Installed: {s_ok}")
    print("="*50)
