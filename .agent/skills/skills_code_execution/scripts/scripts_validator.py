import re

FORBIDDEN_PATTERNS = [
    r"import\s+os",
    r"import\s+subprocess",
    r"import\s+requests",
    r'open\s*\([^)]*,\s*["\']w',  # write mode
    r"exec\s*\(",
    r"eval\s*\(",
    r"__import__",
]


def contains_forbidden_pattern(code: str) -> bool:
    """Check if the code contains any forbidden patterns."""
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, code):
            return True
    return False


def get_detected_patterns(code: str) -> list:
    """Return a list of detected forbidden patterns in the code."""
    detected = []
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, code):
            detected.append(pattern)
    return detected
