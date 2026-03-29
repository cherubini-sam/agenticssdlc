#!/usr/bin/env python3
"""
Prompt optimizer
Automatically optimize prompts for token efficiency and quality
"""

import re
from typing import Dict, List, Tuple


class PromptOptimizer:
    """Optimize prompts for efficiency and effectiveness"""

    # Common verbose phrases and their concise alternatives
    VERBOSE_PATTERNS = {
        r"please\s+": "",
        r"could\s+you\s+": "",
        r"would\s+you\s+": "",
        r"if\s+you\s+don't\s+mind\s*,?\s*": "",
        r"kindly\s+": "",
        r"I\s+would\s+like\s+you\s+to\s+": "",
        r"I\s+need\s+you\s+to\s+": "",
        r"can\s+you\s+": "",
        r"help\s+me\s+(to\s+)?": "",
    }

    # Redundant words to remove
    FILLER_WORDS = {
        "actually",
        "basically",
        "essentially",
        "literally",
        "really",
        "very",
        "quite",
        "rather",
        "somewhat",
    }

    def __init__(self):
        self.optimization_log = []

    def optimize(self, prompt: str) -> Tuple[str, Dict]:
        """
        Optimize a prompt for efficiency

        Returns:
            (optimized_prompt, metrics)
        """
        original_length = len(prompt)
        original_tokens = self._estimate_tokens(prompt)

        optimized = prompt

        # Remove excessive politeness
        optimized = self._remove_verbose_phrases(optimized)

        # Remove filler words
        optimized = self._remove_filler_words(optimized)

        # Consolidate whitespace
        optimized = self._consolidate_whitespace(optimized)

        # Remove redundant punctuation
        optimized = self._clean_punctuation(optimized)

        new_length = len(optimized)
        new_tokens = self._estimate_tokens(optimized)

        metrics = {
            "original_length": original_length,
            "optimized_length": new_length,
            "chars_saved": original_length - new_length,
            "reduction_pct": (
                ((original_length - new_length) / original_length * 100)
                if original_length > 0
                else 0
            ),
            "original_tokens": original_tokens,
            "optimized_tokens": new_tokens,
            "tokens_saved": original_tokens - new_tokens,
        }

        return optimized, metrics

    def _remove_verbose_phrases(self, text: str) -> str:
        """Remove verbose phrases"""
        result = text
        for pattern, replacement in self.VERBOSE_PATTERNS.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result

    def _remove_filler_words(self, text: str) -> str:
        """Remove filler words"""
        words = text.split()
        filtered = [w for w in words if w.lower() not in self.FILLER_WORDS]
        return " ".join(filtered)

    def _consolidate_whitespace(self, text: str) -> str:
        """Consolidate multiple spaces/newlines"""
        # Multiple spaces to single space
        text = re.sub(r" +", " ", text)
        # Multiple newlines to double newline (preserve paragraph breaks)
        text = re.sub(r"\n\n+", "\n\n", text)
        return text.strip()

    def _clean_punctuation(self, text: str) -> str:
        """Remove redundant punctuation"""
        # Multiple punctuation marks
        text = re.sub(r"([!?.])\1+", r"\1", text)
        # Space before punctuation
        text = re.sub(r"\s+([,.!?;:])", r"\1", text)
        return text

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        return int(len(text.split()) * 1.3)

    def chunk_prompt(self, prompt: str, max_chunk_size: int = 1000) -> List[Dict]:
        """
        Break prompt into cacheable chunks

        Returns:
            List of chunks with metadata
        """
        sections = self._identify_sections(prompt)
        chunks = []

        current_chunk = ""
        current_type = "static"

        for section in sections:
            section_text = section["text"]
            section_type = section["type"]

            # If adding this section exceeds max size, save current chunk
            if len(current_chunk) + len(section_text) > max_chunk_size and current_chunk:
                chunks.append(
                    {
                        "content": current_chunk.strip(),
                        "type": current_type,
                        "cacheable": current_type == "static",
                        "size": len(current_chunk),
                    }
                )
                current_chunk = ""

            current_chunk += section_text + "\n\n"
            current_type = section_type

        # Add final chunk
        if current_chunk:
            chunks.append(
                {
                    "content": current_chunk.strip(),
                    "type": current_type,
                    "cacheable": current_type == "static",
                    "size": len(current_chunk),
                }
            )

        return chunks

    def _identify_sections(self, prompt: str) -> List[Dict]:
        """Identify static vs dynamic sections"""
        # Simple heuristic: sections with {variables} are dynamic
        sections = []

        # Split by double newlines (paragraphs)
        paragraphs = prompt.split("\n\n")

        for para in paragraphs:
            has_variables = "{" in para and "}" in para
            section_type = "dynamic" if has_variables else "static"

            sections.append({"text": para, "type": section_type})

        return sections

    def generate_variants(self, prompt: str, count: int = 3) -> List[str]:
        """Generate prompt variants for A/B testing"""
        variants = [prompt]  # Original

        # Variant 1: More concise
        concise, _ = self.optimize(prompt)
        variants.append(concise)

        # Variant 2: More structured (add XML tags if not present)
        if "<" not in prompt:
            structured = self._add_structure(prompt)
            variants.append(structured)

        # Variant 3: Add examples if not present
        if "example" not in prompt.lower():
            with_examples = prompt + "\n\nExample:\nInput: [sample]\nOutput: [expected]"
            variants.append(with_examples)

        return variants[:count]

    def _add_structure(self, prompt: str) -> str:
        """Add XML structure to unstructured prompt"""
        return f"""<task>
{prompt}
</task>

<constraints>
- Be concise
- Follow the specified format
</constraints>"""


def main():
    """Example usage"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python scripts_prompt_optimizer.py '<prompt>'")
        sys.exit(1)

    prompt = sys.argv[1]

    optimizer = PromptOptimizer()

    print("=== PROMPT OPTIMIZATION ===\n")
    print(f"Original:\n{prompt}\n")

    optimized, metrics = optimizer.optimize(prompt)

    print(f"Optimized:\n{optimized}\n")
    print("Metrics:")
    print(f"  Characters saved: {metrics['chars_saved']} ({metrics['reduction_pct']:.1f}%)")
    print(f"  Tokens saved: {metrics['tokens_saved']}")

    print("\n=== VARIANTS ===\n")
    variants = optimizer.generate_variants(prompt)
    for i, variant in enumerate(variants, 1):
        print(f"{i}. {variant[:100]}...\n")


if __name__ == "__main__":
    main()
