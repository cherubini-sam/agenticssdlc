"""Multi-persona confidence audit condensed into one or two LLM passes."""

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.agents_base import AgentsBase
from src.agents.agents_utils import (
    AGENTS_REFLECTOR_AGENT_NAME,
    AGENTS_REFLECTOR_CONTEXT_TRUNCATION,
    AGENTS_REFLECTOR_DEFAULT_CONFIDENCE,
    AGENTS_REFLECTOR_FAST_CONFIDENCE_THRESHOLD,
    AGENTS_REFLECTOR_HUMAN_TEMPLATE,
    AGENTS_REFLECTOR_JSON_PATTERN,
    AGENTS_REFLECTOR_SEVERITY_MEDIUM,
    AGENTS_REFLECTOR_SKIP_LABEL,
    AGENTS_REFLECTOR_SYSTEM_PROMPT,
)


class AgentsReflector(AgentsBase):
    """Judge/critic/refiner/curator rolled into a single LLM call when possible."""

    agent_name: str = AGENTS_REFLECTOR_AGENT_NAME

    async def agents_reflector_critique(self, plan: str, context: str, task: str) -> dict:
        """Two-pass audit: fast assessment first, full refinement only if confidence is low."""

        ctx = (context or "")[:AGENTS_REFLECTOR_CONTEXT_TRUNCATION]
        human_fast = AGENTS_REFLECTOR_HUMAN_TEMPLATE.format(
            threshold=AGENTS_REFLECTOR_FAST_CONFIDENCE_THRESHOLD,
            skip_label=AGENTS_REFLECTOR_SKIP_LABEL,
            task=task,
            context=ctx,
            plan=plan,
        )

        # Pass 1: quick assessment; most plans clear this and skip the second call
        raw_initial = await self._agents_base_call_llm(
            [
                SystemMessage(content=AGENTS_REFLECTOR_SYSTEM_PROMPT),
                HumanMessage(content=human_fast),
            ]
        )
        result = self._agents_reflector_parse(raw_initial, {})

        is_high_conf = (
            float(result.get("confidence", 0.0)) >= AGENTS_REFLECTOR_FAST_CONFIDENCE_THRESHOLD
        )
        should_skip = result.get("refined_plan") == AGENTS_REFLECTOR_SKIP_LABEL or is_high_conf

        if should_skip:
            # Plan looks solid; keep it as-is, no refinement needed
            return {
                "confidence": float(result.get("confidence", AGENTS_REFLECTOR_DEFAULT_CONFIDENCE)),
                "errors": result.get("errors", []),
                "severity": result.get("severity", AGENTS_REFLECTOR_SEVERITY_MEDIUM),
                "suggestions": result.get("suggestions", []),
                "refined_plan": plan,
                "improvements": result.get("improvements", []),
                "reuse_pattern": result.get("reuse_pattern", ""),
                "knowledge_atom": result.get(
                    "knowledge_atom", "Optimal plan detected. Skipping refinement pass."
                ),
            }

        # Pass 1 flagged issues; use whatever refinement the LLM already provided
        return {
            "confidence": float(result.get("confidence", AGENTS_REFLECTOR_DEFAULT_CONFIDENCE)),
            "errors": result.get("errors", []),
            "severity": result.get("severity", AGENTS_REFLECTOR_SEVERITY_MEDIUM),
            "suggestions": result.get("suggestions", []),
            "refined_plan": result.get("refined_plan", plan),
            "improvements": result.get("improvements", []),
            "reuse_pattern": result.get("reuse_pattern", ""),
            "knowledge_atom": result.get("knowledge_atom", ""),
        }

    @staticmethod
    def _agents_reflector_parse(raw: str, default: dict) -> dict:
        """Extract the first JSON object from raw LLM output. Falls back to default on failure."""

        try:
            m = re.search(AGENTS_REFLECTOR_JSON_PATTERN, raw, re.DOTALL)
            if m:
                return json.loads(m.group())
        except (json.JSONDecodeError, AttributeError):
            pass
        return default
