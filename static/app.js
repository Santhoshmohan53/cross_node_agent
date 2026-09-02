// ==============================================================================
// AEGIS DUAL-NODE COMMAND CENTER JAVASCRIPT CONTROLLER
// ==============================================================================

const API_BASE = "";

// State tracking
let currentTopology = null;

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initTerminalListeners();
    initCopilot();
    initActionButtons();
    initFileHandlers();
    
    // Initial fetch and periodic polling
    fetchTopology();
    setInterval(fetchTopology, 3500);

    document.getElementById("btnRefresh").addEventListener("click", fetchTopology);
});

// ------------------------------------------------------------------------------
// 1. TOPOLOGY & STATUS MONITORING
// ------------------------------------------------------------------------------
async function fetchTopology() {
    try {
        const res = await fetch(`${API_BASE}/api/hub/topology`);
        if (!res.ok) throw new Error("Topology fetch failed");
        const data = await res.json();
        currentTopology = data;
        renderTopology(data);
    } catch (err) {
        console.warn("Topology update error:", err);
    }
}

function renderTopology(data) {
    // 1. Kali Node Render
    const kali = data.kali;
    const kaliPill = document.getElementById("kaliPill");
    const kaliDot = kaliPill.querySelector(".status-dot");
    const kaliLatency = document.getElementById("kaliLatency");
    const kaliBadge = document.getElementById("kaliStatusBadge");

    if (kali.reachable && kali.data.status === "online") {
        kaliDot.className = "status-dot online";
        kaliLatency.textContent = `${kali.latency_ms} ms`;
        kaliBadge.textContent = "ONLINE // READY";
        kaliBadge.className = "node-status-badge text-cyan";

        const d = kali.data;
        document.getElementById("kaliCpuVal").textContent = `${d.cpu_percent}%`;
        document.getElementById("kaliCpuBar").style.width = `${d.cpu_percent}%`;
        document.getElementById("kaliMemVal").textContent = `${d.memory_used_mb} / ${d.memory_total_mb} MB (${d.memory_percent}%)`;
        document.getElementById("kaliMemBar").style.width = `${d.memory_percent}%`;

        // Wi-Fi Info
        if (d.wifi_info) {
            document.getElementById("kaliWifiIface").textContent = d.wifi_info.interface || "wlan0";
            const modeEl = document.getElementById("kaliWifiMode");
            const mode = (d.wifi_info.mode || "MANAGED").toUpperCase();
            modeEl.textContent = mode;
            modeEl.className = mode.includes("MONITOR") ? "info-value badge-mode monitor" : "info-value badge-mode";
        }

        // IP Display
        const lanIp = d.ip_addresses.eth0 || d.ip_addresses.enp0s3 || Object.values(d.ip_addresses)[0] || "10.42.0.1";
        document.getElementById("kaliLanIp").textContent = lanIp;
    } else {
        kaliDot.className = "status-dot offline";
        kaliLatency.textContent = "OFFLINE";
        kaliBadge.textContent = "UNREACHABLE";
        kaliBadge.className = "node-status-badge text-red";
    }

    // 2. Windows Node Render
    const win = data.windows;
    const winPill = document.getElementById("winPill");
    const winDot = winPill.querySelector(".status-dot");
    const winLatency = document.getElementById("winLatency");
    const winBadge = document.getElementById("winStatusBadge");

    if (win.reachable && win.data.status === "online") {
        winDot.className = "status-dot online";
        winLatency.textContent = `${win.latency_ms} ms`;
        winBadge.textContent = "ONLINE // READY";
        winBadge.className = "node-status-badge text-green";

        const wd = win.data;
        document.getElementById("winCpuVal").textContent = `${wd.cpu_percent}%`;
        document.getElementById("winCpuBar").style.width = `${wd.cpu_percent}%`;
        document.getElementById("winMemVal").textContent = `${wd.memory_used_mb} / ${wd.memory_total_mb} MB (${wd.memory_percent}%)`;
        document.getElementById("winMemBar").style.width = `${wd.memory_percent}%`;

        const winIp = Object.values(wd.ip_addresses)[0] || "10.42.0.x";
        document.getElementById("winClientIp").textContent = winIp;
        document.getElementById("winGateway").textContent = wd.default_gateway || "10.42.0.1";
    } else {
        winDot.className = "status-dot offline";
        winLatency.textContent = "OFFLINE";
        winBadge.textContent = "UNREACHABLE";
        winBadge.className = "node-status-badge text-red";
    }
}

