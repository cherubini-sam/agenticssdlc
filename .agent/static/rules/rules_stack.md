---
id: rules_stack
description: "Token budget policing and model configuration rules for agents."
type: rule
---

# Stack Rules

## LLM Runtime

The model is fixed for the duration of the session. All agents operate on the same model — no switching at runtime.

Model selection (provider, model ID, temperature, max tokens) is an environment and infrastructure concern. Agents define what they do with responses — not which model executes them.

## Token Budget

| Threshold | Action |
|:---|:---|
| Single request > 50K tokens | LOG WARNING |
| Session total > 500K tokens | STOP + REQUEST CHECKPOINT |

Bypass: manual user override for large-scale codebase migrations.

## Stack Audit

- [ ] **Check 1:** Request token count < 50K; session total < 500K.
- [ ] **Check 2:** Infrastructure targets match authoritative stack configuration.
