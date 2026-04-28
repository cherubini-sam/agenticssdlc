---
id: protocols_workflow
description: "6-Phase pipeline, phase gate rules, security redlines, and context limits."
type: protocol
---

# Workflow Protocol

## 6-Phase Pipeline

The pipeline executes a deterministic 6-phase cycle. Exactly one user authorization halt per cycle at Phase 4.

```
Phase 0:  PROTOCOL  — boot validation, system integrity check
Phase 1:  MANAGER   — task classification and routing
Phase 2:  LIBRARIAN — context retrieval via RAG vector store
Phase 3:  ARCHITECT — implementation plan drafting
Phase 4:  REFLECTOR — critique and approval (confidence ≥ threshold, default 0.85) → user authorization
Phase 5:  ENGINEER  — code implementation
Phase 6:  VALIDATOR — verification and sign-off
```

## Phase Gate Rules

### Phase 0 Gate

PROTOCOL validates system integrity. Returns `protocol_status: "system_green"` to allow the pipeline to proceed; `"system_error"` halts the session. No other agent activates until PROTOCOL passes.

### Phase 4 Gate (Planning Lock)

REFLECTOR must approve the plan at confidence ≥ threshold (default 0.85) before the user authorization request is issued. User authorization and REFLECTOR approval are both required — neither overrides the other.

### Stale State Detection

The current plan is STALE when a new user request arrives. MANAGER discards the prior plan state and restarts from Phase 1.

### Phase 5 Entry Condition

ENGINEER receives a plan only after both REFLECTOR approval (confidence ≥ threshold, default 0.85) and user `yes` are confirmed. Plans that have not passed this gate are BLOCKED from Phase 5.

## Security Redlines

### Secrets

Never include API keys, tokens, passwords, or sensitive identifiers in any agent output. Mask with `******`.

### Destruction Guard

Operations that delete or overwrite persistent data (`DROP TABLE`, collection reset, bulk delete) require explicit user confirmation via the workflow authorization halt. Surface the operation and its scope before executing.

### Network Access

No ad-hoc external HTTP calls. Any external call requires explicit user permission.

## Context Limits

### Per-Role Context Limits

All agents receive context as the `context` state field — a string assembled by LIBRARIAN from the top-4 retrieved documents. Agents do not load files directly.

| Agent | Context String Limit |
|:---|:---|
| ENGINEER | Truncated to 4,000 characters |
| REFLECTOR | Truncated to 2,000 characters |
| ARCHITECT, VALIDATOR, MANAGER | Full context string (no truncation) |

## Compliance Audit

- [ ] Phase 0 PROTOCOL completed before Phase 1 routing.
- [ ] Phase 4 gate satisfied: REFLECTOR confidence ≥ threshold (default 0.85) AND user `yes`.
- [ ] No secrets in any output stream.
- [ ] ENGINEER received an approved plan before Phase 5 execution.
