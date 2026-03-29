#!/usr/bin/env python3
"""
Prompt testing framework
Automated testing and evaluation of LLM prompts
"""

import json
import time
from dataclasses import asdict, dataclass
from typing import Callable, Dict, List


@dataclass
class TestCase:
    """Single test case for prompt evaluation"""

    input: str
    expected_output: str = ""
    expected_format: str = ""
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class EvaluationResult:
    """Results from evaluating a prompt"""

    accuracy: float
    relevance: float
    format_compliance: float
    avg_tokens: int
    avg_latency: float
    total_tests: int
    passed_tests: int

    def to_dict(self) -> Dict:
        return asdict(self)


class PromptTester:
    """Test and evaluate LLM prompts"""

    def __init__(self, llm_function: Callable[[str], str]):
        """
        Initialize tester with LLM function

        Args:
            llm_function: Function that takes prompt string and returns response
        """
        self.llm_function = llm_function
        self.test_cases: List[TestCase] = []

    def add_test_case(self, test_case: TestCase):
        """Add a test case to the suite"""
        self.test_cases.append(test_case)

    def load_test_cases(self, filepath: str):
        """Load test cases from JSON file"""
        with open(filepath, "r") as f:
            data = json.load(f)
            for case in data["test_cases"]:
                self.test_cases.append(TestCase(**case))

    def evaluate_prompt(self, prompt_template: str) -> EvaluationResult:
        """
        Evaluate a prompt against all test cases

        Args:
            prompt_template: Prompt template with {input} placeholder

        Returns:
            EvaluationResult with metrics
        """
        total_accuracy = 0
        total_relevance = 0
        total_format_compliance = 0
        total_tokens = 0
        total_latency = 0
        passed = 0

        for test_case in self.test_cases:
            # Format prompt with test input
            full_prompt = prompt_template.format(input=test_case.input)

            # Measure latency
            start_time = time.time()
            response = self.llm_function(full_prompt)
            latency = time.time() - start_time

            # Calculate metrics
            accuracy = self._calculate_accuracy(response, test_case.expected_output)
            relevance = self._calculate_relevance(response, test_case.input)
            format_compliance = self._check_format(response, test_case.expected_format)
            tokens = self._estimate_tokens(response)

            total_accuracy += accuracy
            total_relevance += relevance
            total_format_compliance += format_compliance
            total_tokens += tokens
            total_latency += latency

            if accuracy > 0.7:  # 70% threshold for passing
                passed += 1

        n = len(self.test_cases)

        return EvaluationResult(
            accuracy=total_accuracy / n if n > 0 else 0,
            relevance=total_relevance / n if n > 0 else 0,
            format_compliance=total_format_compliance / n if n > 0 else 0,
            avg_tokens=int(total_tokens / n) if n > 0 else 0,
            avg_latency=total_latency / n if n > 0 else 0,
            total_tests=n,
            passed_tests=passed,
        )

    def _calculate_accuracy(self, response: str, expected: str) -> float:
        """Calculate accuracy score (0-1)"""
        if not expected:
            return 1.0  # No expected output to compare

        # Simple word overlap metric
        response_words = set(response.lower().split())
        expected_words = set(expected.lower().split())

        if not expected_words:
            return 1.0

        overlap = len(response_words & expected_words)
        return overlap / len(expected_words)

    def _calculate_relevance(self, response: str, input_text: str) -> float:
        """Calculate relevance to input (0-1)"""
        # Check if response addresses the input
        input_keywords = set(input_text.lower().split())
        response_words = set(response.lower().split())

        if not input_keywords:
            return 1.0

        overlap = len(input_keywords & response_words)
        return min(1.0, overlap / len(input_keywords))

    def _check_format(self, response: str, expected_format: str) -> float:
        """Check format compliance (0-1)"""
        if not expected_format:
            return 1.0

        format_checks = {
            "json": lambda r: self._is_valid_json(r),
            "markdown": lambda r: any(marker in r for marker in ["#", "```", "-", "*"]),
            "code": lambda r: "```" in r or "def " in r or "function " in r,
            "list": lambda r: any(marker in r for marker in ["-", "*", "1.", "2."]),
        }

        check_func = format_checks.get(expected_format.lower())
        if check_func:
            return 1.0 if check_func(response) else 0.0

        return 1.0

    def _is_valid_json(self, text: str) -> bool:
        """Check if text is valid JSON"""
        try:
            json.loads(text)
            return True
        except (json.JSONDecodeError, ValueError):
            return False

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (words * 1.3)"""
        return int(len(text.split()) * 1.3)

    def compare_prompts(self, prompts: Dict[str, str]) -> Dict[str, EvaluationResult]:
        """
        Compare multiple prompt variants

        Args:
            prompts: Dict of {name: prompt_template}

        Returns:
            Dict of {name: EvaluationResult}
        """
        results = {}

        for name, prompt in prompts.items():
            print(f"Testing prompt: {name}...")
            results[name] = self.evaluate_prompt(prompt)

        return results

    def generate_report(self, results: Dict[str, EvaluationResult]) -> str:
        """Generate comparison report"""
        lines = ["=== PROMPT COMPARISON REPORT ===\n"]

        for name, result in results.items():
            lines.append(f"\n{name}:")
            lines.append(f"  Accuracy: {result.accuracy:.2%}")
            lines.append(f"  Relevance: {result.relevance:.2%}")
            lines.append(f"  Format Compliance: {result.format_compliance:.2%}")
            lines.append(f"  Avg Tokens: {result.avg_tokens}")
            lines.append(f"  Avg Latency: {result.avg_latency:.2f}s")
            lines.append(f"  Pass Rate: {result.passed_tests}/{result.total_tests}")

        # Find best prompt
        best_name = max(results.keys(), key=lambda k: results[k].accuracy)
        lines.append(f"\nBest Prompt: {best_name}")

        return "\n".join(lines)


def main():
    """Example usage"""

    # Mock LLM function for testing
    def mock_llm(prompt: str) -> str:
        return f"Response to: {prompt[:50]}..."

    tester = PromptTester(mock_llm)

    # Add test cases
    tester.add_test_case(
        TestCase(
            input="def add(a, b): return a+b",
            expected_output="def add(a: int, b: int) -> int: return a + b",
            expected_format="code",
        )
    )

    # Test prompts
    prompts = {
        "verbose": "Please add type hints to this code: {input}",
        "concise": "Add type hints: {input}",
    }

    results = tester.compare_prompts(prompts)
    print(tester.generate_report(results))


if __name__ == "__main__":
    main()
