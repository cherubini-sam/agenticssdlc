---
id: skills_documentation
description: "Documentation discipline — Diátaxis four modes, doc-as-code, audience voice, freshness."
type: skill
---

## Scope

Documentation is a delivery artefact: four user needs — learn, perform, look up, understand — each gets its own page, in the right voice, built and reviewed alongside the code.

## Diátaxis Four Modes

| Mode | User Need | Form |
| :--- | :--- | :--- |
| Tutorial | "I'm new — show me" | Step-by-step lesson; guaranteed outcome |
| How-to guide | "I have a goal — help me reach it" | Numbered steps for a competent user |
| Reference | "What does this do, exactly?" | Complete, accurate, neutral |
| Explanation | "Why is it like this?" | Context, trade-offs, background |

Mature surfaces have all four; thin surfaces may compose how-to plus reference.

## Doc-as-Code

| Check | Direction |
| :--- | :--- |
| Source location | Same repository as the code |
| Review | Changes reviewed like code |
| Build | Builds in the pipeline; broken builds block merge |
| Link integrity | Internal links checked in the pipeline |
| Examples | Tested against real source — never hand-typed |
| Versioning | Tracks product versions; old versions accessible |

## Audience and Voice

| Audience | Voice | Length |
| :--- | :--- | :--- |
| New user (tutorial) | Encouraging, concrete, second person | 5–15 min hands-on |
| Competent user (how-to) | Imperative, terse, no preamble | One screen per task |
| Implementer (reference) | Neutral, exhaustive, structural | As long as the surface |
| Decision maker (explanation) | Reflective, comparative | One topic per article |

## Freshness

Last-reviewed date per page; over 12 months triggers review. Owning team named. Deprecation banners naming the replacement, not a 404. Stale pages removed or redirected.

## Source

Procida, Diátaxis; Gentle, Docs Like Code, 2nd ed., 2017.
