#!/usr/bin/env python3
"""
Kali Linux Agent Daemon (Aegis Kali Node)
Runs on Kali Mini PC (Port 8765).
Handles async task execution, live WebSocket streaming, Wi-Fi monitor mode switching,
system metrics, and cross-node validation.
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
    SystemStatus, WiFiModeRequest
)

app = FastAPI(
    title="Aegis Kali Agent Daemon",
    description="Cross-Node Agent Daemon & Execution Node for Kali Linux",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PEER_WINDOWS_URL = os.environ.get("WINDOWS_DAEMON_URL", "http://10.42.0.10:8766")
STORAGE_DIR = Path("/tmp/aegis_storage")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
START_TIME = time.time()


def get_wifi_status() -> Dict[str, Any]:
    """Inspects wireless interfaces on Kali Linux."""
    wifi_info = {"interface": None, "mode": "unknown", "ssid": None, "channel": None}
    try:
        # Check via iw dev
        proc = os.popen("iw dev 2>/dev/null").read()
        if proc:
            iface_match = re.search(r"Interface\s+([a-zA-Z0-9_-]+)", proc)
            type_match = re.search(r"type\s+([a-zA-Z0-9_-]+)", proc)
            ssid_match = re.search(r"ssid\s+([^\n]+)", proc)
            channel_match = re.search(r"channel\s+([0-9]+)", proc)
            if iface_match:
                wifi_info["interface"] = iface_match.group(1)
            if type_match:
                wifi_info["mode"] = type_match.group(1)
            if ssid_match:
                wifi_info["ssid"] = ssid_match.group(1).strip()
            if channel_match:
                wifi_info["channel"] = int(channel_match.group(1))
    except Exception as e:
        wifi_info["error"] = str(e)
    return wifi_info


@app.get("/api/status", response_model=SystemStatus)
async def get_status():
    """Returns real-time system metrics, IP addresses, and Wi-Fi state."""
    ips = {}
    for iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET:
                ips[iface] = addr.address

    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    
    # Try finding default gateway
    gateway = None
    try:
        route_out = os.popen("ip route | grep default").read()
        gw_match = re.search(r"default via ([0-9.]+)", route_out)
        if gw_match:
            gateway = gw_match.group(1)
    except Exception:
        pass

    return SystemStatus(
        node_name="Kali Linux Mini PC",
        os_name=f"{platform.system()} {platform.release()}",
        hostname=platform.node(),
        status="online",
        ip_addresses=ips,
        default_gateway=gateway,
        cpu_percent=psutil.cpu_percent(interval=0.1),
        memory_used_mb=round((mem.total - mem.available) / (1024 * 1024), 1),
        memory_total_mb=round(mem.total / (1024 * 1024), 1),
        memory_percent=mem.percent,
        disk_used_percent=disk.percent,
        wifi_info=get_wifi_status(),
        uptime_seconds=round(time.time() - START_TIME, 1)
    )


@app.post("/api/execute", response_model=TaskResponse)
async def execute_task(task: TaskRequest):
    """Executes a command on Kali Linux asynchronously."""
    start_time = time.time()
    env = os.environ.copy()
    if task.env_vars:
        env.update(task.env_vars)

    cwd = task.working_dir if task.working_dir and os.path.isdir(task.working_dir) else None
    
    # Determine shell
    shell_cmd = ["/bin/bash", "-c", task.command] if task.shell_type in ["bash", "default"] else ["/bin/sh", "-c", task.command]

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
    """Live interactive WebSocket terminal session on Kali Linux."""
    await websocket.accept()
    try:
        await websocket.send_json({"type": "info", "data": "Connected to Kali Linux Terminal Session\n"})
        while True:
            data = await websocket.receive_json()
            command = data.get("command")
            if not command:
                continue

            await websocket.send_json({"type": "stdout", "data": f"$ {command}\n"})
            
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
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


@app.post("/api/wifi/mode")
async def toggle_wifi_mode(req: WiFiModeRequest):
    """Switches Wi-Fi interface between Managed and Monitor modes."""
    iface = req.interface or get_wifi_status().get("interface")
    if not iface:
        raise HTTPException(status_code=400, detail="No wireless interface found")

    target_mode = req.mode.lower()
    cmd = ""
    if target_mode == "monitor":
        cmd = f"sudo airmon-ng start {iface} || (sudo ip link set {iface} down && sudo iw dev {iface} set type monitor && sudo ip link set {iface} up)"
    else:
        cmd = f"sudo airmon-ng stop {iface} || (sudo ip link set {iface} down && sudo iw dev {iface} set type managed && sudo ip link set {iface} up)"

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    return {
        "success": proc.returncode == 0,
        "interface": iface,
        "requested_mode": target_mode,
        "current_status": get_wifi_status(),
        "output": stdout.decode("utf-8", errors="replace") + stderr.decode("utf-8", errors="replace")
    }


@app.post("/api/validate", response_model=ValidationResponse)
async def validate_state(req: ValidationRequest):
    """Executes validation assertions on Kali Linux."""
    passed = False
    message = ""
    actual_val = None
    details = {}

    try:
        if req.check_type == "ping":
            target = req.target or "8.8.8.8"
            proc = await asyncio.create_subprocess_shell(
                f"ping -c 2 -W 2 {target}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            passed = proc.returncode == 0
            actual_val = passed
            message = f"Ping to {target} {'succeeded' if passed else 'failed'}"

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

        elif req.check_type == "process_running":
            proc_name = req.process_name or ""
            running = any(proc_name.lower() in p.name().lower() for p in psutil.process_iter(['name']))
            passed = running
            actual_val = running
            message = f"Process '{proc_name}' is {'running' if running else 'not running'}"

        elif req.check_type == "file_exists":
            fpath = Path(req.file_path or "")
            passed = fpath.exists()
            actual_val = passed
            message = f"File '{fpath}' {'exists' if passed else 'does not exist'}"
            if passed:
                details["size_bytes"] = fpath.stat().st_size

        elif req.check_type == "custom_script":
            script = req.custom_script or "exit 0"
            proc = await asyncio.create_subprocess_shell(
                script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            s_out, s_err = await proc.communicate()
            passed = (proc.returncode == 0)
            actual_val = proc.returncode
            message = f"Custom validation script exit code: {proc.returncode}"
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
    """Downloads a file from Kali Linux."""
    fpath = Path(path)
    if not fpath.exists() or not fpath.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=str(fpath), filename=fpath.name)


@app.post("/api/peer/forward")
async def forward_to_windows(endpoint: str, payload: Dict[str, Any]):
    """Proxies an API request directly to the Windows peer daemon."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            url = f"{PEER_WINDOWS_URL.rstrip('/')}/{endpoint.lstrip('/')}"
            resp = await client.post(url, json=payload)
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to reach Windows peer at {PEER_WINDOWS_URL}: {str(e)}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    print(f"[*] Starting Aegis Kali Agent Daemon on port {port}...")
    uvicorn.run("kali_daemon:app", host="0.0.0.0", port=port, reload=False)
