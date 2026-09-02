"""
Aegis Agent Bridge Client Library
Provides a high-level asynchronous API for agents to execute tasks, run toolchains,
stream outputs, sync files, and perform cross-node validation across Kali Linux and Windows.
"""

import asyncio
from typing import Dict, Any, Optional, List, Union
import httpx
from pathlib import Path

from common_models import (
    TaskRequest, TaskResponse, ValidationRequest, ValidationResponse,
    SystemStatus, WiFiModeRequest, WorkflowRequest, WorkflowResult
)

class AgentBridge:
    def __init__(
        self,
        kali_url: str = "http://192.168.137.177:8765",
        windows_url: str = "http://127.0.0.1:8766",
        timeout: float = 120.0
    ):
        self.kali_url = kali_url.rstrip("/")
        self.windows_url = windows_url.rstrip("/")
        self.timeout = timeout

    async def get_node_status(self, node: str = "kali") -> SystemStatus:
        """Fetch system status, IP addresses, and hardware metrics from target node."""
        base_url = self.kali_url if node.lower() == "kali" else self.windows_url
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(f"{base_url}/api/status")
                resp.raise_for_status()
                return SystemStatus(**resp.json())
        except Exception as e:
            return SystemStatus(
                node_name="Kali Linux Mini PC" if node.lower() == "kali" else "Windows Host PC",
                os_name="Unknown (Offline)",
                hostname="Offline",
                status="offline",
                default_gateway=None
            )

    async def execute_on_kali(
        self,
        command: str,
        working_dir: Optional[str] = None,
        timeout: int = 120,
        shell_type: str = "bash",
        env_vars: Optional[Dict[str, str]] = None
    ) -> TaskResponse:
        """Executes a bash/sh command or toolchain on the Kali Linux node."""
        req = TaskRequest(
            command=command,
            working_dir=working_dir,
            timeout=timeout,
            shell_type=shell_type,
            env_vars=env_vars
        )
        try:
            async with httpx.AsyncClient(timeout=float(timeout + 5)) as client:
                resp = await client.post(f"{self.kali_url}/api/execute", json=req.model_dump())
                resp.raise_for_status()
                return TaskResponse(**resp.json())
        except Exception as e:
            return TaskResponse(
                task_id=req.task_id,
                status="failed",
                exit_code=-1,
                stderr=f"Kali Linux node unreachable at {self.kali_url}: {str(e)}"
            )

    async def execute_on_windows(
        self,
        command: str,
        working_dir: Optional[str] = None,
        timeout: int = 120,
        shell_type: str = "powershell",
        env_vars: Optional[Dict[str, str]] = None
    ) -> TaskResponse:
        """Executes a PowerShell or CMD command on the Windows node."""
        req = TaskRequest(
            command=command,
            working_dir=working_dir,
            timeout=timeout,
            shell_type=shell_type,
            env_vars=env_vars
        )
        try:
            async with httpx.AsyncClient(timeout=float(timeout + 5)) as client:
                resp = await client.post(f"{self.windows_url}/api/execute", json=req.model_dump())
                resp.raise_for_status()
                return TaskResponse(**resp.json())
        except Exception as e:
            return TaskResponse(
                task_id=req.task_id,
                status="failed",
                exit_code=-1,
                stderr=f"Windows Host node unreachable at {self.windows_url}: {str(e)}"
            )

    async def validate_on_kali(self, validation: ValidationRequest) -> ValidationResponse:
        """Performs a validation assertion on the Kali Linux node."""
        try:
            async with httpx.AsyncClient(timeout=float(validation.timeout + 5)) as client:
                resp = await client.post(f"{self.kali_url}/api/validate", json=validation.model_dump())
                resp.raise_for_status()
                return ValidationResponse(**resp.json())
        except Exception as e:
            return ValidationResponse(
                validation_id=validation.validation_id,
                check_type=validation.check_type,
                passed=False,
                message=f"Kali node validation error: {str(e)}"
            )

    async def validate_on_windows(self, validation: ValidationRequest) -> ValidationResponse:
        """Performs a validation assertion on the Windows node."""
        try:
            async with httpx.AsyncClient(timeout=float(validation.timeout + 5)) as client:
                resp = await client.post(f"{self.windows_url}/api/validate", json=validation.model_dump())
                resp.raise_for_status()
                return ValidationResponse(**resp.json())
        except Exception as e:
            return ValidationResponse(
                validation_id=validation.validation_id,
                check_type=validation.check_type,
                passed=False,
                message=f"Windows node validation error: {str(e)}"
            )

    async def set_kali_wifi_mode(self, mode: str = "monitor", interface: Optional[str] = None) -> Dict[str, Any]:
        """Switches Wi-Fi interface mode on Kali (e.g. monitor mode for packet injection/sniffing)."""
        req = WiFiModeRequest(interface=interface, mode=mode)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(f"{self.kali_url}/api/wifi/mode", json=req.model_dump())
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            return {"success": False, "error": f"Failed to reach Kali Wi-Fi daemon: {str(e)}"}

    async def transfer_file_to_kali(self, local_file_path: str) -> Dict[str, Any]:
        """Uploads a file from Windows to Kali storage."""
        fpath = Path(local_file_path)
        if not fpath.exists():
            raise FileNotFoundError(f"Local file '{local_file_path}' does not exist")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(fpath, "rb") as f:
                files = {"file": (fpath.name, f, "application/octet-stream")}
                resp = await client.post(f"{self.kali_url}/api/files/upload", files=files)
                resp.raise_for_status()
                return resp.json()

    async def transfer_file_to_windows(self, local_file_path: str) -> Dict[str, Any]:
        """Uploads a file from Kali to Windows storage."""
        fpath = Path(local_file_path)
        if not fpath.exists():
            raise FileNotFoundError(f"Local file '{local_file_path}' does not exist")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(fpath, "rb") as f:
                files = {"file": (fpath.name, f, "application/octet-stream")}
                resp = await client.post(f"{self.windows_url}/api/files/upload", files=files)
                resp.raise_for_status()
                return resp.json()
