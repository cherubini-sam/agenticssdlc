#!/usr/bin/env python3
"""
Project classifier
Identifies project archetype and technology stack
"""

import json
from pathlib import Path
from typing import Dict, Optional


class ProjectClassifier:
    """Classify project type and technology stack"""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)

    def classify(self) -> Dict:
        """Perform full project classification"""
        return {
            "archetype": self._detect_archetype(),
            "language": self._detect_primary_language(),
            "framework": self._detect_framework(),
            "package_manager": self._detect_package_manager(),
            "build_tool": self._detect_build_tool(),
        }

    def _detect_archetype(self) -> str:
        """Detect project architecture pattern"""

        # Check for monorepo indicators
        if (
            (self.root_path / "lerna.json").exists()
            or (self.root_path / "pnpm-workspace.yaml").exists()
            or (self.root_path / "packages").is_dir()
        ):
            return "monorepo"

        # Check for microservices
        service_dirs = ["services", "apps", "microservices"]
        if any((self.root_path / d).is_dir() for d in service_dirs):
            return "microservices"

        # Check for library
        if (self.root_path / "lib").is_dir() and (self.root_path / "examples").is_dir():
            return "library"

        # Check for plugin architecture
        if (self.root_path / "plugins").is_dir() or (self.root_path / "extensions").is_dir():
            return "plugin_architecture"

        # Default to monolith
        return "monolith"

    def _detect_primary_language(self) -> str:
        """Detect primary programming language"""

        indicators = {
            "python": ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile"],
            "javascript": ["package.json", "yarn.lock"],
            "typescript": ["tsconfig.json"],
            "rust": ["Cargo.toml"],
            "go": ["go.mod"],
            "java": ["pom.xml", "build.gradle"],
            "ruby": ["Gemfile"],
            "php": ["composer.json"],
            "c#": ["*.csproj", "*.sln"],
        }

        for lang, files in indicators.items():
            if any((self.root_path / f).exists() for f in files):
                return lang

        return "unknown"

    def _detect_framework(self) -> Optional[str]:
        """Detect web framework or major library"""

        # Check package.json for JS frameworks
        package_json = self.root_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    deps = {
                        **data.get("dependencies", {}),
                        **data.get("devDependencies", {}),
                    }

                    if "next" in deps:
                        return "Next.js"
                    elif "react" in deps:
                        return "React"
                    elif "vue" in deps:
                        return "Vue"
                    elif "@angular/core" in deps:
                        return "Angular"
                    elif "express" in deps:
                        return "Express"
            except (json.JSONDecodeError, ValueError, KeyError):
                pass

        # Check Python frameworks
        requirements = self.root_path / "requirements.txt"
        if requirements.exists():
            content = requirements.read_text().lower()
            if "django" in content:
                return "Django"
            elif "flask" in content:
                return "Flask"
            elif "fastapi" in content:
                return "FastAPI"

        return None

    def _detect_package_manager(self) -> Optional[str]:
        """Detect package manager"""

        managers = {
            "npm": "package-lock.json",
            "yarn": "yarn.lock",
            "pnpm": "pnpm-lock.yaml",
            "pip": "requirements.txt",
            "poetry": "poetry.lock",
            "pipenv": "Pipfile.lock",
            "cargo": "Cargo.lock",
            "bundler": "Gemfile.lock",
        }

        for manager, lockfile in managers.items():
            if (self.root_path / lockfile).exists():
                return manager

        return None

    def _detect_build_tool(self) -> Optional[str]:
        """Detect build tool"""

        tools = {
            "webpack": "webpack.config.js",
            "vite": "vite.config.js",
            "rollup": "rollup.config.js",
            "parcel": ".parcelrc",
            "make": "Makefile",
            "cmake": "CMakeLists.txt",
            "gradle": "build.gradle",
            "maven": "pom.xml",
        }

        for tool, config in tools.items():
            if (self.root_path / config).exists():
                return tool

        return None


def main():
    import sys

    root_path = sys.argv[1] if len(sys.argv) > 1 else "."

    classifier = ProjectClassifier(root_path)
    result = classifier.classify()

    print("\n=== PROJECT CLASSIFICATION ===\n")
    print(f"Archetype: {result['archetype']}")
    print(f"Language: {result['language']}")
    print(f"Framework: {result['framework'] or 'None detected'}")
    print(f"Package Manager: {result['package_manager'] or 'None detected'}")
    print(f"Build Tool: {result['build_tool'] or 'None detected'}")


if __name__ == "__main__":
    main()
