---
name: skills-prompt-engineering
description: "MANAGER request-structuring protocol — transforms raw user input into a structured goal/scope/constraints/acceptance/refs XML packet before every ARCHITECT handoff."
---

## 1. Transformation Protocol

Apply deterministically — identical input produces identical output. No synonym substitution. No creative rewording.

### Step 1 — Language Lock

Detect session language from the first substantive word of the input.

- `EN` → all output in English
- Mixed → use the dominant language of the body

### Step 2 — Strip Zero-Semantic Tokens

Remove: greetings ("hi", "please", "could you"), hedging ("I think", "maybe"), polite framing ("I was wondering if").
Preserve: every technical term, file path, function name, error message, and constraint word.

### Step 3 — Resolve Deictic References

| Deictic         | Resolution rule                                                            |
| :-------------- | :------------------------------------------------------------------------- |
| "this file"     | Resolve from IDE selection, attached file, or most recently mentioned path |
| "that function" | Resolve to the function name last mentioned in context                     |
| "the bug"       | Resolve to the error identifier, stack trace, or symptom described         |
| "it" / "them"   | Resolve to the last concrete noun in the message                           |

If a deictic cannot be resolved → mark as `{{UNRESOLVED: <original text>}}` and flag in Step 6.

### Step 4 — Extract Implicit Constraints

Surface constraints hidden in the phrasing:

- "without breaking tests" → `constraint: must not regress existing test suite`
- "quickly" / "simple" → `constraint: minimal scope; no new abstractions`
- "production" → `constraint: no debug code, no TODO markers, no placeholder logic`
- "refactor only" → `constraint: no feature additions; behavior must be preserved`

### Step 5 — Build Output Packet

```xml
<context_packet>
  <goal>{{one-sentence, action-verb-first statement of what must be achieved}}</goal>
  <scope>
    <in>
      - {{concrete in-scope item 1}}
      - {{concrete in-scope item 2}}
    </in>
    <out>
      - {{explicitly excluded concern 1}}
    </out>
  </scope>
  <constraints>
    - {{technical, security, style, time, dependency constraint}}
  </constraints>
  <acceptance>
    - {{measurable criterion 1 — Definition of Done}}
    - {{measurable criterion 2}}
  </acceptance>
  <refs>
    - {{file path, function name, error id, or external resource — never invented}}
  </refs>
</context_packet>
```

### Step 6 — Validate & Flag

Before emitting the packet, verify:

| Check                                                      | Rule                                                                               |
| :--------------------------------------------------------- | :--------------------------------------------------------------------------------- |
| `<goal>` is a single sentence starting with an action verb | Reject multi-sentence goals; split into scope items                                |
| No invented references in `<refs>`                         | Every ref must appear verbatim in the original input or be resolvable from context |
| `<out>` is populated                                       | If scope boundaries are implicit, surface the most likely exclusions               |
| Token delta ≤ 0                                            | The packet must be ≤ the original token count; reformulation MUST NOT pad          |
| No unresolved deictics remain                              | If `{{UNRESOLVED}}` markers exist, halt and ask the user for clarification         |

## 2. Scope Boundary Rules

When the user's request is ambiguous about scope, apply the **minimum viable scope** principle:

- A bug fix → scope covers only the reported symptom, not surrounding cleanup
- A feature request → scope covers the named feature only, not related improvements
- A refactor → scope covers the named module/function only, not callers or dependencies
- "Everything" / "the whole thing" → halt and ask for explicit scope confirmation

## 3. Quick-Pass Conditions (skip transformation)

Return the original input verbatim when:

- Input < 15 tokens
- Input is a single-word acknowledgment (`yes`, `no`, `proceed`, `stop`)
- Input is a slash command (`/compact`, `/review-pr`, ...)
- Input contains `"verbatim"`, `"exact"`, `"letterale"`, `"così com'è"`
