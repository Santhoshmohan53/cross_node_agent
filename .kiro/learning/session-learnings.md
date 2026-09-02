# Session Learnings & Architectural Invariants

## Invariants & Conventions

### E-01 — Hostname Casing Invariant (Kali Linux Node)
* **Date:** 2026-08-23
* **Pattern/Issue:** In Deskflow, Barrier, SSH, and network automation, using capitalized `Ghost` instead of lowercase `ghost` caused client connection rejections (`a client with name Ghost is already connected` or hostname alias mismatches).
* **Rule/Fix:** The Linux system hostname and user on the Mini PC is strictly lowercase **`ghost`** (`hostnamectl set-hostname ghost`). All Deskflow/Barrier screen definitions, alias mappings, configuration files, and SSH scripts must ALWAYS use lowercase **`ghost`**. Never use capitalized `Ghost`.
