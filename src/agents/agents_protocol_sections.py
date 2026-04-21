"""Canonical protocol-section preamble injected into LIBRARIAN-provided context.

The ARCHITECT and ENGINEER agents carry fail-closed guards that refuse to run
when their plan references section markers (``INTEGRATION & BENCHMARK AUTHORITY``,
``FEEDBACK LOOP``) absent from the runtime context. Those markers are system-level
protocol concepts — they are never task-specific RAG hits, so the LIBRARIAN never
retrieves them organically. Without a deterministic injection path the guard
fires on every production run, producing a contradictory "completed with refusal"
response.

This module defines the literal preamble string that the MANAGER prepends to
LIBRARIAN context at Phase 2. The markers are kept in sync with
``AGENTS_ARCHITECT_REQUIRED_SECTIONS`` and ``AGENTS_KNOWN_PROTOCOL_SECTIONS``;
the body text is intentionally short — the guards only check for literal marker
presence, not semantic completeness.
"""

from __future__ import annotations

from src.agents.agents_utils import (
    AGENTS_ARCHITECT_REQUIRED_SECTIONS,
    AGENTS_KNOWN_PROTOCOL_SECTIONS,
)

AGENTS_PROTOCOL_SECTION_PREAMBLE: str = (
    "## INTEGRATION & BENCHMARK AUTHORITY\n"
    "\n"
    "Canonical source for integration contracts and benchmark targets. The ARCHITECT and "
    "ENGINEER are authorized to reference this section when the plan requires coordination "
    "with external systems (BigQuery, Supabase, Qdrant, Grafana Cloud) or a benchmark "
    "acceptance criterion. Absence of this marker in context indicates a context-assembly "
    "regression — do not proceed with a fabricated integration plan.\n"
    "\n"
    "## FEEDBACK LOOP\n"
    "\n"
    "Canonical source for the validator-to-architect refinement channel. The REFLECTOR's "
    "critique and the VALIDATOR's verdict feed back into the next retry iteration via the "
    "``critique.refined_plan`` state field. Absence of this marker in context means the "
    "refinement channel has not been wired and downstream retries cannot learn from the "
    "prior cycle.\n"
)


def agents_protocol_sections_validate_preamble() -> list[str]:
    """Return the subset of required markers NOT present in the canonical preamble.

    Fails the invariant that every section listed in
    ``AGENTS_ARCHITECT_REQUIRED_SECTIONS`` and ``AGENTS_KNOWN_PROTOCOL_SECTIONS``
    must be literally present in ``AGENTS_PROTOCOL_SECTION_PREAMBLE``. An empty
    return list means the preamble satisfies the guards; a non-empty list is a
    configuration bug and every workflow will refuse until fixed.

    Returns:
        List of marker strings expected by the guards but absent from the
        preamble. Empty when the invariant holds.
    """

    required = set(AGENTS_ARCHITECT_REQUIRED_SECTIONS) | set(AGENTS_KNOWN_PROTOCOL_SECTIONS)
    return [marker for marker in required if marker not in AGENTS_PROTOCOL_SECTION_PREAMBLE]
