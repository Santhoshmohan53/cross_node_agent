---
name: scavenger-hunt
description: Eliminate exploratory thrashing and aimless codebase wandering. Systematically discovers entry points, architectural boundaries, living tests, dependency graphs, and active configurations before writing or modifying code. Use when onboarding onto an unfamiliar codebase, starting a new complex feature, investigating cross-module bugs, or locating dispersed configuration patterns.
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# Scavenger Hunt Elimination Protocol

When navigating an unfamiliar repository or debugging a complex multi-file issue, AI agents often fall into the **"Scavenger Hunt" anti-pattern**—aimlessly opening files, reading irrelevant directories, guessing file locations, and exhausting token context on trial-and-error discovery.

This skill enforces an **efficient, hypothesis-driven discovery protocol** that maps repository architecture in minimum turns.

---

## 1. The 4-Phase Systematic Discovery Protocol

```
Phase 1: Perimeter Recon  -> Check manifests, root configs, active scripts, and entry points
Phase 2: Targeted Index   -> Use ripgrep / glob with precise symbol queries (never linear reading)
Phase 3: Living Contracts -> Locate test suites, schemas, and runnable examples
Phase 4: Context Anchor   -> Synthesize an unambiguous 5-line brief before making changes
```

---

### Phase 1: Perimeter Reconnaissance (Root & Topology)

Never guess how a project is structured. Discover the ground truth in 1–2 tool calls:

1. **Project Root Manifests**:
   - Node: `package.json`, `pnpm-workspace.yaml`, `tsconfig.json`
   - Python: `pyproject.toml`, `setup.py`, `requirements.txt`
   - Rust: `Cargo.toml`, `Cargo.lock`
   - Go: `go.mod`
   - Polyglot / Agent: `.agents/`, `.gemini/`, `.github/workflows/`
2. **Determine Active Entry Points**:
   - Inspect build scripts (`scripts` in `package.json`, `Makefile`, `taskfile.yml`, `run.py`).
   - Identify main processes and daemon entry points (`src/index.ts`, `main.py`, `cmd/main.go`).

---

### Phase 2: Targeted Grep & Symbol Indexing

Never read full files sequentially to find where something is defined or handled.

- **Exact Symbol Search**: Use `grep_search` with exact function/class/interface names.
- **Pattern Matching**: Search for route definitions, event listeners, or dependency injection tokens:
  - Express/FastAPI: `@app.get`, `router.get`, `app.use`
  - React/UI: `export const`, `function [A-Z]`, `createSlice`, `useContext`
  - Database: `model`, `Schema`, `Entity`, `CREATE TABLE`
- **Restrict Scope**: Use `Includes` globs (e.g. `*.ts`, `src/**`) to avoid searching build artifacts, `.git`, or `node_modules`.

---

### Phase 3: Living Contracts & Test Discovery

Documentation can be stale. The truest specifications in any codebase are **tests, type definitions, and mocks**:

1. **Locate Test Harnesses**:
   - Find relevant test files (`*.test.ts`, `*_test.py`, `tests/`, `spec/`).
   - Read test fixtures to see realistic input payloads and expected outputs.
2. **Inspect Type Definitions & Interfaces**:
   - Check `types.ts`, `models.py`, `interfaces/`, or OpenAPI/GraphQL schemas.
   - Ground all new function signatures in existing type contracts.

---

### Phase 4: The Consolidated Context Anchor

Before writing or editing code, formulate a brief mental (or written) anchor:

```markdown
### Codebase Recon Brief:
- **Architecture**: [e.g., Next.js 14 App Router + Tailwind + SQLite / Prisma]
- **Target File(s)**: [Exact path(s) identified]
- **Existing Reusable Utilities**: [Path to utility or component]
- **Verification Harness**: [Command to run relevant tests, e.g., `npm test -- path/to/test`]
```

---

## 2. Anti-Patterns to Strictly Avoid

| Anti-Pattern | Bad Behavior | Correct Protocol |
|---|---|---|
| **Directory Strolling** | Calling `list_dir` on every nested folder recursively. | Check root configs, then grep for specific symbol or filename. |
| **Bulk Reading** | Viewing 500 lines of multiple files hoping to find a clue. | Search with `grep_search` (MatchPerLine: true), slice view only the matching function. |
| **Guess-and-Check Imports** | Creating new import paths without checking tsconfig paths or module aliases. | Inspect `tsconfig.json` (`paths`), `vite.config.ts`, or `sys.path`. |
| **Ignoring Existing Patterns** | Inventing custom error formats or logger setups when one already exists. | Grep for existing logger/error handlers and match their style. |

---

## 3. Checklist for Pre-Flight Exploration

- [ ] Identified package manager and build tool.
- [ ] Confirmed root path aliases (`@/`, `~`, `src/`).
- [ ] Located existing test suite and verification command.
- [ ] Checked for project-specific conventions (`.agents/rules/`, `CONTRIBUTING.md`, `linter configs`).
- [ ] Narrowed target edit down to exact file and line ranges.
