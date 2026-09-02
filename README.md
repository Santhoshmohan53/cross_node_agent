# 🌐 Cross-Node Agent Mesh & Autonomous Multimodal Deep Research

An end-to-end, privacy-preserving AI orchestration ecosystem integrating:
1. **Autonomous Multimodal Deep Research Agent**: An OpenAI-compatible multi-agent service running locally with vision ingestion, planning, parallel web intelligence gathering, structured synthesis, and instant memory offload.
2. **Cross-Node Mesh Infrastructure**: Secure KVM and input multiplexing connecting Windows workstation and Kali Linux nodes over Tailscale and Deskflow / Barrier.
3. **Open WebUI Workspace**: Production web interface with canvas notes, conversation branching, and tool compatibility.

---

## 🌟 Architecture Overview

```
                                  [ User Browser ]
                                         │
                                         ▼ (Port 3000)
                              ┌─────────────────────┐
                              │     Open WebUI      │
                              └──────────┬──────────┘
                                         │ OpenAI /v1 API
                                         ▼ (Port 8001)
                         ┌───────────────────────────────┐
                         │ Autonomous Deep Research Pipe │
                         └───────────────┬───────────────┘
                                         │
            ┌────────────────────────────┼────────────────────────────┐
            ▼                            ▼                            ▼
  [ Phase 0: Vision Agent ]    [ Phase 1: Planner Agent ]   [ Phase 2: Parallel Scraper ]
         (llava:7b)                 (deepseek-r1:7b)             (DuckDuckGo/Mojeek/Yahoo)
  Resolves image previews,     Decomposes query into        Fetches & extracts text from
  OCR text & table layouts     3-5 targeted sub-questions   live sources with citations
            │                            │                            │
            └────────────────────────────┼────────────────────────────┘
                                         │
                                         ▼
                            [ Phase 3: Synthesizer Agent ]
                                   (deepseek-r1:7b)
                            Compiles cited markdown dossier
                                         │
                                         ▼
                            [ Instant Memory Offload ]
                              (keep_alive: 0 to Ollama)
                             Evicts model weights from RAM
```

---

## 🚀 Key Features

### 1. Multimodal Deep Research Pipeline
- **Phase 0 (Vision Ingestion)**: Native support for images, tables, diagrams, and OCR via local vision models (`llava:7b`). Automatically resolves disk-uploaded files and base64 strings.
- **Phase 1 (Planning)**: Automatic query decomposition using reasoning models (`deepseek-r1:7b`).
- **Phase 2 (Parallel Scraping)**: Concurrent web scraping across multiple search engines with zero API keys required.
- **Phase 3 (Synthesis)**: Formats verified sources, live highlights, and comprehensive analytical breakdowns with bracketed citations.
- **Dynamic Memory Offload**: Directly signals Ollama with `keep_alive: 0` immediately upon completion, returning **5.4 GB of RAM** back to the OS.

### 2. Open WebUI Compatibility Layer
- Patched Ollama router to preemptively strip `tools` parameters for vision models that do not support tool calling (preventing `does not support tools` errors).
- Fast-path handler for background utility tasks (title, tags, and follow-up prompts) to prevent GPU/CPU saturation.

### 3. Cross-Node Hardware Mesh
- Bi-directional keyboard/mouse sharing between Windows host and remote Linux machines (Kali) using Deskflow / Barrier.
- Tailscale mesh routing and automated service orchestration.

---

## 🛠️ Port & Service Configuration

| Service | Address | Role |
| :--- | :--- | :--- |
| **Open WebUI** | `http://localhost:3000` | Chat interface, notes workspace, conversation trees |
| **Deep Research Service** | `http://127.0.0.1:8001` | Multi-agent research microservice (`/v1/chat/completions`) |
| **Ollama Local Engine** | `http://127.0.0.1:11434` | Local model backend (`llava:7b`, `deepseek-r1:7b`) |

---

## 📦 Quick Start

### 1. Launch All Services (Windows)
```cmd
start_all_services.bat
```
Or via PowerShell:
```powershell
.\start_all_services.ps1
```

### 2. Running Automated Tests
```powershell
pytest tests/
```

---

## 📄 License
MIT License.
