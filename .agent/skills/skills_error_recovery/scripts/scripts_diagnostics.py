#!/usr/bin/env python3
"""
Error diagnostics automation script
Parses logs and stack traces to identify common error patterns
"""

import re
from pathlib import Path
from typing import Any, Dict, List


class ErrorDiagnostics:
    """Automated error pattern detection and analysis"""

    ERROR_PATTERNS = {
        "import_error": r'(ImportError|ModuleNotFoundError):\s*No module named [\'"](\w+)[\'"]',
        "type_error": r"TypeError:\s*(.+)",
        "key_error": r'KeyError:\s*[\'"](\w+)[\'"]',
        "attribute_error": (
            r'AttributeError:\s*[\'"]?(\w+)[\'"]?\s*object has no attribute [\'"](\w+)[\'"]'
        ),
        "connection_error": r"(ConnectionError|ConnectionRefusedError|TimeoutError):\s*(.+)",
        "file_not_found": (
            r'FileNotFoundError:\s*\[Errno 2\]\s*No such file or directory:\s*[\'"](.+)[\'"]'
        ),
        "index_error": r"IndexError:\s*(.+)",
        "value_error": r"ValueError:\s*(.+)",
    }

    def __init__(self, log_file: str = None):
        self.log_file = log_file
        self.errors_found = []

    def parse_log(self, content: str) -> List[Dict[str, Any]]:
        """Parse log content and extract error patterns"""
        errors = []

        for error_type, pattern in self.ERROR_PATTERNS.items():
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                errors.append(
                    {
                        "type": error_type,
                        "message": match.group(0),
                        "details": match.groups(),
                        "suggestion": self._get_suggestion(error_type, match.groups()),
                    }
                )

        return errors

    def _get_suggestion(self, error_type: str, details: tuple) -> str:
        """Generate fix suggestions based on error type"""
        suggestions = {
            "import_error": (
                f"Install missing module: pip install "
                f"{details[1] if len(details) > 1 else 'module'}"
            ),
            "type_error": "Check argument types and function signature",
            "key_error": (
                f"Use .get('{details[0]}', default) instead of direct access"
                if details
                else "Use .get() with default value"
            ),
            "attribute_error": (
                f"Check if object is of expected type before accessing .{details[1]}"
                if len(details) > 1
                else "Verify object type"
            ),
            "connection_error": "Check network connectivity and retry with exponential backoff",
            "file_not_found": (
                f"Verify path exists: {details[0]}"
                if details
                else "Check file path and permissions"
            ),
            "index_error": "Check list/array bounds before accessing",
            "value_error": "Validate input format and type before processing",
        }
        return suggestions.get(error_type, "Review error message for details")

    def analyze_stack_trace(self, stack_trace: str) -> Dict[str, Any]:
        """Parse stack trace and identify key information"""
        lines = stack_trace.split("\n")

        # Find the actual error line (usually last non-empty line)
        error_line = next((line for line in reversed(lines) if line.strip()), None)

        # Extract file paths and line numbers
        file_pattern = r'File "(.+)", line (\d+)'
        frames = []

        for line in lines:
            match = re.search(file_pattern, line)
            if match:
                frames.append(
                    {
                        "file": match.group(1),
                        "line": int(match.group(2)),
                        "is_user_code": not any(
                            lib in match.group(1) for lib in ["site-packages", "lib/python"]
                        ),
                    }
                )

        # Find first user code frame (bottom-up)
        user_frame = next((f for f in reversed(frames) if f["is_user_code"]), None)

        return {
            "error_message": error_line,
            "total_frames": len(frames),
            "user_code_frame": user_frame,
            "all_frames": frames,
        }

    def generate_debug_commands(self, error_info: Dict[str, Any]) -> List[str]:
        """Generate debugging commands based on error analysis"""
        commands = []

        if error_info.get("user_code_frame"):
            frame = error_info["user_code_frame"]
            commands.append("# Inspect the failing line:")
            commands.append(
                f"view_file {frame['file']} --lines {max(1, frame['line'] - 5)}-{frame['line'] + 5}"
            )

        error_msg = error_info.get("error_message", "")

        if "ImportError" in error_msg or "ModuleNotFoundError" in error_msg:
            commands.append("# Check installed packages:")
            commands.append("pip list | grep <module_name>")

        if "ConnectionError" in error_msg:
            commands.append("# Test connectivity:")
            commands.append("curl -I <endpoint_url>")

        return commands


def main():
    """CLI interface for error diagnostics"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python scripts_diagnostics.py <log_file>")
        sys.exit(1)

    log_file = sys.argv[1]

    if not Path(log_file).exists():
        print(f"Error: File {log_file} not found")
        sys.exit(1)

    with open(log_file, "r") as f:
        content = f.read()

    diagnostics = ErrorDiagnostics(log_file)
    errors = diagnostics.parse_log(content)

    print("\n=== Error Diagnostics Report ===\n")
    print(f"Found {len(errors)} error(s)\n")

    for i, error in enumerate(errors, 1):
        print(f"{i}. {error['type'].upper()}")
        print(f"   Message: {error['message']}")
        print(f"   Suggestion: {error['suggestion']}\n")


if __name__ == "__main__":
    main()
