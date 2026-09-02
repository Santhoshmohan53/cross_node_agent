#!/usr/bin/env python3
"""
Aegis Unified Command Center Hub Server
Central orchestration engine and Web Dashboard server.
Connects Kali Linux and Windows Daemons into a single unified control surface.
Runs on Port 8080.
"""

import asyncio
import os
import sys
import json
import time
import socket
from pathlib import Path
from typing import Dict, Any, List, Optional

import httpx
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Ensure parent directory in path
CURRENT_DIR = Path(__file__).parent
sys.path.insert(0, str(CURRENT_DIR / "daemon"))

from common_models import (
    TaskRequest, TaskResponse, ValidationRequest, ValidationResponse,
    SystemStatus, WorkflowRequest, WorkflowResult, WorkflowStep
)
from agent_bridge import AgentBridge

app = FastAPI(
    title="Aegis Unified Cross-Node Command Center",
    description="Unified Management Surface for Kali Linux & Windows Agent Correlation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurable Daemon URLs (Supports dynamic override and default 192.168.137.177 / 10.42.0.1)
KALI_CANDIDATES = [
    os.environ.get("KALI_DAEMON_URL", "http://10.42.0.1:8765"),
    "http://192.168.137.177:8765",
    "http://100.98.110.86:8765",
]
WINDOWS_URL = os.environ.get("WINDOWS_DAEMON_URL", "http://127.0.0.1:8766")

active_kali_url = KALI_CANDIDATES[0]
bridge = AgentBridge(kali_url=active_kali_url, windows_url=WINDOWS_URL)

# Mount static web directory
STATIC_DIR = CURRENT_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>Unified Dashboard is initializing...</h1>", status_code=200)
    return HTMLResponse(content=index_file.read_text(encoding="utf-8"), status_code=200)


async def _probe_kali():
    global active_kali_url
    async def _probe_single(url: str):
        t0 = time.time()
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                resp = await client.get(f"{url}/api/status")
                if resp.status_code == 200:
                    lat = round((time.time() - t0) * 1000, 1)
                    return True, lat, resp.json(), url
        except Exception:
            pass
        return False, None, None, url

    # Probe all candidate URLs concurrently
    tasks = [_probe_single(url) for url in KALI_CANDIDATES]
    results = await asyncio.gather(*tasks)
    for reachable, lat, data, url in results:
        if reachable:
            active_kali_url = url
            bridge.kali_url = url
            return True, lat, data, url

    return False, None, {"status": "offline", "node_name": "Kali Linux Mini PC", "error": "Unreachable"}, active_kali_url


async def _probe_windows():
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            resp = await client.get(f"{WINDOWS_URL}/api/status")
            if resp.status_code == 200:
                lat = round((time.time() - t0) * 1000, 1)
                return True, lat, resp.json()
    except Exception:
        pass
    return False, None, {"status": "offline", "node_name": "Windows Host PC", "error": "Unreachable"}


@app.get("/api/hub/topology")
async def get_topology():
    """Polls both Kali and Windows daemons concurrently and aggregates the network matrix."""
    kali_res, win_res = await asyncio.gather(_probe_kali(), _probe_windows())
    kali_reachable, kali_latency_ms, kali_status, found_kali_url = kali_res
    win_reachable, win_latency_ms, win_status = win_res

    return {
        "timestamp": time.time(),
        "endpoints": {
            "kali_url": found_kali_url,
            "windows_url": WINDOWS_URL
        },
        "kali": {
            "reachable": kali_reachable,
            "latency_ms": kali_latency_ms,
            "data": kali_status
        },
        "windows": {
            "reachable": win_reachable,
            "latency_ms": win_latency_ms,
            "data": win_status
        }
    }


@app.post("/api/hub/execute")
async def hub_execute(node: str, task: TaskRequest):
    """Dispatches a command directly to the selected node."""
    if node.lower() == "kali":
        return await bridge.execute_on_kali(
            command=task.command,
            working_dir=task.working_dir,
            timeout=task.timeout,
            shell_type=task.shell_type
        )
    elif node.lower() == "windows":
        return await bridge.execute_on_windows(
            command=task.command,
            working_dir=task.working_dir,
            timeout=task.timeout,
            shell_type=task.shell_type
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unknown node: {node}. Use 'kali' or 'windows'.")


@app.post("/api/hub/validate")
async def hub_validate(node: str, val: ValidationRequest):
    """Dispatches a validation check to the selected node."""
    if node.lower() == "kali":
        return await bridge.validate_on_kali(val)
    elif node.lower() == "windows":
        return await bridge.validate_on_windows(val)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown node: {node}")


@app.post("/api/hub/workflow/run", response_model=WorkflowResult)
async def run_workflow(wf: WorkflowRequest):
    """Runs a multi-step cross-node correlation playbook."""
    start_time = time.time()
    step_results = []
    workflow_status = "completed"

    for step in wf.steps:
        step_start = time.time()
        step_entry = {
            "step_id": step.step_id,
            "name": step.name,
            "target_node": step.target_node,
            "action_type": step.action_type,
            "passed": True,
            "details": None,
            "duration_ms": 0.0
        }

        try:
            if step.action_type == "execute":
                res = await hub_execute(step.target_node, TaskRequest(command=step.command or ""))
                step_entry["details"] = res.model_dump()
                step_entry["passed"] = (res.status == "completed")
            elif step.action_type == "validate":
                if step.validation:
                    res = await hub_validate(step.target_node, step.validation)
                    step_entry["details"] = res.model_dump()
                    step_entry["passed"] = res.passed
                else:
                    step_entry["passed"] = False
                    step_entry["details"] = {"error": "Missing validation definition"}
        except Exception as e:
            step_entry["passed"] = False
            step_entry["details"] = {"error": str(e)}

        step_entry["duration_ms"] = round((time.time() - step_start) * 1000, 2)
        step_results.append(step_entry)

        if not step_entry["passed"] and not step.continue_on_failure:
            workflow_status = "failed"
            break

    total_time_ms = round((time.time() - start_time) * 1000, 2)
    return WorkflowResult(
        workflow_id=wf.workflow_id,
        name=wf.name,
        status=workflow_status,
        step_results=step_results,
        total_time_ms=total_time_ms
    )


@app.post("/api/hub/agent/orchestrate")
async def orchestrate_prompt(data: Dict[str, Any]):
    """
    Autonomous Cross-System Agent Orchestrator.
    Takes a natural language goal, translates it into coordinated Kali + Windows actions,
    and returns an execution roadmap with results.
    """
    goal = data.get("prompt", "")
    if not goal:
        raise HTTPException(status_code=400, detail="Missing 'prompt' in request body")

    # Built-in intelligent intent parsing & execution patterns
    lower_goal = goal.lower()
    executed_steps = []

    if "scan" in lower_goal or "nmap" in lower_goal or "port" in lower_goal:
        # Pattern 1: Security Recon & Cross-Node Validation
        target_ip = "192.168.137.177" if "192.168.137" in KALI_URL else "10.42.0.1"
        if "google" in lower_goal or "web" in lower_goal:
            target_ip = "8.8.8.8"

        # Step 1: Kali executes Nmap / Network discovery
        step1 = await bridge.execute_on_kali(f"nmap -F {target_ip} || ping -c 3 {target_ip}")
        executed_steps.append({
            "node": "Kali Linux",
            "action": f"Executed Network Recon ({target_ip})",
            "output": step1.stdout or step1.stderr,
            "status": step1.status
        })

        # Step 2: Windows validates connectivity to discovered ports
        val = ValidationRequest(check_type="ping", target=target_ip)
        step2 = await bridge.validate_on_windows(val)
        executed_steps.append({
            "node": "Windows Host",
            "action": f"Cross-Validated reachability from Windows client",
            "output": step2.message,
            "status": "passed" if step2.passed else "failed"
        })

    elif "wifi" in lower_goal or "monitor" in lower_goal or "packet" in lower_goal or "capture" in lower_goal:
        # Pattern 2: Wireless & Sniffing Mode
        step1 = await bridge.set_kali_wifi_mode(mode="monitor")
        executed_steps.append({
            "node": "Kali Linux",
            "action": "Set Wi-Fi adapter to Monitor Mode",
            "output": step1.get("output", "Mode switched"),
            "status": "completed" if step1.get("success") else "failed"
        })
        
        # Step 2: Validate Windows routing status
        step2 = await bridge.validate_on_windows(ValidationRequest(check_type="custom_script", custom_script="Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Select-Object -ExpandProperty NextHop"))
        executed_steps.append({
            "node": "Windows Host",
            "action": "Checked Windows Default Gateway Route",
            "output": step2.details.get("stdout", "") if step2.details else step2.message,
            "status": "passed" if step2.passed else "failed"
        })

    else:
        # General Command Distribution
        step1 = await bridge.execute_on_kali("uname -a && uptime")
        executed_steps.append({
            "node": "Kali Linux",
            "action": "System Information Check",
            "output": step1.stdout,
            "status": step1.status
        })
        step2 = await bridge.execute_on_windows("Get-ComputerInfo | Select-Object WindowsProductName, OsVersion, CsProcessors")
        executed_steps.append({
            "node": "Windows Host",
            "action": "Host System Verification",
            "output": step2.stdout,
            "status": step2.status
        })

    return {
        "prompt": goal,
        "summary": f"Executed multi-agent plan for: '{goal}'",
        "plan_steps": executed_steps,
        "completed_at": time.time()
    }


if __name__ == "__main__":
    port = int(os.environ.get("HUB_PORT", 8080))
    print(f"[*] Starting Aegis Unified Command Center Hub on http://0.0.0.0:{port}")
    uvicorn.run("hub_server:app", host="0.0.0.0", port=port, reload=False)
