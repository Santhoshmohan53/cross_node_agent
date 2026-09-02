---
name: tdd-verification
description: Enforce strict Test-Driven Development (TDD) and automated test execution quality gates. Mandates the Iron Law (no code without a failing test), Red-Green-Refactor loop, and automated verification in the terminal before declaring tasks complete. Use when writing new features, fixing bugs, refactoring logic, or performing pre-commit verification.
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# TDD-Verification: Quality Gate & Test-Driven Development Protocol

This skill enforces disciplined, test-grounded engineering. It prevents "vibe coding" (assuming code works without empirical verification) by mandating that every feature, bug fix, or refactor is validated through automated test execution in the terminal before a task is marked complete.

---

## 1. The Iron Law of TDD

> [!CAUTION]
> **No production code shall be written or marked complete without an automated test verifying its behavior.**
> If there is no test verifying the change, the task is **not done**.

---

## 2. The Red-Green-Refactor Verification Cycle

```
  ┌─────────────────────────────────────────────────────────┐
  │ 1. RED      Write a test capturing the desired behavior.│
  │             Execute it -> Verify it FAILS as expected.   │
  └───────────────────────────┬─────────────────────────────┘
                              │
  ┌───────────────────────────▼─────────────────────────────┐
  │ 2. GREEN    Write the MINIMAL code required to pass.    │
  │             Execute test -> Verify it PASSES (exit 0).  │
  └───────────────────────────┬─────────────────────────────┘
                              │
  ┌───────────────────────────▼─────────────────────────────┐
  │ 3. REFACTOR Clean up code, remove duplication.          │
  │             Re-run full suite -> Guarantee NO regression.│
  └─────────────────────────────────────────────────────────┘
```

### Step 1: RED (Failing Test)
- **For Bug Fixes**: Write a regression test that reliably reproduces the reported bug. Run it to witness the failure.
- **For New Features**: Write a unit/integration test defining the expected interface, return values, and edge cases before writing the implementation.
- **Verify Failure Mode**: Ensure the test fails because the feature is missing or the bug exists, *not* because of a syntax or import error.

### Step 2: GREEN (Minimal Implementation)
- Write the simplest code necessary to satisfy the test contract (applying the *Ponytail Rule*).
- Run the test suite and confirm that the test passes with exit code 0.

### Step 3: REFACTOR & VERIFY (Zero Regressions)
- Simplify structure, remove duplicated logic, and enforce typing.
- Run the complete project test suite to verify that existing features remain unbroken.

---

## 3. Test Runner Detection & Execution Matrix

Detect the project's native test harness and run the targeted test command:

| Ecosystem | Configuration File | Targeted Test Command | Full Suite Command |
|---|---|---|---|
| **Node / TS (Vitest)** | `vitest.config.ts` | `npx vitest run path/to/test.ts` | `npm test` |
| **Node / TS (Jest)** | `jest.config.js` | `npx jest path/to/test.ts` | `npm test` |
| **Node (Native Test)** | `package.json` | `node --test path/to/test.mjs` | `npm test` |
| **Python (pytest)** | `pyproject.toml` / `pytest.ini` | `pytest tests/test_feature.py -v` | `pytest` |
| **Python (unittest)** | `setup.py` / `tests/` | `python -m unittest tests/test_feature.py` | `python -m unittest discover` |
| **Go** | `go.mod` | `go test -v ./pkg/feature/...` | `go test ./...` |
| **Rust** | `Cargo.toml` | `cargo test test_feature_name` | `cargo test` |
| **Flutter / Dart** | `pubspec.yaml` | `flutter test test/feature_test.dart` | `flutter test` |

---

## 4. Test Quality Guidelines

1. **Deterministic Assertions**: Avoid flaky tests, random seeds, or unseeded time dependencies.
2. **Mock Boundaries**: Mock external network calls, payment APIs, and heavy database sidecars; test business logic directly.
3. **Async / Timers**: Properly `await` async promises, use fake timers for delays, and handle timeouts gracefully.
4. **Boundary & Edge Cases**: Test empty inputs, `null`/`undefined`, invalid types, negative numbers, and boundary limits.

---

## 5. Quality Gate Checklist

Before declaring any coding task complete:
- [ ] Reproducing or unit test written.
- [ ] Test executed in the sandboxed terminal view.
- [ ] Confirmed exit code 0 and passing assertions.
- [ ] Full regression test suite executed without failures.
- [ ] Terminal test logs recorded for artifact reporting.
