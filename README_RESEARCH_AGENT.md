# 🔬 Autonomous Multimodal Deep Research Agent & Local Workspace

A 100% private, locally hosted AI research workspace powered by **Open WebUI**, **Ollama**, **Qwen 2.5-VL (7B)**, and **DeepSeek-R1 (7B)**.

---

## 🌟 Key Capabilities

1. **Autonomous Multi-Agent Deep Research Loop**:
   - **Planner Agent (`DeepSeek-R1 7B`)**: Decomposes complex topics into 3–5 targeted sub-questions.
   - **Parallel Scraper Agent (`DuckDuckGo + Trafilatura`)**: Gathers and extracts full clean text from 10–20 web sources concurrently without any API keys or paid subscriptions.
   - **Synthesizer Agent (`Qwen 2.5-VL 7B`)**: Aggregates evidence and compiles structured, comprehensive research dossiers with bracketed citations (`[1]`, `[2]`), comparison tables, and bibliography.
2. **Unrestricted Multimodal Vision (`Qwen 2.5-VL 7B`)**:
   - Drag & drop PDFs, architecture diagrams, data charts, and screenshots directly into the Web UI.
   - High-precision local OCR and unrestricted reasoning over visual data.
3. **Interactive Commenting & Dual-Pane Notes**:
   - One-click export research reports to the built-in rich Markdown Notes editor.
   - Highlight text, write inline annotations/margin comments, and ask direct follow-up questions to the model in the live sidebar drawer.
4. **Hardware Optimized for 16 GB RAM & 2 GB VRAM**:
   - Q4_K_M 4-bit quantization keeps total RAM footprint under **~4.8–5.2 GB**, preventing disk swapping and maximizing responsiveness.

---

## 🚀 Quick Start (One-Click)

Run the automated launcher script:

```bat
start_all_services.bat
```

Or via PowerShell:

```powershell
.\start_all_services.ps1
```

This will automatically:
1. Verify and start **Ollama** on `http://127.0.0.1:11434`.
2. Start the **Autonomous Deep Research Microservice** on `http://127.0.0.1:8001`.
3. Launch **Open WebUI** on `http://localhost:8080` and open your default browser.

---

## 📖 How to Use the Research Features

### 1. Running an Autonomous Multi-Agent Deep Research Query
1. Open [http://localhost:8080](http://localhost:8080).
2. In the model selector dropdown at the top, select **`autonomous-deep-research`** (or select `deep_research_pipe`).
3. Type any research topic (e.g. *"Solid state battery commercialization breakthroughs 2025"* or *"Comparison of local vector databases for embedded agents"*).
4. Watch the agent stream live progress:
   - 🧩 **Phase 1**: Research Planning & Query Decomposition
   - 🌐 **Phase 2**: Parallel Web Scraping across 10+ sources
   - ✍️ **Phase 3**: Synthesis of cited markdown dossier

### 2. Asking Direct Questions & Multimodal Vision Analysis
1. Select **`qwen2.5-vl:7b`** from the model dropdown.
2. Click the 📎 **Attach / Upload** button to upload images, PDFs, charts, or screenshots.
3. Ask specific questions about the documents (e.g. *"Extract all table data into JSON"*, *"Explain the mechanism in this diagram"*, *"Critique this methodology"*).

### 3. Making Comments & Annotating Research in Notes
1. On any generated research response, click the **Copy to Notes** or **Save** button.
2. Open the **Notes / Workspace** tab in Open WebUI.
3. Highlight any section to add your own comments, notes, or critique.
4. Use the sidebar chat to ask direct follow-up questions about highlighted paragraphs.

---

## 🛠️ Architecture & Port Mapping

| Service | Port | Endpoint | Role |
| :--- | :--- | :--- | :--- |
| **Open WebUI** | `8080` | `http://localhost:8080` | Modern responsive Web UI, Notes Workspace, Chat |
| **Research Microservice** | `8001` | `http://127.0.0.1:8001/v1` | Autonomous Multi-Agent Planner + Scraper + Synthesizer |
| **Local Ollama Engine** | `11434` | `http://127.0.0.1:11434` | Local Q4_K_M GGUF model execution (`qwen2.5-vl:7b`, `deepseek-r1:7b`) |