// ------------------------------------------------------------------------------
// 2. TAB CONTROLS
// ------------------------------------------------------------------------------
function initTabs() {
    const tabs = document.querySelectorAll(".tab-btn");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

            tab.classList.add("active");
            const targetId = tab.getAttribute("data-tab");
            document.getElementById(targetId).classList.add("active");
        });
    });
}

// ------------------------------------------------------------------------------
// 3. DUAL TERMINAL SYSTEM
// ------------------------------------------------------------------------------
function initTerminalListeners() {
    // Kali Terminal
    const kaliInput = document.getElementById("kaliTermInput");
    const btnSendKali = document.getElementById("btnSendKali");
    const btnClearKali = document.getElementById("btnClearKaliTerm");

    const execKali = async () => {
        const cmd = kaliInput.value.trim();
        if (!cmd) return;
        appendTermLine("kaliTermOutput", `kali@root:~# ${cmd}`, "cmd");
        kaliInput.value = "";

        try {
            const res = await fetch(`${API_BASE}/api/hub/execute?node=kali`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ command: cmd, timeout: 60 })
            });
            const data = await res.json();
            if (data.stdout) appendTermLine("kaliTermOutput", data.stdout, "stdout");
            if (data.stderr) appendTermLine("kaliTermOutput", data.stderr, "stderr");
            if (!data.stdout && !data.stderr) appendTermLine("kaliTermOutput", `[Exit Code: ${data.exit_code}]`, "sys");
        } catch (err) {
            appendTermLine("kaliTermOutput", `Error executing on Kali: ${err.message}`, "stderr");
        }
    };

    btnSendKali.addEventListener("click", execKali);
    kaliInput.addEventListener("keydown", (e) => { if (e.key === "Enter") execKali(); });
    btnClearKali.addEventListener("click", () => {
        document.getElementById("kaliTermOutput").innerHTML = '<div class="term-line sys">Kali terminal buffer cleared.</div>';
    });

    // Windows Terminal
    const winInput = document.getElementById("winTermInput");
    const btnSendWin = document.getElementById("btnSendWin");
    const btnClearWin = document.getElementById("btnClearWinTerm");

    const execWin = async () => {
        const cmd = winInput.value.trim();
        if (!cmd) return;
        appendTermLine("winTermOutput", `PS C:\\> ${cmd}`, "cmd");
        winInput.value = "";

        try {
            const res = await fetch(`${API_BASE}/api/hub/execute?node=windows`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ command: cmd, timeout: 60, shell_type: "powershell" })
            });
            const data = await res.json();
            if (data.stdout) appendTermLine("winTermOutput", data.stdout, "stdout");
            if (data.stderr) appendTermLine("winTermOutput", data.stderr, "stderr");
            if (!data.stdout && !data.stderr) appendTermLine("winTermOutput", `[Exit Code: ${data.exit_code}]`, "sys");
        } catch (err) {
            appendTermLine("winTermOutput", `Error executing on Windows: ${err.message}`, "stderr");
        }
    };

    btnSendWin.addEventListener("click", execWin);
    winInput.addEventListener("keydown", (e) => { if (e.key === "Enter") execWin(); });
    btnClearWin.addEventListener("click", () => {
        document.getElementById("winTermOutput").innerHTML = '<div class="term-line sys">Windows terminal buffer cleared.</div>';
    });
}

function appendTermLine(containerId, text, type) {
    const container = document.getElementById(containerId);
    const line = document.createElement("div");
    line.className = `term-line ${type}`;
    line.textContent = text;
    container.appendChild(line);
    container.scrollTop = container.scrollHeight;
}

