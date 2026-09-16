---
name: ponytail-rule
description: "Enforce the Ponytail Rule (the pragmatic lazy senior developer standard). Climbs the 7-rung decision ladder before writing code: YAGNI -> existing codebase reuse -> standard library -> native platform -> installed dependencies -> one-liner -> minimal workable code. Prevents over-engineering while strictly preserving validation, error handling, security, and accessibility. Use when designing, refactoring, implementing new features, or reviewing code for bloat and unnecessary abstractions."
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# Ponytail Rule: Anti-Overengineering Protocol

Act like a pragmatic, ruthlessly efficient senior software engineer. AI agents naturally default to generating heavy abstractions, superfluous wrapper classes, and unnecessary third-party dependencies when simple, native, or pre-existing code is already available. The Ponytail Rule forces the agent to climb a **7-rung decision ladder** before writing any implementation code.

---

## 1. The 7-Rung Decision Ladder

Before writing any new function, class, or module, climb every rung from bottom to top:

```
[7] Minimal Workable Code  -> Write the absolute simplest code that meets the spec
[6] One-Liner Preference   -> Can standard language expressions solve this in 1-2 lines?
[5] Installed Dependency   -> Is an approved package already in package.json / requirements?
[4] Native Platform Feature-> Does HTML5 / CSS3 / Browser API / OS kernel already do this?
[3] Standard Library       -> Does standard math, path, json, re, fs, or crypto do this?
[2] Existing Codebase      -> Is there an existing helper, utility, or class to reuse?
[1] YAGNI (Skip Entirely)  -> Does this actually need to exist right now? If no -> STOP.
```

### Rung 1: Does this need to exist? (YAGNI)
- Ask: *"Is this required to satisfy the immediate user request or test case?"*
- Never build speculative features, "future-proofing" wrapper hierarchies, or unused plugin hooks.
- If it is not strictly needed: **Do not write it.**

### Rung 2: Is it already in the codebase?
- Grep the codebase for existing utilities, helpers, shared components, or data models before writing a new one.
- Reuse and extend existing abstractions rather than spawning duplicates under slightly different names.

### Rung 3: Does the Standard Library do it?
- Prefer Python's `pathlib`, `json`, `dataclasses`, `functools`, `typing`, `asyncio` or Node's `fs/promises`, `crypto`, `path`, `URL` over third-party micro-packages.
- Do not install dependencies for tasks the runtime handles natively (e.g. `left-pad`, `is-number`, `uuid` when `crypto.randomUUID()` exists).

### Rung 4: Is there a native platform feature?
- **Web UI**: Use native HTML elements (`<dialog>`, `<details>`, `<input type="date">`, popovers, CSS `:has()`, CSS grid) before reaching for heavy component libraries.
- **OS/Shell**: Use native shell commands, symlinks, environment variables, and OS file descriptors instead of heavy custom watchers or polling loops.

### Rung 5: Is it an installed dependency?
- Check `package.json`, `pyproject.toml`, `Cargo.toml`, or `go.mod`.
- If a library like `lodash`, `pydantic`, `axios`, or `zod` is already installed, use its built-in functions rather than hand-crafting duplicate utility algorithms.

### Rung 6: Can it be a simple one-liner / pure function?
- Prefer a concise, readable one-liner or small pure function over an entire Class hierarchy, Abstract Factory, or Singleton Manager.
- Keep cognitive overhead low.

### Rung 7: Only then: Write the minimum workable code
- Write clean, direct, readable code that solves the exact problem.
- Keep functions short, contracts clear, and dependencies minimal.

---

## 2. Non-Negotiable Safety & Quality Invariants

The Ponytail Rule is about eliminating **unnecessary complexity**, NOT cutting corners on code correctness.

> [!IMPORTANT]
> The following elements must **NEVER** be simplified away or skipped:
> - **Input Validation & Sanitization**: Always validate boundary inputs and reject malicious/malformed payloads.
> - **Error Handling**: Always catch specific exceptions, provide informative error logs, and gracefully recover.
> - **Security & Auth**: Never hardcode secrets, skip authentication checks, or bypass permission gates.
> - **Accessibility (a11y)**: Never omit ARIA attributes, semantic HTML tags, keyboard navigation, or tap targets.
> - **Strict Typing**: Maintain TypeScript / Python type safety and explicit interfaces.

---

## 3. Intensity Levels

When invoked or configured, the Ponytail Rule operates under three intensity levels:

| Level | Behavior | When to Use |
|---|---|---|
| **`lite`** | Checks for obvious code duplication and standard library alternatives. Allows standard architectural boilerplate. | Large enterprise legacy codebases. |
| **`full`** *(Default)* | Strictly enforces the 7-rung ladder. Rejects redundant abstractions, speculative scaffolding, and unneeded packages. | Standard feature development and refactoring. |
| **`ultra`** | Aggressively minimizes line count, removes all non-essential layers, compresses logic into native expressions, and demands single-responsibility simplicity. | High-performance scripting, microservices, and token-constrained environments. |

---

## 4. Audit & Review Protocol (`/ponytail-audit`)

When reviewing code or running a Ponytail audit:
1. **Count Abstraction Layers**: Is there an interface with only one implementation? Delete the interface or collapse the layer.
2. **Scan Package Additions**: Were new dependencies introduced when native APIs exist? Remove them.
3. **Dead Code & Speculative Logic**: Identify functions with 0 references or parameters that are never passed. Prune them.
4. **Cognitive Complexity**: Flag deeply nested conditionals or multi-layer delegation chains and refactor to early returns.
