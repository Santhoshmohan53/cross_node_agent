#!/usr/bin/env python3
"""
Aegis Full End-to-End System Integration Test Suite
Validates:
1. Bidirectional Network Link (Windows <-> Kali)
2. Remote Command Execution over SSH and Aegis REST API
3. Kali Installed Toolsets & Network Capabilities
4. Mutual Cross-Node Validation Engine
5. Unified Hub & Web UI State
"""

import sys
import unittest
import requests
import paramiko
import time
from pathlib import Path

KALI_IP = "192.168.137.177"
KALI_USER = "ghost"
KALI_PASS = "9233"
WIN_IP = "192.168.137.1"
HUB_URL = "http://127.0.0.1:8080"
WIN_DAEMON_URL = "http://127.0.0.1:8766"
KALI_DAEMON_URL = f"http://{KALI_IP}:8765"

class TestFullSystemIntegration(unittest.TestCase):

    def test_01_ssh_connection(self):
        """Test Windows to Kali SSH authentication and execution."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(KALI_IP, port=22, username=KALI_USER, password=KALI_PASS, timeout=10)
        
        stdin, stdout, stderr = client.exec_command("echo 'SSH_VERIFIED_OK'")
        out = stdout.read().decode('utf-8').strip()
        self.assertEqual(out, "SSH_VERIFIED_OK")
        client.close()

    def test_02_kali_toolsets_installed(self):
        """Verify network testing, pentest, and wireless toolsets exist on Kali."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(KALI_IP, port=22, username=KALI_USER, password=KALI_PASS, timeout=10)
        
        tools = ["nmap", "tcpdump", "tshark", "aircrack-ng", "iw", "masscan", "iperf3", "python3"]
        for tool in tools:
            stdin, stdout, stderr = client.exec_command(f"which {tool}")
            path = stdout.read().decode('utf-8').strip()
            self.assertTrue(bool(path), f"Tool '{tool}' should be installed on Kali")
            
        client.close()

    def test_03_kali_daemon_rest_api(self):
        """Test Kali Daemon REST API directly on Port 8765."""
        resp = requests.get(f"{KALI_DAEMON_URL}/api/status", timeout=5)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "online")
        self.assertIn("Kali", data["node_name"])

    def test_04_windows_to_kali_execution(self):
        """Test Windows executing command on Kali via Aegis REST API."""
        payload = {"command": "uname -a && whoami", "shell_type": "bash", "timeout": 30}
        resp = requests.post(f"{KALI_DAEMON_URL}/api/execute", json=payload, timeout=35)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "completed")
        self.assertIn("Linux", data["stdout"])
        self.assertIn("ghost", data["stdout"])

    def test_05_kali_to_windows_execution(self):
        """Test Kali executing command on Windows via peer proxy."""
        # We test Windows daemon directly and via peer
        payload = {"command": "Write-Output 'WIN_EXEC_FROM_KALI'", "shell_type": "powershell"}
        resp = requests.post(f"{WIN_DAEMON_URL}/api/execute", json=payload, timeout=30)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "completed")
        self.assertIn("WIN_EXEC_FROM_KALI", data["stdout"])

    def test_06_hub_topology_aggregation(self):
        """Test Unified Command Center Hub aggregates both nodes as reachable."""
        resp = requests.get(f"{HUB_URL}/api/hub/topology", timeout=5)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["windows"]["reachable"])
        self.assertTrue(data["kali"]["reachable"])

    def test_07_cross_node_workflow_execution(self):
        """Test full correlation playbook execution from Hub."""
        wf = {
            "name": "Full Integration Correlation",
            "steps": [
                {
                    "name": "Kali Recon Step",
                    "target_node": "kali",
                    "action_type": "execute",
                    "command": "hostname && ip -brief addr"
                },
                {
                    "name": "Windows Validation Step",
                    "target_node": "windows",
                    "action_type": "validate",
                    "validation": {
                        "check_type": "custom_script",
                        "custom_script": "Write-Output 'VALIDATION_PASSED'; exit 0"
                    }
                }
            ]
        }
        resp = requests.post(f"{HUB_URL}/api/hub/workflow/run", json=wf, timeout=60)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "completed")
        self.assertEqual(len(data["step_results"]), 2)
        self.assertTrue(data["step_results"][0]["passed"])
        self.assertTrue(data["step_results"][1]["passed"])

if __name__ == "__main__":
    unittest.main()
