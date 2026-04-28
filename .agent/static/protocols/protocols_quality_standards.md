---
id: protocols_quality_standards
description: "Content quality standards, anti-patterns, evaluation metrics, script constraints, and allowed tools for all agents."
type: protocol
---

# Quality Standards

## Content Quality

**Emoji Policy:** STRICTLY FORBIDDEN. **Tone:** Technical, Professional, Zero-Fluff.

### Content Depth

**Forbidden:** `TODO`, `TBD`, placeholders. **Requirement:** Complete, working code/docs.

### Writing Style

**Allowed:** Passive (descriptive), Active (instructional). **Forbidden:** Slang, first-person.


## Definition of Done

- **Workflow Completion:** All 6 phases (0–6) verified.

## Verification Protocol

Before completion: no emojis | copyright present | no placeholders | schemas valid | phase boundary not violated (Law 15).

## Anti-Patterns

### Recovery Protocols

**SYNC_FAILURE:** Exponential backoff (1s, 2s, 4s, 8s, 16s). Max 5 retries → ABORT.

**STATE_MISSING:** Required context field is absent from the workflow state → surface the missing field to MANAGER and halt.

### Token Anti-Patterns

**Context Bloat:** Injecting an untruncated context string into agents that have tighter limits. Guard: ENGINEER cap is 4,000 characters; REFLECTOR cap is 2,000 characters — apply truncation before injection. Recovery: prune context to relevant sections only.

**Cache Miss:** Dynamic content before static in prompt structure. Guard: static rules first. Recovery: reorder prompt structure.

### Workflow Anti-Patterns

**Freestyle Output:** Creating artifacts without following defined schemas. Action: use schema definitions. All outputs must follow established schemas.

**Vague Task:** Manager starts execution without a task manifest or manifest is vague. Action: BLOCK — break down steps until atomic and unambiguous.

**Schema Void:** Agent output does not follow the required schema. Action: REJECT — retry with the explicit schema definition.

**Phase Consolidated (Law 15 Violation):** Agent crosses more than one phase boundary per invocation. Action: STOP at the first phase boundary — require a new invocation for the next phase.

## INTEGRATION & BENCHMARK AUTHORITY

Evaluation dimensions and scoring for agent output quality assessment.

### Evaluation Dimensions

| Dimension | Definition | Measurement | Weight |
|:---|:---|:---|:---|
| Accuracy | Output correctness vs expected | % correct assertions | 30% |
| Completeness | All requirements addressed | % requirements satisfied | 25% |
| Efficiency | Resource usage vs baseline | Tokens used / optimal | 20% |
| Safety | No policy violations | Binary (pass/fail) | 15% |
| Latency | Response time within limits | Actual vs threshold | 10% |

`final_score = accuracy*0.30 + completeness*0.25 + efficiency*0.20 + safety*0.15 + latency*0.10`

| Score | Grade | Action |
|:---|:---|:---|
| 0.95–1.00 | A+ | Approve |
| 0.90–0.94 | A | Approve |
| 0.80–0.89 | B | Approve with notes |
| 0.70–0.79 | C | Review recommended |
| 0.50–0.69 | D | Refinement required |
| 0.00–0.49 | F | Reject |

### Self-Evaluation Checklist

**Pre-Response:** PROTOCOL boot passed | language consistent (Law 10) | no emojis | no placeholders.

**Post-Response:** Target agent executed | output delivered into correct state field.

### Reflector Integration

Route to REFLECTOR when: quality score < threshold (configurable, default 0.85) | security-sensitive output | architecture decisions | multi-file changes | user requests review.

`Score < threshold → REFLECTOR | Score ≥ threshold → Approve`

### Benchmark Alignment

**GAIA:** Reasoning, multi-modality, tool use.
**HAL:** Coding, science, customer service.

## FEEDBACK LOOP

Continuous improvement cycle to track quality scores and identify recurring failure patterns.

`Execute → Evaluate → Log → Analyze → Improve → (repeat)`

Track: average quality score per agent | common failure patterns | improvement rate after reflection | user satisfaction.

## Script Constraints

- **No Hard Paths:** Use the runtime working directory API or relative paths.
- **No User Interaction:** Never use interactive prompts — inputs come from the workflow state.
- **No Placeholders:** Full implementation only (Law 6).

### Script Lifecycle

1. Delete one-time scripts after successful execution.
2. Exit codes: `0` = success | `1` = error | `2` = validation failure.

### Script Execution Checklist

- [ ] No hardcoded paths (runtime working directory API or relative only).
- [ ] No interactive prompts — inputs come from workflow state only.
- [ ] No placeholder markers (`TODO`, `...`, `TBD`).
- [ ] Exit codes match contract (0/1/2).

## Output Delivery

Agent output is delivered as structured text into the workflow state fields (`plan`, `critique`, `result`, `error`, `confidence`). Agents do not write files or call external APIs directly — the workflow harness acts on their output.

### Error Recovery

**Context retrieval fail:** Proceed with internal knowledge. Do NOT surface raw retrieval errors in the response.

**LLM timeout:** The harness retries with exponential backoff. Agents do not need to handle retry logic in their output.
