---
id: skills_architecture_design
description: "System design — boundaries, contracts, decomposition, decision capture."
type: skill
---

## Scope

System architecture decomposes a system into runtime units, names the boundaries between them, captures the trade-offs that produced the design, and decides which cross-cutting concerns each unit must address.

## C4 Decomposition

| Level | Question | Output |
| :--- | :--- | :--- |
| Context | Who uses the system and which external systems does it depend on? | User roles plus external systems |
| Container | Which runtime units make up the system? | Container list with one-sentence responsibility |
| Component | Which modules cooperate inside each container? | Component list per container |
| Code | Module-level relations | Only when non-obvious |

## Boundary Hygiene

| Property | Direction |
| :--- | :--- |
| Data ownership | Each container owns its store; no cross-container database sharing |
| Single responsibility | One sentence per component |
| Call depth | Synchronous calls cross at most one boundary; deeper chains use async or events |
| Contract surface | Explicit interface, schema, or event — never an implicit shared struct |

## Architectural Decision Records

| Section | Content |
| :--- | :--- |
| Title | Imperative phrase |
| Status | proposed / accepted / superseded |
| Context | Forces and constraint the decision must satisfy |
| Decision | The choice, stated affirmatively |
| Consequences | Positive, negative, neutral effects, including what becomes harder |
| Alternatives | At least two rejected options with one-line rationale |

ADRs are append-only; reversal creates a new ADR that supersedes the old.

## Cross-Cutting Concerns

Decide up front, per container: failure mode per external dependency; data lifecycle (retention, deletion, ownership); authentication boundary; versioning policy; minimum observability signals.

## Source

Brown, C4 Model; Nygard, Documenting Architecture Decisions, 2011.