// ------------------------------------------------------------------------------
// 4. QUICK ACTION SHORTCUTS
// ------------------------------------------------------------------------------
function initActionButtons() {
    // Kali: Toggle Monitor Mode
    document.getElementById("btnToggleMonitor").addEventListener("click", async () => {
        const curMode = document.getElementById("kaliWifiMode").textContent.trim();
        const nextMode = curMode.includes("MONITOR") ? "managed" : "monitor";
        appendTermLine("kaliTermOutput", `[AEGIS] Switching Wi-Fi adapter mode to '${nextMode}'...`, "sys");

        try {
            const res = await fetch(`${API_BASE}/api/hub/execute?node=kali`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ command: `sudo airmon-ng ${nextMode === 'monitor' ? 'start' : 'stop'} wlan0`, timeout: 30 })
            });
            const data = await res.json();
            appendTermLine("kaliTermOutput", data.stdout || data.stderr || "Mode switch triggered", "stdout");
            fetchTopology();
        } catch (err) {
            appendTermLine("kaliTermOutput", `Failed to switch mode: ${err.message}`, "stderr");
        }
    });

    // Kali: Quick Recon
    document.getElementById("btnKaliQuickRecon").addEventListener("click", async () => {
        appendTermLine("kaliTermOutput", `kali@root:~# nmap -F 10.42.0.1`, "cmd");
        try {
            const res = await fetch(`${API_BASE}/api/hub/execute?node=kali`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ command: "nmap -F 10.42.0.1", timeout: 60 })
            });
            const data = await res.json();
            appendTermLine("kaliTermOutput", data.stdout || data.stderr, "stdout");
        } catch (err) {
            appendTermLine("kaliTermOutput", `Recon error: ${err.message}`, "stderr");
        }
    });

    // Windows: Test Kali Gateway Route
    document.getElementById("btnWinTestRoute").addEventListener("click", async () => {
        appendTermLine("winTermOutput", `PS C:\\> Test-Connection 10.42.0.1 -Count 2`, "cmd");
        try {
            const res = await fetch(`${API_BASE}/api/hub/execute?node=windows`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ command: "Test-Connection 10.42.0.1 -Count 2", timeout: 30 })
            });
            const data = await res.json();
            appendTermLine("winTermOutput", data.stdout || data.stderr, "stdout");
        } catch (err) {
            appendTermLine("winTermOutput", `Route test error: ${err.message}`, "stderr");
        }
    });

    // Windows: Validate DNS
    document.getElementById("btnWinValidateDns").addEventListener("click", async () => {
        appendTermLine("winTermOutput", `PS C:\\> Resolve-DnsName google.com`, "cmd");
        try {
            const res = await fetch(`${API_BASE}/api/hub/execute?node=windows`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ command: "Resolve-DnsName google.com", timeout: 30 })
            });
            const data = await res.json();
            appendTermLine("winTermOutput", data.stdout || data.stderr, "stdout");
        } catch (err) {
            appendTermLine("winTermOutput", `DNS validation error: ${err.message}`, "stderr");
        }
    });
}

