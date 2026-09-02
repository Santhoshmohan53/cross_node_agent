#!/usr/bin/env python3
"""
Aegis Cross-Node System Integration Tests
Validates daemon endpoints, models, agent bridge, and hub orchestrator.
"""

import sys
import unittest
import asyncio
from pathlib import Path

# Ensure paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "daemon"))
sys.path.insert(0, str(PROJECT_ROOT))

from common_models import (
    TaskRequest, TaskResponse, ValidationRequest, ValidationResponse,
    SystemStatus, WorkflowStep, WorkflowRequest
)
from windows_daemon import app as win_app
from hub_server import app as hub_app
from agent_bridge import AgentBridge
from fastapi.testclient import TestClient

class TestCrossNodeArchitecture(unittest.TestCase):

    def setUp(self):
        self.win_client = TestClient(win_app)
        self.hub_client = TestClient(hub_app)

    def test_01_pydantic_models(self):
        """Verify model instantiation and serialization."""
        task = TaskRequest(command="echo 'test'")
        self.assertEqual(task.command, "echo 'test'")
        self.assertEqual(task.shell_type, "default")
        
        val = ValidationRequest(check_type="port_open", target="127.0.0.1", port=8080)
        self.assertEqual(val.check_type, "port_open")
        self.assertEqual(val.port, 8080)

    def test_02_windows_daemon_status(self):
        """Test Windows daemon status endpoint."""
        resp = self.win_client.get("/api/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["node_name"], "Windows Host PC")
        self.assertIn("cpu_percent", data)
        self.assertIn("memory_percent", data)

    def test_03_windows_daemon_execution(self):
        """Test Windows daemon executing a PowerShell task."""
        req = TaskRequest(command="Write-Output 'AEGIS_ACTIVE'", shell_type="powershell")
        resp = self.win_client.post("/api/execute", json=req.model_dump())
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "completed")
        self.assertIn("AEGIS_ACTIVE", data["stdout"])

    def test_04_windows_daemon_validation(self):
        """Test Windows daemon validation engine."""
        val = ValidationRequest(check_type="custom_script", custom_script="Write-Output 'passed'; exit 0")
        resp = self.win_client.post("/api/validate", json=val.model_dump())
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["passed"])

    def test_05_hub_topology_endpoint(self):
        """Test Hub topology aggregator."""
        resp = self.hub_client.get("/api/hub/topology")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("kali", data)
        self.assertIn("windows", data)
        self.assertIn("endpoints", data)

    def test_06_hub_static_dashboard(self):
        """Test Hub serving index.html dashboard."""
        resp = self.hub_client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("AEGIS", resp.text)
        self.assertIn("Kali Linux", resp.text)

if __name__ == "__main__":
    unittest.main()
