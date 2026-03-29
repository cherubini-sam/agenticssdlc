#!/usr/bin/env python3
"""
Project structure mapper
Generates visual directory tree with smart filtering
"""

import os
from pathlib import Path
from typing import List


class ProjectMapper:
    """Generate project structure visualization"""

    # Directories to ignore
    IGNORE_DIRS = {
        "node_modules",
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "dist",
        "build",
        ".next",
        ".cache",
        "coverage",
        ".pytest_cache",
        ".mypy_cache",
        "target",
        "vendor",
    }

    # Files to ignore
    IGNORE_FILES = {
        ".DS_Store",
        "Thumbs.db",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".gitignore",
        ".env",
        "*.log",
    }

    def __init__(self, root_path: str, max_depth: int = 3):
        self.root_path = Path(root_path)
        self.max_depth = max_depth

    def generate_tree(self) -> str:
        """Generate directory tree structure"""
        lines = [f"{self.root_path.name}/"]
        self._walk_directory(self.root_path, "", 0, lines)
        return "\n".join(lines)

    def _walk_directory(self, path: Path, prefix: str, depth: int, lines: List[str]):
        """Recursively walk directory and build tree"""
        if depth >= self.max_depth:
            return

        try:
            entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except PermissionError:
            return

        # Filter out ignored items
        entries = [
            e for e in entries if e.name not in self.IGNORE_DIRS and e.name not in self.IGNORE_FILES
        ]

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            current_prefix = "└── " if is_last else "├── "
            next_prefix = "    " if is_last else "│   "

            if entry.is_dir():
                lines.append(f"{prefix}{current_prefix}{entry.name}/")
                self._walk_directory(entry, prefix + next_prefix, depth + 1, lines)
            else:
                lines.append(f"{prefix}{current_prefix}{entry.name}")

    def get_statistics(self) -> dict:
        """Get project statistics"""
        stats = {
            "total_files": 0,
            "total_dirs": 0,
            "files_by_type": {},
            "largest_files": [],
        }

        for root, dirs, files in os.walk(self.root_path):
            # Filter ignored directories
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]

            stats["total_dirs"] += len(dirs)

            for file in files:
                if file in self.IGNORE_FILES:
                    continue

                stats["total_files"] += 1

                # Count by extension
                ext = Path(file).suffix or "no_extension"
                stats["files_by_type"][ext] = stats["files_by_type"].get(ext, 0) + 1

                # Track file size
                file_path = Path(root) / file
                try:
                    size = file_path.stat().st_size
                    stats["largest_files"].append((str(file_path), size))
                except OSError:
                    pass

        # Sort and limit largest files
        stats["largest_files"].sort(key=lambda x: x[1], reverse=True)
        stats["largest_files"] = stats["largest_files"][:10]

        return stats


def main():
    import sys

    root_path = sys.argv[1] if len(sys.argv) > 1 else "."
    max_depth = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    mapper = ProjectMapper(root_path, max_depth)

    print("\n=== PROJECT STRUCTURE ===\n")
    print(mapper.generate_tree())

    print("\n\n=== STATISTICS ===\n")
    stats = mapper.get_statistics()
    print(f"Total Files: {stats['total_files']}")
    print(f"Total Directories: {stats['total_dirs']}")

    print("\nFiles by Type:")
    for ext, count in sorted(stats["files_by_type"].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {ext}: {count}")

    print("\nLargest Files:")
    for path, size in stats["largest_files"][:5]:
        size_kb = size / 1024
        print(f"  {size_kb:.1f} KB - {path}")


if __name__ == "__main__":
    main()
