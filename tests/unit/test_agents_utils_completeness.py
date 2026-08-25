"""Behavioral contract coverage for agents_validator_find_empty_sections."""

from __future__ import annotations

import time

from agents.agents_validator import agents_validator_find_empty_sections


class TestAgentsUtilsFindEmptySectionsPositive:
    """Cases that MUST be flagged as empty."""

    def test_brief_fixture_flags_empty_code_section(self) -> None:
        """The exact defect fixture from the requirements brief."""
        result = agents_validator_find_empty_sections("## Code\n\n## Notes\n\ntext")
        assert result == ["Code"]

    def test_trailing_heading_at_eof_is_flagged(self) -> None:
        """A heading with nothing after it, up to EOF, is empty."""
        result = agents_validator_find_empty_sections("## Notes\n\ntext\n\n## Trailing")
        assert result == ["Trailing"]

    def test_whitespace_only_body_is_flagged(self) -> None:
        """A body of only blank lines/whitespace counts as empty."""
        result = agents_validator_find_empty_sections("## A\n\n   \n\n")
        assert result == ["A"]


class TestAgentsUtilsFindEmptySectionsNegative:
    """False-positive guards — each maps to one Step 3 recognition clause."""

    def test_empty_string_returns_empty_list(self) -> None:
        assert agents_validator_find_empty_sections("") == []

    def test_prose_with_no_heading_returns_empty_list(self) -> None:
        assert agents_validator_find_empty_sections("just prose, no headings at all") == []

    def test_container_heading_is_not_empty(self) -> None:
        """(5d) A heading immediately followed by a deeper heading is a container."""
        result = agents_validator_find_empty_sections("## A\n### A.1\nbody")
        assert result == []

    def test_terse_but_present_body_is_not_flagged(self) -> None:
        """Zero-non-whitespace only — never a length heuristic (NFR-003/AC-D3-04)."""
        result = agents_validator_find_empty_sections("## A\nword")
        assert result == []

    def test_backtick_fence_hides_phantom_heading(self) -> None:
        """(5a) A '#' at column 0 inside a backtick fence is never a heading."""
        markdown = "## A\n```\n# not a heading\n```\nbody"
        result = agents_validator_find_empty_sections(markdown)
        assert "not a heading" not in result

    def test_backtick_fence_bare_no_trailing_body_line(self) -> None:
        """Bare fenced case with no line after the closing fence."""
        markdown = "## A\n```\n# not a heading\n```\n"
        result = agents_validator_find_empty_sections(markdown)
        assert "not a heading" not in result
        assert result != ["A", "not a heading"]

    def test_tilde_fence_hides_phantom_heading(self) -> None:
        """(5a) Tilde fences are skipped exactly like backtick fences."""
        markdown = "## A\n~~~\n# not a heading\n~~~\nbody"
        result = agents_validator_find_empty_sections(markdown)
        assert "not a heading" not in result

    def test_backtick_run_does_not_close_tilde_fence(self) -> None:
        """Same-character close rule: a ``` run never closes a ~~~ fence."""
        markdown = "## A\n~~~\n# x\n```\nstill inside\n~~~\nbody"
        result = agents_validator_find_empty_sections(markdown)
        assert "x" not in result

    def test_unclosed_fence_runs_to_eof(self) -> None:
        """An unclosed fence consumes every remaining line, including any '#' lines."""
        markdown = "## A\n~~~\n# x\n"
        result = agents_validator_find_empty_sections(markdown)
        assert "x" not in result

    def test_four_space_indent_is_code_not_heading(self) -> None:
        """(5b) Four or more leading spaces is an indented code block, not a heading."""
        markdown = "## A\n    # indented\nbody"
        result = agents_validator_find_empty_sections(markdown)
        assert "indented" not in result

    def test_three_space_indent_is_still_a_valid_heading(self) -> None:
        """(5b) Positive control: 0-3 leading spaces is still a valid ATX heading."""
        markdown = "   ### C\n\n## D\ntext"
        result = agents_validator_find_empty_sections(markdown)
        assert result == ["C"]

    def test_setext_heading_is_untracked(self) -> None:
        """(5c) Setext headings are deliberately out of scope; ATX only."""
        markdown = "## A\nSetext Title\n=====\nbody"
        result = agents_validator_find_empty_sections(markdown)
        assert "Setext Title" not in result
        assert "A" not in result

    def test_closing_hash_sequence_is_stripped(self) -> None:
        """(5e) A trailing '##' closing run is stripped from the heading text."""
        markdown = "## Code ##\n\n## Notes\n\ntext"
        result = agents_validator_find_empty_sections(markdown)
        assert result == ["Code"]
        assert "Code ##" not in result

    def test_hashtag_with_no_space_is_not_a_heading(self) -> None:
        """(5e) A hash run with no following whitespace is body text, not a heading."""
        markdown = "## A\n#hashtag\nbody"
        result = agents_validator_find_empty_sections(markdown)
        assert result == []


class TestAgentsUtilsFindEmptySectionsClosingHashPerformance:
    """Regression coverage for catastrophic-backtracking-shaped closing-hash input."""

    def test_adversarial_closing_hash_run_completes_within_bound(self) -> None:
        """A pathological trailing space-then-hash run must resolve in linear time.

        Reproduces the adversarial shape that previously drove catastrophic
        regex backtracking in the closing-hash-sequence stripper: a heading
        line followed by a long run of spaces immediately followed by a long
        run of hash characters and a non-matching terminator. The bound is
        set with generous headroom (well under the multi-second-to-minute
        blowup the vulnerable pattern exhibited) so the assertion stays
        robust on a loaded CI machine while still failing hard if the
        catastrophic-backtracking shape is ever reintroduced.
        """

        n = 64_000
        markdown = "## A" + " " * n + "#" * n + "X\nbody\n"

        start = time.monotonic()
        result = agents_validator_find_empty_sections(markdown)
        elapsed = time.monotonic() - start

        assert elapsed < 1.0
        assert result == []