// ------------------------------------------------------------------------------
// 5. AI AGENT COPILOT DISPATCHER
// ------------------------------------------------------------------------------
function initCopilot() {
    const input = document.getElementById("agentPromptInput");
    const btn = document.getElementById("btnDispatchAgent");

    const dispatch = async () => {
        const prompt = input.value.trim();
        if (!prompt) return;

        const resultsBox = document.getElementById("copilotResults");
        const container = document.getElementById("planStepsContainer");
        const badge = document.getElementById("copilotStatus");
        const summary = document.getElementById("copilotSummary");

        resultsBox.style.display = "block";
        badge.textContent = "ORCHESTRATING...";
        badge.className = "badge";
        summary.textContent = `Dispatching Goal: "${prompt}"`;
        container.innerHTML = `<div class="term-line sys">Analyzing intent and routing subtasks across Kali Linux and Windows nodes...</div>`;

        try {
            const res = await fetch(`${API_BASE}/api/hub/agent/orchestrate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt })
            });
            const data = await res.json();
            badge.textContent = "COMPLETED";
            badge.className = "badge badge-win";
            summary.textContent = data.summary;

            container.innerHTML = "";
            data.plan_steps.forEach((step, idx) => {
                const item = document.createElement("div");
                item.className = "plan-step-item";
                item.innerHTML = `
                    <div class="plan-step-title">
                        <span><strong>Step ${idx + 1}:</strong> [${step.node}] ${step.action}</span>
                        <span class="badge ${step.status === 'completed' || step.status === 'passed' ? 'badge-win' : 'badge-kali'}">${step.status.toUpperCase()}</span>
                    </div>
                    <div class="plan-step-out">${escapeHtml(step.output || '(No output)')}</div>
                `;
                container.appendChild(item);
            });
        } catch (err) {
            badge.textContent = "FAILED";
            badge.className = "badge text-red";
            container.innerHTML = `<div class="term-line stderr">Orchestration Error: ${err.message}</div>`;
        }
    };

    btn.addEventListener("click", dispatch);
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") dispatch(); });
}

// ------------------------------------------------------------------------------
// 6. WORKFLOW PRESET RUNNER
// ------------------------------------------------------------------------------
window.triggerPresetWorkflow = async function(presetName) {
    const wfBox = document.getElementById("wfOutputBox");
    const wfTitle = document.getElementById("wfTitle");
    const wfBadge = document.getElementById("wfBadge");
    const wfTimeline = document.getElementById("wfTimeline");

    wfBox.style.display = "block";
    wfBadge.textContent = "RUNNING";
    wfBadge.className = "badge";
    wfTimeline.innerHTML = '<div class="term-line sys">Initiating multi-node playbook execution...</div>';

    let workflowPayload = null;

    if (presetName === "recon_validation") {
        wfTitle.textContent = "Full Gateway Recon & Windows Client Validation";
        workflowPayload = {
            name: "Gateway Recon & Validation",
            steps: [
                {
                    name: "Port Recon on Gateway",
                    target_node: "kali",
                    action_type: "execute",
                    command: "nmap -F 10.42.0.1"
                },
                {
                    name: "Windows Reachability Verification",
                    target_node: "windows",
                    action_type: "validate",
                    validation: { check_type: "ping", target: "10.42.0.1" }
                },
                {
                    name: "Windows Internet DNS Verification",
                    target_node: "windows",
                    action_type: "validate",
                    validation: { check_type: "custom_script", custom_script: "Resolve-DnsName google.com | Select-Object -First 1" }
                }
            ]
        };
    } else if (presetName === "wifi_sniff_validate") {
        wfTitle.textContent = "Wi-Fi Monitor Mode Sniff & Windows Route Verification";
        workflowPayload = {
            name: "Wi-Fi Monitor & Route Validation",
            steps: [
                {
                    name: "Toggle Kali Wi-Fi Monitor Mode",
                    target_node: "kali",
                    action_type: "execute",
                    command: "sudo airmon-ng start wlan0 || iw dev"
                },
                {
                    name: "Windows LAN Keepalive Test",
                    target_node: "windows",
                    action_type: "validate",
                    validation: { check_type: "ping", target: "10.42.0.1" }
                }
            ]
        };
    }

    try {
        const res = await fetch(`${API_BASE}/api/hub/workflow/run`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(workflowPayload)
        });
        const data = await res.json();
        wfBadge.textContent = data.status.toUpperCase();
        wfBadge.className = data.status === "completed" ? "badge badge-win" : "badge text-red";

        wfTimeline.innerHTML = "";
        data.step_results.forEach((s, idx) => {
            const stepEl = document.createElement("div");
            stepEl.className = "plan-step-item";
            const outText = s.details ? JSON.stringify(s.details, null, 2) : "Passed";
            stepEl.innerHTML = `
                <div class="plan-step-title">
                    <span><strong>Step ${idx + 1}:</strong> [${s.target_node.toUpperCase()}] ${s.name} (${s.duration_ms} ms)</span>
                    <span class="badge ${s.passed ? 'badge-win' : 'badge-kali'}">${s.passed ? 'PASSED' : 'FAILED'}</span>
                </div>
                <div class="plan-step-out">${escapeHtml(outText)}</div>
            `;
            wfTimeline.appendChild(stepEl);
        });
    } catch (err) {
        wfBadge.textContent = "ERROR";
        wfTimeline.innerHTML = `<div class="term-line stderr">Playbook failed: ${err.message}</div>`;
    }
};

// ------------------------------------------------------------------------------
// 7. FILE & ARTIFACT TRANSFERS
// ------------------------------------------------------------------------------
function initFileHandlers() {
    const btnUpload = document.getElementById("btnUploadKali");
    const fileInput = document.getElementById("fileKaliUpload");

    btnUpload.addEventListener("click", async () => {
        if (!fileInput.files || fileInput.files.length === 0) {
            alert("Please select a file to upload first.");
            return;
        }
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append("file", file);

        appendTermLine("kaliTermOutput", `[AEGIS] Uploading '${file.name}' (${file.size} bytes) to Kali...`, "sys");
        try {
            const res = await fetch("http://10.42.0.1:8765/api/files/upload", {
                method: "POST",
                body: formData
            });
            const data = await res.json();
            appendTermLine("kaliTermOutput", `File saved on Kali at: ${data.saved_path}`, "stdout");
            alert(`File successfully pushed to Kali: ${data.saved_path}`);
        } catch (err) {
            appendTermLine("kaliTermOutput", `Upload failed: ${err.message}`, "stderr");
        }
    });

    const btnDownload = document.getElementById("btnDownloadKali");
    const downloadInput = document.getElementById("kaliDownloadPath");

    btnDownload.addEventListener("click", () => {
        const path = downloadInput.value.trim();
        if (!path) {
            alert("Please enter a valid Kali file path to download.");
            return;
        }
        const downloadUrl = `http://10.42.0.1:8765/api/files/download?path=${encodeURIComponent(path)}`;
        window.open(downloadUrl, "_blank");
    });
}

function escapeHtml(str) {
    if (typeof str !== "string") str = String(str);
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
