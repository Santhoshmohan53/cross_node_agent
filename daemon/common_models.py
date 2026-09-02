from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field
import time
import uuid

class TaskRequest(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    command: str
    working_dir: Optional[str] = None
    timeout: int = 120
    shell_type: str = "default"  # "bash", "sh", "powershell", "cmd", "python"
    env_vars: Optional[Dict[str, str]] = None
    background: bool = False

class TaskResponse(BaseModel):
    task_id: str
    status: str  # "completed", "failed", "running", "timeout"
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: float = 0.0
    timestamp: float = Field(default_factory=time.time)

class ValidationRequest(BaseModel):
    validation_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    check_type: str  # "ping", "port_open", "http_status", "file_exists", "process_running", "regex_match", "custom_script"
    target: Optional[str] = None
    port: Optional[int] = None
    expected_status_code: Optional[int] = None
    file_path: Optional[str] = None
    process_name: Optional[str] = None
    pattern: Optional[str] = None
    custom_script: Optional[str] = None
    timeout: int = 30

class ValidationResponse(BaseModel):
    validation_id: str
    check_type: str
    passed: bool
    actual_value: Optional[Any] = None
    message: str = ""
    details: Optional[Dict[str, Any]] = None
    timestamp: float = Field(default_factory=time.time)

class SystemStatus(BaseModel):
    node_name: str
    os_name: str
    hostname: str
    status: str = "online"
    ip_addresses: Dict[str, str] = {}
    default_gateway: Optional[str] = None
    cpu_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_total_mb: float = 0.0
    memory_percent: float = 0.0
    disk_used_percent: float = 0.0
    wifi_info: Optional[Dict[str, Any]] = None  # { "interface": "wlan0", "mode": "monitor|managed", "ssid": "..." }
    uptime_seconds: float = 0.0
    timestamp: float = Field(default_factory=time.time)

class WiFiModeRequest(BaseModel):
    interface: Optional[str] = None
    mode: str = "monitor"  # "monitor" or "managed"
    channel: Optional[int] = None

class WorkflowStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    target_node: str  # "kali" or "windows"
    action_type: str  # "execute" or "validate"
    command: Optional[str] = None
    validation: Optional[ValidationRequest] = None
    continue_on_failure: bool = False

class WorkflowRequest(BaseModel):
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    description: Optional[str] = None
    steps: List[WorkflowStep] = []

class WorkflowResult(BaseModel):
    workflow_id: str
    name: str
    status: str  # "completed", "failed", "running"
    step_results: List[Dict[str, Any]] = []
    total_time_ms: float = 0.0
