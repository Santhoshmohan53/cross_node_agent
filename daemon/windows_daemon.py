#!/usr/bin/env python3
"""
Windows Agent Daemon (Aegis Windows Node)
Runs on Windows Host PC (Port 8766).
Handles async task execution (PowerShell/CMD), live WebSocket streaming,
system metrics, cross-node validation, and file sync.
"""

import asyncio
import os
import sys
import platform
import socket
import re
import time
import shutil
from typing import Dict, Any, Optional
from pathlib import Path

import psutil
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uvicorn

# Ensure parent directory in path
sys.path.insert(0, str(Path(__file__).parent))
from common_models import (
    TaskRequest, TaskResponse, ValidationRequest, ValidationResponse,
    SystemStatus
)

app = FastAPI(
    title="Aegis Windows Agent Daemon",
    description="Cross-Node Agent Daemon & Execution Node for Windows",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PEER_KALI_URL = os.environ.get("KALI_DAEMON_URL", "http://192.168.137.177:8765")
STORAGE_DIR = Path(os.environ.get("TEMP", "C:/Temp")) / "aegis_storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
START_TIME = time.time()


@app.get("/api/status", response_model=SystemStatus)
async def get_status():
    """Returns real-time Windows system metrics, network adapters, and gateway info."""
    ips = {}
    for iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                ips[iface] = addr.address

    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")
    
    # Try finding default gateway on Windows
    gateway = None
    try:
        net_stats = psutil.net_if_stats()
        # Look via netstat or route print if needed
        proc = os.popen("route print 0.0.0.0").read()
        gw_match = re.search(r"0\.0\.0\.0\s+0\.0\.0\.0\s+([0-9.]+)", proc)
        if gw_match:
            gateway = gw_match.group(1)
    except Exception:
        pass

    return SystemStatus(
        node_name="Windows Host PC",
        os_name=f"{platform.system()} {platform.release()} (Build {platform.version()})",
        hostname=platform.node(),
        status="online",
        ip_addresses=ips,
        default_gateway=gateway,
        cpu_percent=psutil.cpu_percent(interval=0.1),
        memory_used_mb=round((mem.total - mem.available) / (1024 * 1024), 1),
        memory_total_mb=round(mem.total / (1024 * 1024), 1),
        memory_percent=mem.percent,
        disk_used_percent=disk.percent,
        wifi_info=None,
        uptime_seconds=round(time.time() - START_TIME, 1)
    )


@app.post("/api/execute", response_model=TaskResponse)
async def execute_task(task: TaskRequest):
    """Executes PowerShell or CMD commands on Windows asynchronously."""
    start_time = time.time()
    env = os.environ.copy()
    if task.env_vars:
        env.update(task.env_vars)

    cwd = task.working_dir if task.working_dir and os.path.isdir(task.working_dir) else None
    
    # Determine shell (Default to PowerShell)
    if task.shell_type == "cmd":
        shell_cmd = ["cmd.exe", "/c", task.command]
    elif task.shell_type == "python":
        shell_cmd = [sys.executable, "-c", task.command]
    else:  # powershell
        shell_cmd = ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", task.command]

    try:
        proc = await asyncio.create_subprocess_exec(
            *shell_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=float(task.timeout)
            )
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            status = "completed" if proc.returncode == 0 else "failed"
            exit_code = proc.returncode
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            stdout = ""
            stderr = f"Execution timed out after {task.timeout} seconds"
            status = "timeout"
            exit_code = -1

    except Exception as e:
        stdout = ""
        stderr = f"Failed to spawn process: {str(e)}"
        status = "failed"
        exit_code = -1

    duration_ms = round((time.time() - start_time) * 1000, 2)
    return TaskResponse(
        task_id=task.task_id,
        status=status,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        execution_time_ms=duration_ms
    )


@app.websocket("/ws/terminal")
async def websocket_terminal(websocket: WebSocket):
    """Live streaming PowerShell terminal session on Windows."""
    await websocket.accept()
    try:
        await websocket.send_json({"type": "info", "data": "Connected to Windows PowerShell Session\n"})
        while True:
            data = await websocket.receive_json()
            command = data.get("command")
            if not command:
                continue

            await websocket.send_json({"type": "stdout", "data": f"PS > {command}\n"})
            
            proc = await asyncio.create_subprocess_exec(
                "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            async def stream_output(stream, msg_type):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    await websocket.send_json({"type": msg_type, "data": line.decode("utf-8", errors="replace")})

            await asyncio.gather(
                stream_output(proc.stdout, "stdout"),
                stream_output(proc.stderr, "stderr")
            )
            await proc.wait()
            await websocket.send_json({"type": "exit", "code": proc.returncode})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "data": str(e)})
        except Exception:
            pass


