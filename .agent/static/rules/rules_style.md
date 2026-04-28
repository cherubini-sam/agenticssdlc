---
id: rules_style
description: "Hygiene, formatting, and implementation standards for artifacts and code."
type: rule
---

# Style Rules

## Language (Law 10)

Session language is detected at Phase 0 and locked for the entire P1→P6 cycle. In any conflict: session language wins. On mismatch: REGENERATE output in the locked language.

Exception: technical terms, code identifiers, and comments always use canonical English regardless of session language.

## Formatting (Laws 11, 12)

Zero fluff. No preambles, apologies, or trailing summaries. No emojis in source code, filenames, or system artifacts. Standard: GitHub Flavored Markdown.

## Code Standards

Type annotations mandatory (static analysis compatibility). Documentation comments: one-line summary plus parameter and return descriptions. Structured error handling required on all file and network I/O.

**Prohibited in production:** no-op stubs, `TODO`, `FIXME`, `TBD`, commented-out code blocks, placeholder `...` markers, bare `pass`. Delete old files immediately after successful refactor.

## Output Structure

Plan and critique outputs use H2 (`##`) for major logical sections. Checkbox syntax (`- [ ]` pending, `- [x]` complete) for phase status. Plan revisions MUST append a "Revision History" section — never truncate prior design history.

### Violation Consequences

| Violation | Action |
|:---|:---|
| Language mismatch | REGENERATE in correct language |
| Emoji in output | Strip and log |
| Placeholder / pass-zombie in generated code | Reject and request full implementation |

## Style Audit

- [ ] **Check 1:** Output language matches session lock (Law 10).
- [ ] **Check 2:** No emojis in code, filenames, or system output (Law 12).
- [ ] **Check 3:** No TODO / TBD / placeholder markers / no-op stubs in generated code (Law 6).
