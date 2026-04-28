---
id: skills_data_modeling
description: "Schema design and migration safety — types, constraints, contracts, zero-downtime evolution."
type: skill
---

## Scope

Data modelling chooses the storage shape that answers queries correctly, evolves without downtime, and survives concurrent change. Shape decisions outlive the code that reads and writes them.

## Schema Hygiene

| Check | Direction |
| :--- | :--- |
| Primary key | Explicit, immutable identifier |
| Type fidelity | Narrowest type; decimal for money; enum over free text |
| Nullability | Default non-null; nullable fields document why |
| Foreign keys | Declares referential action |
| Time | UTC; stored at required precision |
| Money / quantity | Exact-precision; explicit unit and currency |

## Data Contracts

| Element | Direction |
| :--- | :--- |
| Schema | Versioned, machine-readable; compatibility rules declared |
| Semantics | Each field documents definition, unit, range |
| Ownership | Producing team named |
| SLO | Freshness, completeness, accuracy targets per dataset |
| Compatibility | Forward, backward, or full — enforced at publish time |

## Constraints

`NOT NULL`, `UNIQUE`, `CHECK`, foreign keys, and indexes belong in the storage layer. Application-only enforcement of a storage-enforceable invariant is a smell.

## Migration Safety (Expand → Migrate → Contract)

| Phase | Action |
| :--- | :--- |
| Expand | Add columns, tables, indexes — additive only; old and new code work |
| Backfill | Populate new fields in batches, idempotently |
| Dual-write | Code writes both shapes during transition |
| Cutover | Switch reads or writes to new shape behind a flag |
| Contract | Drop old columns, tables, indexes |

Every step reversible until contract. Direct destructive migrations on live data are unsafe.

## Source

Ambler & Sadalage, Refactoring Databases, 2006; Fowler, PoEAA, 2002; Jones, Data Contracts, 2023; Dehghani, Data Mesh, 2022.
