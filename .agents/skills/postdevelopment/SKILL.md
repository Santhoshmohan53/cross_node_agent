---
name: postdevelopment
description: Runs automated code verification, scans files for configuration flaws, and structures clean logging documentation in Antigravity Artifacts.
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# Post-Development Audit Workflow

description: Runs automated code verification, scans files for configuration flaws, and structures clean logging documentation.

## Steps

1. **Verify that no private environment files, keys, or passwords are rawly coded inside the updated paths.**
   - Scan modified and staged files for raw API keys, bearer tokens, AWS credentials, private keys (`BEGIN PRIVATE KEY`), or hardcoded passwords.
   - Verify that `.env`, `.env.local`, `.env.production`, and credential stores are included in `.gitignore` and never committed.
   - Check that secret references use environment variables (`process.env.KEY`, `os.environ.get("KEY")`).

2. **Audit the project structure to ensure all elements perfectly respect active directory paths.**
   - Verify that all imports and file paths use standard path conventions (`Join-Path`, `path.join`, relative paths, or configured `@/` aliases).
   - Check that no absolute machine-specific paths (e.g. `C:\Users\username\...` or `/home/username/...`) are hardcoded in application logic.
   - Verify path casing consistency across case-sensitive POSIX and case-insensitive Windows environments.
   - Confirm that temp files, logs, and scratch scripts are stored in proper designated scratch/tmp directories.

3. **Run the automated testing harness script inside the project's sandboxed terminal view.**
   - Identify the project's test runner (`npm test`, `pytest`, `cargo test`, `go test`, `flutter test`, or custom test scripts).
   - Execute the test suite via the terminal.
   - Capture live test results, exit codes, test duration, and pass/fail counts.
   - If tests fail, halt and report the exact failure output for immediate remediation.

4. **Output a brief markdown overview summarizing your terminal outputs, script updates, and validation scores inside the Antigravity Artifacts window.**
   - Create or update a designated markdown artifact (`postdevelopment_audit.md`).
   - Include:
     - **Security & Secret Audit**: Pass/Fail status and scanned file count.
     - **Path & Directory Hygiene**: Pass/Fail status and path consistency check.
     - **Automated Test Results**: Test runner name, suite duration, tests passed/failed/skipped, and raw terminal log snippet.
     - **Validation Score**: Summary rating (e.g. `100% PASS` or action items).
