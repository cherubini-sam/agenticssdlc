#!/usr/bin/env python3
"""
Stack trace analyzer
Highlights user code frames and filters library noise
"""

import re
import sys
from typing import Dict


def analyze_stack_trace(stack_trace: str) -> Dict:
    """Parse and analyze Python stack trace"""

    lines = stack_trace.strip().split("\n")

    # Common library paths to filter out
    LIBRARY_PATHS = [
        "site-packages",
        "lib/python",
        "dist-packages",
        "/usr/lib",
        "/usr/local/lib",
    ]

    frames = []
    file_pattern = r'File "(.+)", line (\d+), in (.+)'

    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.search(file_pattern, line)

        if match:
            file_path = match.group(1)
            line_num = int(match.group(2))
            function = match.group(3)

            # Get code snippet (next line)
            code_snippet = lines[i + 1].strip() if i + 1 < len(lines) else ""

            is_user_code = not any(lib in file_path for lib in LIBRARY_PATHS)

            frames.append(
                {
                    "file": file_path,
                    "line": line_num,
                    "function": function,
                    "code": code_snippet,
                    "is_user_code": is_user_code,
                }
            )

            i += 2  # Skip code line
        else:
            i += 1

    # Extract error message (last line)
    error_message = lines[-1] if lines else ""

    # Find first user code frame (most relevant)
    user_frames = [f for f in frames if f["is_user_code"]]
    primary_frame = user_frames[-1] if user_frames else None

    return {
        "error_message": error_message,
        "total_frames": len(frames),
        "user_frames": len(user_frames),
        "primary_frame": primary_frame,
        "all_frames": frames,
    }


def format_analysis(analysis: Dict) -> str:
    """Format analysis results for display"""
    output = []

    output.append("=" * 60)
    output.append("STACK TRACE ANALYSIS")
    output.append("=" * 60)
    output.append(f"\nError: {analysis['error_message']}\n")
    output.append(f"Total frames: {analysis['total_frames']}")
    output.append(f"User code frames: {analysis['user_frames']}\n")

    if analysis["primary_frame"]:
        frame = analysis["primary_frame"]
        output.append("PRIMARY FAILURE POINT (Your Code):")
        output.append(f"  File: {frame['file']}")
        output.append(f"  Line: {frame['line']}")
        output.append(f"  Function: {frame['function']}")
        output.append(f"  Code: {frame['code']}\n")

    output.append("USER CODE FRAMES:")
    for i, frame in enumerate([f for f in analysis["all_frames"] if f["is_user_code"]], 1):
        output.append(f"\n{i}. {frame['file']}:{frame['line']} in {frame['function']}")
        output.append(f"   {frame['code']}")

    return "\n".join(output)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Read from file
        with open(sys.argv[1], "r") as f:
            stack_trace = f.read()
    else:
        # Read from stdin
        stack_trace = sys.stdin.read()

    analysis = analyze_stack_trace(stack_trace)
    print(format_analysis(analysis))