@app.post("/api/validate", response_model=ValidationResponse)
async def validate_state(req: ValidationRequest):
    """Executes validation assertions on Windows."""
    passed = False
    message = ""
    actual_val = None
    details = {}

    try:
        if req.check_type == "ping":
            target = req.target or "10.42.0.1"
            proc = await asyncio.create_subprocess_exec(
                "ping.exe", "-n", "1", "-w", "1000", target,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            s_out, _ = await proc.communicate()
            passed = (proc.returncode == 0)
            actual_val = passed
            message = f"Ping from Windows to {target}: {'REACHABLE' if passed else 'UNREACHABLE'}"

        elif req.check_type == "port_open":
            host = req.target or "127.0.0.1"
            port = req.port or 80
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            res = sock.connect_ex((host, port))
            sock.close()
            passed = (res == 0)
            actual_val = passed
            message = f"Port {port} on {host} is {'OPEN' if passed else 'CLOSED'}"

        elif req.check_type == "http_status":
            url = req.target or "http://127.0.0.1"
            expected = req.expected_status_code or 200
            async with httpx.AsyncClient(timeout=5.0) as client:
                try:
                    resp = await client.get(url)
                    actual_val = resp.status_code
                    passed = (resp.status_code == expected)
                    message = f"HTTP GET {url} returned status {resp.status_code} (expected {expected})"
                except Exception as ex:
                    passed = False
                    message = f"HTTP GET {url} failed: {str(ex)}"

        elif req.check_type == "process_running":
            proc_name = req.process_name or ""
            running = any(proc_name.lower() in p.name().lower() for p in psutil.process_iter(['name']))
            passed = running
            actual_val = running
            message = f"Windows Process '{proc_name}' is {'running' if running else 'not running'}"

        elif req.check_type == "file_exists":
            fpath = Path(req.file_path or "")
            passed = fpath.exists()
            actual_val = passed
            message = f"Windows File '{fpath}' {'exists' if passed else 'does not exist'}"
            if passed:
                details["size_bytes"] = fpath.stat().st_size

        elif req.check_type == "custom_script":
            script = req.custom_script or "exit 0"
            proc = await asyncio.create_subprocess_exec(
                "powershell.exe", "-NoProfile", "-Command", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            s_out, s_err = await proc.communicate()
            passed = (proc.returncode == 0)
            actual_val = proc.returncode
            message = f"PowerShell validation script exit code: {proc.returncode}"
            details["stdout"] = s_out.decode("utf-8", errors="replace")
            details["stderr"] = s_err.decode("utf-8", errors="replace")

        else:
            message = f"Unsupported check type: {req.check_type}"

    except Exception as e:
        passed = False
        message = f"Validation exception: {str(e)}"

    return ValidationResponse(
        validation_id=req.validation_id,
        check_type=req.check_type,
        passed=passed,
        actual_value=actual_val,
        message=message,
        details=details
    )


@app.post("/api/files/upload")
async def upload_file(file: UploadFile = File(...)):
    """Receives and stores uploaded files."""
    dest_path = STORAGE_DIR / file.filename
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"filename": file.filename, "saved_path": str(dest_path), "size_bytes": dest_path.stat().st_size}


@app.get("/api/files/download")
async def download_file(path: str):
    """Downloads a file from Windows Host."""
    fpath = Path(path)
    if not fpath.exists() or not fpath.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=str(fpath), filename=fpath.name)


@app.post("/api/peer/forward")
async def forward_to_kali(endpoint: str, payload: Dict[str, Any]):
    """Proxies an API request directly to the Kali peer daemon."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            url = f"{PEER_KALI_URL.rstrip('/')}/{endpoint.lstrip('/')}"
            resp = await client.post(url, json=payload)
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to reach Kali peer at {PEER_KALI_URL}: {str(e)}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8766))
    print(f"[*] Starting Aegis Windows Agent Daemon on port {port}...")
    uvicorn.run("windows_daemon:app", host="0.0.0.0", port=port, reload=False)
