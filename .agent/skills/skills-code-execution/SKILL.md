---
name: skills-code-execution
description: "Production readiness gate — static analysis across forbidden patterns, security, test coverage, style, and architecture boundaries."
---

## 1. Analysis Protocol (run all gates in order)

**Gate 1 → Gate 5 must all pass for a `READY` verdict.**
Any `BLOCKED` gate halts immediately — ENGINEER fixes before re-running.

### Gate 1 — Forbidden Pattern Scan

```python
import re

FORBIDDEN = [
    (r"import\s+os\b",            "bare os import — use pathlib or approved abstraction"),
    (r"import\s+subprocess",      "subprocess import — prohibited in agent-executed code"),
    (r"exec\s*\(",                "exec() call — code injection risk"),
    (r"eval\s*\(",                "eval() call — code injection risk"),
    (r"__import__\s*\(",          "dynamic import — prohibited"),
    (r'open\s*\([^)]*["\']w',     "raw file write — use project I/O utilities"),
    (r"os\.system\s*\(",          "os.system() call — use subprocess with explicit args if unavoidable"),
    (r"print\s*\(",               "print() — use project logging utility"),
    (r"#\s*(TODO|FIXME|HACK|XXX)","unresolved marker — not production-ready"),
    (r"\.\.\.",                   "ellipsis placeholder — implement or remove"),
    (r"^\s*pass\s*$",             "bare pass — dead code"),
]

def scan(code: str) -> list[dict]:
    findings = []
    for lineno, line in enumerate(code.splitlines(), 1):
        for pattern, reason in FORBIDDEN:
            if re.search(pattern, line):
                findings.append({"line": lineno, "pattern": pattern, "reason": reason})
    return findings
```

**Verdict if findings exist:** `BLOCKED`

### Gate 2 — Security Anti-Patterns

Check for:

| Anti-pattern                                                                 | Severity |
| :--------------------------------------------------------------------------- | :------- |
| Hardcoded string matching `sk-`, `AIza`, `Bearer `, `password =`, `secret =` | CRITICAL |
| `f"...{user_input}..."` passed directly to SQL or shell                      | CRITICAL |
| `except Exception: pass` or `except: pass`                                   | HIGH     |
| Mutable default argument `def f(x=[])`                                       | MEDIUM   |
| `assert` used for input validation in non-test code                          | MEDIUM   |

**Verdict if CRITICAL found:** `BLOCKED`
**Verdict if HIGH only:** `NEEDS_REVIEW`

### Gate 3 — Test Coverage Check

For every new public function or class written this phase, verify:

- A corresponding test file exists under `tests/unit/` mirroring the module path.
- The test file contains at least one test for the new symbol.

```
src/agents/agents_engineer.py → tests/unit/test_agents_engineer.py
src/rag/rag_retriever.py      → tests/unit/test_rag_retriever.py
```

**Verdict if test file missing:** `NEEDS_REVIEW` (not BLOCKED — new modules may defer tests)
**Verdict if existing module modified but test file absent:** `BLOCKED`

### Gate 4 — Style Gate

| Check                  | Rule                                                                |
| :--------------------- | :------------------------------------------------------------------ |
| Type annotations       | All public function signatures must have param + return annotations |
| Copyright header       | First line must be the project copyright docstring                  |
| Google-style docstring | Every public function must have a one-line summary                  |
| Line length            | Max 88 chars (Black-compatible)                                     |
| Import order           | stdlib → third-party → local (isort `black` profile)                |

**Verdict if violations found:** `NEEDS_REVIEW`

### Gate 5 — Architecture Boundary Check

Verify the module's imports respect the project's unidirectional dependency flow:

```
globals → systems → utilities → clouds/drivers → domain → main
```

Forbidden cross-imports:

- `globals/` importing from any other layer
- `utilities/` importing from `domain/`
- Lower layers importing `src/api/` or `src/ui/`

**Verdict if boundary violated:** `BLOCKED`

## 2. Readiness Report Format

```
## Production Readiness Report
**File(s):** <paths analyzed>
**Verdict:** READY | NEEDS_REVIEW | BLOCKED

### Gate 1 — Forbidden Patterns
- [PASS | BLOCKED] <finding or "No violations">

### Gate 2 — Security
- [PASS | NEEDS_REVIEW | BLOCKED] <finding or "No violations">

### Gate 3 — Test Coverage
- [PASS | NEEDS_REVIEW | BLOCKED] <finding or "No violations">

### Gate 4 — Style
- [PASS | NEEDS_REVIEW] <finding or "No violations">

### Gate 5 — Architecture Boundaries
- [PASS | BLOCKED] <finding or "No violations">

### Required Actions Before Sign-Off
- [ ] <specific fix 1>
- [ ] <specific fix 2>
```

## 3. Verdict Rules

| Condition                              | Verdict                                                |
| :------------------------------------- | :----------------------------------------------------- |
| All 5 gates PASS                       | `READY` — hand off to VALIDATOR                        |
| One or more NEEDS_REVIEW, zero BLOCKED | `NEEDS_REVIEW` — ENGINEER decides, documents rationale |
| Any BLOCKED gate                       | `BLOCKED` — fix required, re-run analysis              |
