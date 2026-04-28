---
id: skills_code_execution
description: "Source-level static cleanliness — forbidden patterns, hygiene markers, structural style, complexity."
type: skill
---

## Scope

Source-level cleanliness keeps a codebase readable, finishable, and free of patterns that compromise it on its own terms — independent of runtime behaviour.

## Forbidden Patterns

| Pattern | Reason |
| :--- | :--- |
| Direct OS or process-control module import | Use the project abstraction |
| Subprocess or external-command execution import | Prohibited in agent-executed code |
| Dynamic code or expression evaluation | Code-injection surface |
| Dynamic module loading | Bypasses project import resolution |
| Raw file write bypassing project I/O | Use the project I/O layer |
| External command via system call without explicit argument list | Command-injection surface |
| Direct console output in non-CLI code | Use the project logging utility |

## Hygiene Markers

| Marker | Reason |
| :--- | :--- |
| `TODO`, `FIXME`, `HACK`, `XXX` | Unresolved work — not production-ready |
| Placeholder or no-op stub as implementation body | Implement or remove |
| Commented-out code block | Use version control, not comments |
| Empty catch block | Hides failures — log and re-raise or convert |
| Mutable value as a function default parameter | Cross-call state leak |

## Structural Style

Public signatures carry parameter and return annotations; every public function has a one-line summary. One casing convention per module. Imports ordered standard library → third-party → local. Project copyright on every file.

## Complexity Thresholds

| Check | Threshold |
| :--- | :--- |
| Cyclomatic complexity | At most 10; over 15 requires justification |
| Function length | At most 50 lines of body |
| Module length | At most 500 lines |
| Parameter count | At most 5 positional |
| Nesting depth | At most 3 levels |

## Source

NIST SP 800-218 v1.1 (PW.5, PW.7), 2022; McCabe, A Complexity Measure, IEEE TSE, 1976.
