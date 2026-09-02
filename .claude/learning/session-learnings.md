# Session Learnings & Architectural Invariants

### E-01 — Custom Frontend Pivot Anti-Pattern (Violation of Rule 03)
- **Date**: 2026-09-02
- **What Happened**: When tasked with delivering an interactive research & commenting workflow, the agent abandoned the production-grade Open WebUI setup (port 3000) and attempted to write a bespoke HTML/CSS/JS frontend (`web_ui/index.html` on port 5000) from scratch. This led to broken viewport scrollbars (`overflow: hidden`), lack of multi-turn conversational history, absence of prompt editing/branching, and immense user frustration.
- **Root Cause**: Premature custom UI generation rather than integrating the multi-agent loop as an OpenAI-compatible microservice (`/v1/chat/completions`) inside established top-tier UI repositories (Open WebUI).
- **Rule / Fix**: Always enforce Rule 03. Connect autonomous pipelines as standard OpenAI-compatible endpoints into Open WebUI (`http://127.0.0.1:8001/v1` -> Open WebUI port 3000). Use Open WebUI's native prompt editing, branching, multi-turn follow-ups, and Notes canvas.

### E-02 — Multi-Model Confusion & Routing Transparency
- **Date**: 2026-09-02
- **What Happened**: User was confused by having multiple local models (`deepseek-r1:7b` vs `llava:7b`) and having to manually switch between them.
- **Root Cause**: Exposing hardware-constrained model specializations (Reasoning vs Multimodal Vision) directly to the user without a unified agent interface.
- **Rule / Fix**: Package the research agent as a single unified entity (`autonomous-deep-research`) in the Open WebUI dropdown. The backend microservice automatically routes text research to the reasoning engine and vision tasks to the multimodal model transparently.
